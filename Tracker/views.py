import os
import tempfile
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from Tracker.ai_client import generate_spending_advice
from Tracker.models import (
    Category,
    CategorySpendingLimit,
    GeneralSpendingLimit,
    RecurringTransaction,
    SavingPlan,
    Transaction,
)
from Tracker.serializers import (
    CategorySerializer,
    CategorySpendingLimitSerializer,
    DashboardTransactionSerializer,
    GeneralSpendingLimitSerializer,
    ListTransactionSerializer,
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
    create_error_response,
    create_success_response,
    create_transaction_response,
    extract_transaction_data,
    validate_category_exists,
)

# ── ViewSets (Standard Resources) ──


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True, is_system=True)
        ).order_by("-is_system", "name")

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            is_system=False,
            tag=serializer.validated_data.get("name", "").lower(),
        )


class TransactionViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action == "list":
            return ListTransactionSerializer
        return TransactionSerializer

    def get_queryset(self):
        return (
            Transaction.objects.filter(user=self.request.user, is_deleted=False)
            .select_related("category")
            .order_by("-transaction_date")
        )

    def create(self, request, *args, **kwargs):
        data, parse_error = TransactionService.parse_receipt_if_uploaded(request)
        if parse_error:
            return create_error_response(parse_error)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)  # pyright: ignore[reportUnreachable, reportUnreachable]

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


class RecurringTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTransactionSerializer

    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GeneralBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = GeneralSpendingLimitSerializer

    def get_queryset(self):
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


class CategoryBudgetViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySpendingLimitSerializer

    def get_queryset(self):
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


class SavingPlanViewSet(viewsets.ModelViewSet):
    serializer_class = SavingPlanSerializer

    def get_queryset(self):
        return SavingPlan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="Active")


# ── APIViews (Action Endpoints) ──


class DashboardOverview(APIView):
    def get(self, request: Request):
        user = request.user
        now = datetime.now()
        today = now.date()
        week_ago = today - timedelta(days=7)

        transactions = Transaction.objects.filter(
            user=user,
            is_deleted=False,
            transaction_date__isnull=False,
        ).select_related("category")

        monthly_transactions = transactions.filter(
            transaction_date__year=now.year,
            transaction_date__month=now.month,
        )

        monthly_totals = monthly_transactions.values("type").annotate(
            total=Sum("amount")
        )
        monthly_income = next(
            (t["total"] for t in monthly_totals if t["type"] == "Income"), 0
        )
        monthly_expenses = next(
            (t["total"] for t in monthly_totals if t["type"] == "Expense"), 0
        )
        daily_average = round(monthly_expenses / max(1, today.day), 2)

        expense_qs = monthly_transactions.filter(type="Expense", category__isnull=False)
        category_totals = (
            expense_qs.values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        expense_distribution = [
            {"name": item["category__name"], "amount": item["total"]}
            for item in category_totals
        ]
        top_category = expense_distribution[0]["name"] if expense_distribution else None

        expense_by_day = (
            expense_qs.filter(transaction_date__date__gte=today - timedelta(days=6))
            .annotate(day=TruncDate("transaction_date"))
            .values("day")
            .annotate(total=Sum("amount"))
            .order_by("day")
        )
        day_totals = {item["day"]: item["total"] for item in expense_by_day}
        chart_labels = []
        chart_values = []
        for offset in range(6, -1, -1):
            label_date = today - timedelta(days=offset)
            chart_labels.append(label_date.strftime("%b %d"))
            chart_values.append(day_totals.get(label_date, 0))

        latest_transactions = transactions.order_by("-created_at")[:5]

        general_limit = GeneralSpendingLimit.objects.filter(user=user).first()
        budget_summary = None
        if general_limit is not None:
            budget_summary = {
                "plan": general_limit.budget_plan,
                "limit": general_limit.budget_amount,
                "spent": monthly_expenses,
                "remaining": max(general_limit.budget_amount - monthly_expenses, 0),
            }

        weekly_transactions = transactions.filter(
            transaction_date__date__gte=week_ago
        ).count()
        total_transactions = transactions.count()

        data = {
            "overview": {
                "monthly_income": monthly_income,
                "monthly_expenses": monthly_expenses,
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
        return create_success_response("Dashboard data retrieved successfully", data)


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


class AiClient(APIView):
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
    def get(self, request: Request):
        saving_plans = SavingPlan.objects.filter(user=request.user)
        for plan in saving_plans:
            SavingPlanService.update_saving_plan_status(plan)
        return create_success_response("Status Checked Successfully")


class RenewSavingGoal(APIView):
    def put(self, request: Request, pk):
        data = request.data
        try:
            saving_plan = SavingPlan.objects.get(id=pk, user=request.user)
            serializer = SavingPlanSerializer(
                instance=saving_plan, data=data, partial=True
            )
            if serializer.is_valid():
                new_saving_plan_amount = serializer.validated_data["savings_amount"]
                success, message = SavingPlanService.renew_saving_plan(
                    saving_plan, new_saving_plan_amount
                )
                if not success:
                    return create_error_response(message)
                return create_success_response(message, serializer.data)
        except SavingPlan.DoesNotExist:
            return create_error_response("Saving Plan does not exist")
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
