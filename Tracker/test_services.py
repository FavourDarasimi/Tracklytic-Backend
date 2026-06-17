import pytest
from datetime import date, timedelta
from decimal import Decimal
from model_bakery import baker

from django.contrib.auth import get_user_model
from Tracker.models import SavingPlan, Transaction, GeneralSpendingLimit
from Tracker.services import SavingPlanService, BudgetService

User = get_user_model()


@pytest.mark.django_db
class TestSavingPlanService:
    def test_update_status_to_past_deadline(self):
        user = baker.make(User)
        plan = baker.make(
            SavingPlan,
            user=user,
            savings_amount=Decimal("1000"),
            savings_reached_amount=Decimal("0"),
            status="Active",
            deadline=date.today() - timedelta(days=1),
        )
        updated = SavingPlanService.update_saving_plan_status(plan)
        assert updated.status == "Past Deadline"
        assert updated.savings_reached is False

    def test_update_status_to_completed(self):
        user = baker.make(User)
        plan = baker.make(
            SavingPlan,
            user=user,
            savings_amount=Decimal("1000"),
            savings_reached_amount=Decimal("1000"),
            status="Active",
        )
        updated = SavingPlanService.update_saving_plan_status(plan)
        assert updated.status == "Completed"
        assert updated.savings_reached is True

    def test_renew_saving_plan_rejects_lower_amount(self):
        user = baker.make(User)
        plan = baker.make(
            SavingPlan,
            user=user,
            savings_amount=Decimal("1000"),
            savings_reached_amount=Decimal("500"),
        )
        success, message = SavingPlanService.renew_saving_plan(plan, Decimal("200"))
        assert success is False
        assert "Cannot be lower" in message


@pytest.mark.django_db
class TestBudgetService:
    def test_general_limit_monthly_not_reached(self):
        user = baker.make(User)
        baker.make(
            GeneralSpendingLimit,
            user=user,
            budget_plan="Monthly",
            budget_amount=Decimal("10000"),
        )
        baker.make(
            Transaction, user=user, type="Expense", amount=Decimal("3000")
        )

        result = BudgetService.get_general_limit_status(user)
        assert "remaining" in result
        assert "Monthly" in result

    def test_general_limit_monthly_reached(self):
        user = baker.make(User)
        baker.make(
            GeneralSpendingLimit,
            user=user,
            budget_plan="Monthly",
            budget_amount=Decimal("5000"),
        )
        baker.make(
            Transaction, user=user, type="Expense", amount=Decimal("6000")
        )

        result = BudgetService.get_general_limit_status(user)
        assert "Limit has been Reached" in result

    def test_no_limit_returns_message(self):
        user = baker.make(User)
        result = BudgetService.get_general_limit_status(user)
        assert "does not have a general spending limit" in result
