import csv
import os
import tempfile
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import StreamingHttpResponse
from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from Tracker.ai_client import generate_spending_advice
from Tracker.models import (
    Category,
    CategorySpendingLimit,
    CurrencyExchangeRate,
    GeneralSpendingLimit,
    RecurringTransaction,
    SavingPlan,
    Transaction,
    Type,
)
from Tracker.serializers import (
    BulkDeleteSerializer,
    CategorySerializer,
    CategorySpendingLimitSerializer,
    DashboardTransactionSerializer,
    GeneralSpendingLimitSerializer,
    ListTransactionSerializer,
    MakeRecurringSerializer,
    RecurringTransactionSerializer,
    SavingPlanSerializer,
    TransactionSerializer,
)

from .services import (
    BudgetService,
    SavingPlanService,
    SavingsService,
    TransactionService,
)
from .utils import (
    convert_currency,
    create_error_response,
    create_success_response,
    create_transaction_response,
    extract_transaction_data,
    validate_category_exists,
)

CACHE_TTL = 300
CACHE_PREFIX = "dashboard_"


def invalidate_dashboard_cache(user_id):
    cache.delete(f"{CACHE_PREFIX}{user_id}")


# ── ViewSets (Standard Resources) ──


@extend_schema(tags=["Categories"])
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        return Category.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True, is_system=True)
        ).order_by("-is_system", "name")

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            is_system=False,
            tag=serializer.validated_data.get("name", "").lower(),
        )


class TransactionFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    date_from = filters.DateTimeFilter(field_name="transaction_date", lookup_expr="gte")
    date_to = filters.DateTimeFilter(field_name="transaction_date", lookup_expr="lte")
    type = filters.ChoiceFilter(choices=Type)
    category = filters.NumberFilter(field_name="category__id")
    amount_min = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    deleted = filters.BooleanFilter(field_name="is_deleted")
    recurring = filters.BooleanFilter(field_name="recurring")

    class Meta:
        model = Transaction
        fields = [
            "type",
            "category",
            "date_from",
            "date_to",
            "amount_min",
            "amount_max",
            "deleted",
            "recurring",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(party_name__icontains=value) | Q(notes__icontains=value)
        )


