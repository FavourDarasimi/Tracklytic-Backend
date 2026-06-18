from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from Account.models import CURRENCIES

user = get_user_model()

Type = (
    ("Expense", "Expense"),
    ("Income", "Income"),
)

Plan = (
    ("Daily", "Daily"),
    ("Weekly", "Weekly"),
    ("Monthly", "Monthly"),
    ("Yearly", "Yearly"),
)

Category_Type = (
    ("Income", "Income"),
    ("Expense", "Expense"),
)
Saving_Plan_Status = (
    ("Active", "Active"),
    ("Past Deadline", "Past Deadline"),
    ("Completed", "Completed"),
)
Priority = (
    ("Low", "Low"),
    ("Medium", "Medium"),
    ("High", "High"),
)


class Category(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=Category_Type)
    tag = models.CharField(max_length=100, null=True, blank=True)
    is_system = models.BooleanField(default=False)
    icon = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [models.Index(fields=["user", "type"])]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_user_category_name"
            )
        ]


class GeneralBudget(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(choices=Plan, max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [models.Index(fields=["user", "period"])]


class CategoryBudget(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    period = models.CharField(choices=Plan, max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.category}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "category"]),
            models.Index(fields=["user", "period"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "period"],
                name="unique_user_category_budget",
            )
        ]


class SavingPlan(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    savings_amount = models.DecimalField(max_digits=12, decimal_places=2)
    savings_reached_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    savings_reached = models.BooleanField(default=False)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        choices=Saving_Plan_Status, max_length=100, null=True, blank=True
    )
    priority = models.CharField(
        choices=Priority, max_length=10, default="Medium"
    )

    def __str__(self):
        return f"{self.user.username} {self.name} savings"

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["deadline"]),
        ]


class Transaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=200, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    type = models.CharField(choices=Type, max_length=50, null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    notes = models.TextField(max_length=500, blank=True, null=True)
    receipt = models.FileField(upload_to="receipts/", blank=True, null=True)
    transaction_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    add_savings = models.BooleanField(default=False)
    savings_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    savings = models.ForeignKey(
        SavingPlan, on_delete=models.CASCADE, null=True, blank=True
    )
    savings_note = models.TextField(max_length=500, blank=True, null=True)
    recurring = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="NGN")

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.party_name}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "transaction_date"]),
            models.Index(fields=["user", "category"]),
            models.Index(fields=["is_deleted"]),
        ]


class RecurringTransaction(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ("Daily", "Daily"),
            ("Weekly", "Weekly"),
            ("Monthly", "Monthly"),
            ("Yearly", "Yearly"),
        ],
    )
    next_due_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "active"]),
            models.Index(fields=["next_due_date"]),
        ]


class CurrencyExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3, choices=CURRENCIES)
    target_currency = models.CharField(max_length=3, choices=CURRENCIES)
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["base_currency", "target_currency"]

    def __str__(self):
        return f"{self.base_currency} → {self.target_currency}: {self.rate}"
