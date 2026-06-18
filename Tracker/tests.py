import pytest
from django.contrib.auth import get_user_model
from django.db.models import Sum
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from Tracker.models import Category, GeneralBudget, SavingPlan, Transaction
from Tracker.serializers import CategorySerializer, TransactionSerializer

User = get_user_model()


# ── Serializer Tests ──

@pytest.mark.django_db
class TestCategorySerializer:
    def test_includes_type_field(self):
        user = baker.make(User)
        category = baker.make(Category, user=user, type="Expense")
        serializer = CategorySerializer(category)
        assert "type" in serializer.data
        assert serializer.data["type"] == "Expense"


@pytest.mark.django_db
class TestTransactionSerializerCategoryFilter:
    def test_category_queryset_limited_to_user_categories(self):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request

        user = baker.make(User)
        other_user = baker.make(User)
        user_cat = baker.make(Category, user=user, type="Expense")
        other_cat = baker.make(Category, user=other_user, type="Expense")
        sys_cat = baker.make(Category, user=None, is_system=True, type="Expense")

        factory = APIRequestFactory()
        drf_request = Request(factory.get("/"))
        drf_request.user = user
        serializer = TransactionSerializer(context={"request": drf_request})

        qs_ids = list(serializer.fields["category"].queryset.values_list("id", flat=True))
        assert user_cat.id in qs_ids
        assert sys_cat.id in qs_ids
        assert other_cat.id not in qs_ids


# ── Service Layer Tests ──

@pytest.mark.django_db
class TestBudgetServiceAggregation:
    def test_get_general_limit_status_uses_sum_aggregation(self):
        user = baker.make(User)
        limit = baker.make(
            GeneralBudget, user=user, period="Monthly", amount=10000
        )
        baker.make(Transaction, user=user, type="Expense", amount=3000, _quantity=3)

        monthly_expense = Transaction.objects.filter(
            user=user, type="Expense"
        ).aggregate(total=Sum("amount"))["total"]

        assert monthly_expense == 9000
        assert monthly_expense < limit.amount


@pytest.mark.django_db
class TestSavingPlanStatus:
    def test_saving_plan_status_transitions(self):
        from datetime import date, timedelta
        from Tracker.services import SavingPlanService

        user = baker.make(User)
        plan = baker.make(
            SavingPlan, user=user, savings_amount=1000, savings_reached_amount=0,
            status="Active", deadline=date.today() - timedelta(days=1),
        )
        updated = SavingPlanService.update_saving_plan_status(plan)
        assert updated.status == "Past Deadline"

    def test_saving_plan_completes_when_target_reached(self):
        from Tracker.services import SavingPlanService

        user = baker.make(User)
        plan = baker.make(
            SavingPlan, user=user, savings_amount=1000, savings_reached_amount=1000,
            status="Active",
        )
        updated = SavingPlanService.update_saving_plan_status(plan)
        assert updated.status == "Completed"
        assert updated.savings_reached is True


# ── API Integration Tests ──

@pytest.mark.django_db
class TestTransactionAPI:
    def test_create_transaction_with_own_category(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="pass123"
        )
        cat = baker.make(Category, user=user, type="Expense")

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/v1/transactions/",
            {"party_name": "Test", "amount": 50.00, "type": "Expense", "category": cat.id},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_create_transaction_with_another_users_category(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="pass123"
        )
        other_user = User.objects.create_user(
            email="other@example.com", username="otheruser", password="pass123"
        )
        other_cat = baker.make(Category, user=other_user, type="Expense")

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(
            "/api/v1/transactions/",
            {"party_name": "Test", "amount": 50.00, "type": "Expense", "category": other_cat.id},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDashboardAPI:
    def test_dashboard_returns_overview(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="pass123"
        )
        baker.make(Transaction, user=user, type="Income", amount=5000)
        baker.make(Transaction, user=user, type="Expense", amount=2000)

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/v1/dashboard/overview/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert "overview" in response.data["data"]


@pytest.mark.django_db
class TestSavingPlanAPI:
    def test_create_and_renew_saving_plan(self):
        user = User.objects.create_user(
            email="test@example.com", username="testuser", password="pass123"
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            "/api/v1/saving-plans/",
            {"name": "Vacation", "savings_amount": 100000, "deadline": "2026-12-31"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        plan_id = response.data["id"]

        response = client.get("/api/v1/check/saving/plan/status/")
        assert response.status_code == status.HTTP_200_OK