@extend_schema(tags=["Transactions"])
class TransactionViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination
    page_size = 20
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_class = TransactionFilter
    ordering_fields = ["amount", "transaction_date", "created_at"]
    ordering = ["-transaction_date"]

    def get_serializer_class(self):
        if getattr(self, "swagger_fake_view", False):
            return TransactionSerializer
        if self.action == "list":
            return ListTransactionSerializer
        return TransactionSerializer

    def get_queryset(self):
        if (
            getattr(self, "swagger_fake_view", False)
            or not self.request.user.is_authenticated
        ):
            return Transaction.objects.none()
        qs = Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )
        deleted = self.request.query_params.get("deleted")
        if deleted == "true":
            return qs.filter(is_deleted=True)
        if deleted == "all":
            return qs
        return qs.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        invalidate_dashboard_cache(self.request.user.id)

    def perform_update(self, serializer):
        serializer.save()
        invalidate_dashboard_cache(self.request.user.id)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()
        invalidate_dashboard_cache(self.request.user.id)

    def create(self, request, *args, **kwargs):
        invalidate_dashboard_cache(request.user.id)
        data, parse_error = TransactionService.parse_receipt_if_uploaded(request)
        if parse_error:
            return create_error_response(parse_error)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        processed_data, error = TransactionService.process_transaction_data(
            data, request.user
        )
        if error:
            return create_error_response(error)

        with transaction.atomic():
            serializer.validated_data["user"] = request.user

            if processed_data["saving"] is not None:
                serializer.validated_data["category"] = processed_data["category"]
                serializer.validated_data["savings"] = processed_data["saving"]

                savings_percentage = serializer.validated_data.get("savings_percentage")
                transaction_type = serializer.validated_data.get("type")
                add_savings = serializer.validated_data.get("add_savings")

                serializer.validated_data["savings_note"] = (
                    TransactionService.determine_savings_note(
                        processed_data["saving"],
                        savings_percentage,
                        transaction_type,
                        add_savings,
                    )
                )

            transaction_instance = serializer.save()

            recurring = transaction_instance.recurring
            category = processed_data["category"]
            amount = transaction_instance.amount
            recurring_message = None
            if recurring:
                recurring_message = TransactionService.create_recurring_transaction(
                    data, request.user, category, amount, transaction_instance
                )

            savings_message = SavingsService.process_savings_from_income(
                transaction_instance
            )
            limit_message = BudgetService.get_general_limit_status(request.user)

        return create_transaction_response(
            serializer.data, limit_message, savings_message, recurring_message
        )

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        try:
            txn = Transaction.objects.get(id=pk, user=request.user, is_deleted=True)
            txn.is_deleted = False
            txn.save()
            invalidate_dashboard_cache(request.user.id)
            return create_success_response("Transaction restored successfully")
        except Transaction.DoesNotExist:
            return create_error_response(
                "Transaction not found or not deleted", status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        methods=["POST"],
        request=BulkDeleteSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "deleted_count": {"type": "integer"},
                },
            }
        },
    )
    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        deleted_count = Transaction.objects.filter(
            id__in=ids, user=request.user
        ).update(is_deleted=True)
        invalidate_dashboard_cache(request.user.id)
        return Response(
            {
                "status": "success",
                "message": f"{deleted_count} transaction(s) deleted",
                "deleted_count": deleted_count,
            }
        )

    @extend_schema(
        methods=["GET"],
        parameters=[
            OpenApiParameter(
                name="deleted",
                description="Filter by deleted status: true/false/all",
                required=False,
                type=str,
            ),
        ],
        responses={200: {"type": "string", "content": {"text/csv": {}}}},
    )
    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        user = request.user
        qs = self.filter_queryset(self.get_queryset()).select_related(
            "category", "savings"
        )

        def stream():
            writer = csv.writer(open(os.devnull, "w"))
            yield "id,date,type,party,amount,currency,category,notes,savings_plan,savings_status\n"
            for txn in qs.iterator():
                yield (
                    f"{txn.id},{txn.transaction_date},{txn.type},{txn.party_name},"
                    f"{txn.amount},{txn.currency},"
                    f"{txn.category.name if txn.category else ''},"
                    f"{txn.notes if txn.notes else ''},"
                    f"{txn.savings.name if txn.savings else ''},"
                    f"{txn.savings.status if txn.savings else ''}\n"
                )

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        return response

    @extend_schema(
        methods=["POST"],
        request=MakeRecurringSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                },
            }
        },
    )
    @action(detail=True, methods=["post"])
    def make_recurring(self, request, pk=None):
        try:
            txn = Transaction.objects.get(id=pk, user=request.user)
        except Transaction.DoesNotExist:
            return create_error_response(
                "Transaction not found", status.HTTP_404_NOT_FOUND
            )

        if RecurringTransaction.objects.filter(transaction=txn).exists():
            return create_error_response(
                "Transaction is already recurring"
            )

        serializer = MakeRecurringSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data.get("next_due_date"):
            delta = {
                "Daily": relativedelta(days=1),
                "Weekly": relativedelta(weeks=1),
                "Monthly": relativedelta(months=1),
                "Yearly": relativedelta(years=1),
            }.get(data["frequency"])
            data["next_due_date"] = datetime.now().date() + delta

        msg = TransactionService.create_recurring_transaction(
            data=data,
            user=request.user,
            category=txn.category,
            amount=txn.amount,
            transaction=txn,
        )

        txn.recurring = True
        txn.save(update_fields=["recurring"])
        invalidate_dashboard_cache(request.user.id)

        return create_success_response(msg)


@extend_schema(tags=["Recurring Transactions"])
class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTransactionSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RecurringTransaction.objects.none()
        return RecurringTransaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Budgets"])
class GeneralBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = GeneralSpendingLimitSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GeneralSpendingLimit.objects.none()
        return GeneralSpendingLimit.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        budget_exists, error_message = BudgetService.check_general_budget_exists(
            request.user
        )
        if budget_exists:
            return create_error_response(error_message)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Budgets"])
class CategoryBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySpendingLimitSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CategorySpendingLimit.objects.none()
        return CategorySpendingLimit.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data
        category_id = data.get("category")
        category, category_error = validate_category_exists(category_id, request.user)
        if category_error:
            return create_error_response(category_error)

        budget_exists, error_message = BudgetService.check_category_budget_exists(
            category_id, request.user
        )
        if budget_exists:
            return create_error_response(error_message)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, category=category)
        return create_success_response(
            f"Budget Added for {category.name}",
            serializer.data,
            status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Saving Plans"])
class SavingPlanViewSet(viewsets.ModelViewSet):
    serializer_class = SavingPlanSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SavingPlan.objects.none()
        return SavingPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="Active")


# ── APIViews (Action Endpoints) ──


class DashboardOverview(APIView):
    @extend_schema(
        tags=["Dashboard"],
        parameters=[
            OpenApiParameter(
                "period", str, required=False, description="1W, 1M, 3M, 1Y, all"
            )
        ],
        responses={200: {"type": "object"}},
        description="Get aggregated dashboard overview with currency conversion to user's base currency",
    )
    def get(self, request: Request):
        user = request.user
        now = datetime.now()
        today = now.date()

        try:
            base_currency = user.profile.base_currency
        except user._meta.model.profile.RelatedObjectDoesNotExist:
            base_currency = "NGN"

        period = request.query_params.get("period", "1M")
        start_date = {
            "1W": today - timedelta(days=7),
            "1M": today - relativedelta(months=1),
            "3M": today - relativedelta(months=3),
            "1Y": today - relativedelta(years=1),
            "all": None,
        }.get(period, today - relativedelta(months=1))

        cache_key = f"{CACHE_PREFIX}{user.id}_{period}"
        cached = cache.get(cache_key)
        if cached:
            return create_success_response(
                "Dashboard data retrieved successfully", cached
            )

        transactions = Transaction.objects.filter(
            user=user,
            is_deleted=False,
            transaction_date__isnull=False,
        ).select_related("category")

        period_qs = transactions
        if start_date:
            period_qs = transactions.filter(transaction_date__date__gte=start_date)

        totals = period_qs.values("type", "currency").annotate(total=Sum("amount"))
        monthly_income = 0
        monthly_expenses = 0
        for entry in totals:
            converted = convert_currency(
                entry["total"], entry["currency"], base_currency
            )
            if entry["type"] == "Income":
                monthly_income += converted
            else:
                monthly_expenses += converted

        days_in_period = (today - start_date).days if start_date else today.day
        daily_average = round(monthly_expenses / max(1, days_in_period), 2)

        expense_qs = period_qs.filter(type="Expense", category__isnull=False)
        category_totals_raw = (
            expense_qs.values("category__name", "currency")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        category_agg = {}
        for item in category_totals_raw:
            name = item["category__name"]
            converted = convert_currency(item["total"], item["currency"], base_currency)
            category_agg[name] = category_agg.get(name, 0) + converted

        expense_distribution = [
            {"name": name, "amount": round(amount, 2)}
            for name, amount in sorted(category_agg.items(), key=lambda x: -x[1])
        ]
        top_category = expense_distribution[0]["name"] if expense_distribution else None

        # Dynamic expense chart
        if period in ("1W", "1M"):
            trunc_fn = TruncDate("transaction_date")
            step = timedelta(days=1)
            label_fmt = "%b %d"
            cursor = start_date
        elif period == "3M":
            trunc_fn = TruncWeek("transaction_date")
            step = timedelta(weeks=1)
            label_fmt = "%b %d"
            cursor = start_date - timedelta(days=start_date.weekday())
        else:
            trunc_fn = TruncMonth("transaction_date")
            step = relativedelta(months=1)
            label_fmt = "%b %Y"
            earliest = transactions.earliest("transaction_date").transaction_date.date()
            base = start_date if start_date else earliest
            cursor = base.replace(day=1)

        chart_raw = (
            expense_qs.annotate(period_label=trunc_fn)
            .values("period_label", "currency")
            .annotate(total=Sum("amount"))
            .order_by("period_label")
        )
        period_totals = {}
        for item in chart_raw:
            key = item["period_label"]
            if key:
                if isinstance(key, datetime):
                    key = key.date()
                converted = convert_currency(
                    item["total"], item["currency"], base_currency
                )
                period_totals[key] = period_totals.get(key, 0) + converted

        chart_labels = []
        chart_values = []
        while cursor <= today:
            chart_labels.append(cursor.strftime(label_fmt))
            chart_values.append(round(period_totals.get(cursor, 0), 2))
            cursor += step

        MAX_BARS = 60
        if len(chart_labels) > MAX_BARS:
            step_size = len(chart_labels) // MAX_BARS
            chart_labels = chart_labels[::step_size][:MAX_BARS]
            chart_values = [
                sum(chart_values[i : i + step_size])
                for i in range(0, len(chart_values), step_size)
            ][:MAX_BARS]

        latest_transactions = transactions.select_related("savings").order_by(
            "-created_at"
        )[:5]

        general_limit = GeneralSpendingLimit.objects.filter(user=user).first()
        budget_summary = None
        if general_limit is not None:
            budget_limit_converted = convert_currency(
                float(general_limit.budget_amount), "NGN", base_currency
            )
            budget_summary = {
                "plan": general_limit.budget_plan,
                "limit": round(budget_limit_converted, 2),
                "spent": round(monthly_expenses, 2),
                "remaining": round(
                    max(budget_limit_converted - monthly_expenses, 0), 2
                ),
            }

        weekly_transactions = transactions.filter(
            transaction_date__date__gte=today - timedelta(days=7)
        ).count()
        total_transactions = transactions.count()

        data = {
            "base_currency": base_currency,
            "overview": {
                "monthly_income": round(monthly_income, 2),
                "monthly_expenses": round(monthly_expenses, 2),
                "daily_average": daily_average,
                "top_category": top_category,
                "total_transactions": total_transactions,
                "weekly_transactions": weekly_transactions,
                "budget": budget_summary,
                "expense_distribution": expense_distribution,
                "expense_chart": {
                    "labels": chart_labels,
                    "values": chart_values,
                },
            },
            "latest_transactions": DashboardTransactionSerializer(
                latest_transactions, many=True
            ).data,
        }
        cache.set(cache_key, data, CACHE_TTL)
        return create_success_response("Dashboard data retrieved successfully", data)


class AiClient(APIView):
    @extend_schema(tags=["AI Insights"], responses={200: {"type": "object"}})
    def get(self, request: Request):
        user = request.user
        transactions = Transaction.objects.filter(user=user).order_by(
            "-transaction_date"
        )[:20]
        general_limit = GeneralSpendingLimit.objects.filter(user=user).first()
        category_limits = CategorySpendingLimit.objects.filter(user=user)
        saving_plans = SavingPlan.objects.filter(user=user)
        limits = {"general": general_limit, "categories": category_limits}
        advice = generate_spending_advice(user, transactions, limits, saving_plans)
        return create_success_response("Ai Insights", advice)


class CheckStatusOfUserSavingPlans(APIView):
    @extend_schema(tags=["Saving Plans"], responses={200: {"type": "object"}})
    def get(self, request: Request):
        saving_plans = SavingPlan.objects.filter(user=request.user)
        for plan in saving_plans:
            SavingPlanService.update_saving_plan_status(plan)
        return create_success_response("Status Checked Successfully")


class RenewSavingGoal(APIView):
    serializer_class = SavingPlanSerializer

    @extend_schema(tags=["Saving Plans"], responses={200: {"type": "object"}})
    def put(self, request: Request, pk):
        data = request.data
        try:
            saving_plan = SavingPlan.objects.get(id=pk, user=request.user)
            serializer = SavingPlanSerializer(
                instance=saving_plan, data=data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            new_saving_plan_amount = serializer.validated_data["savings_amount"]
            success, message = SavingPlanService.renew_saving_plan(
                saving_plan, new_saving_plan_amount
            )
            if not success:
                return create_error_response(message)
            return create_success_response(message, serializer.data)
        except SavingPlan.DoesNotExist:
            return create_error_response("Saving Plan does not exist")


@extend_schema(tags=["Transactions"])
class ParseReceiptView(APIView):
    def post(self, request, *args, **kwargs):
        receipt = request.FILES.get("receipt")
        if not receipt:
            return create_error_response(
                "No file uploaded", status.HTTP_400_BAD_REQUEST
            )

        suffix = os.path.splitext(receipt.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in receipt.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            extracted = extract_transaction_data(tmp_path)
        except Exception:
            return create_error_response(
                "Receipt parsing temporarily unavailable",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return create_success_response("Receipt data Extracted Successfully", extracted)
