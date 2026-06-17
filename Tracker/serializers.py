from django.db.models import Q

from rest_framework import serializers

from Account.serializers import CustomUserSerializer

from .models import (
    Category,
    CategorySpendingLimit,
    GeneralSpendingLimit,
    RecurringTransaction,
    SavingPlan,
    Transaction,
)

class CategorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "user", "name", "type", "tag", "is_system", "icon", "color"]

    def get_user(self, obj):
        return obj.user.username if obj.user else None


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "party_name",
            "amount",
            "type",
            "category",
            "notes",
            "receipt",
            "transaction_date",
            "created_at",
            "add_savings",
            "savings_percentage",
            "savings",
            "savings_note",
            "recurring",
            "currency",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['category'].queryset = Category.objects.filter(
                Q(user=request.user) | Q(user__isnull=True, is_system=True)
            )

    def get_user(self, obj):
        user = obj.user.username
        return user


class ListTransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "party_name",
            "amount",
            "type",
            "category",
            "notes",
            "receipt",
            "transaction_date",
            "created_at",
            "currency",
        ]

    def get_user(self, obj):
        return obj.user.username

    def get_category(self, obj):
        if obj.category is None:
            return None
        return {
            "id": obj.category.id,
            "name": obj.category.name,
            "type": obj.category.type,
            "is_system": obj.category.is_system,
            "icon": obj.category.icon,
            "color": obj.category.color,
        }


class DashboardTransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    savings = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "party_name",
            "amount",
            "type",
            "category",
            "notes",
            "receipt",
            "transaction_date",
            "created_at",
            "add_savings",
            "savings_percentage",
            "savings",
            "savings_note",
            "recurring",
            "currency",
        ]

    def get_user(self, obj):
        return obj.user.username

    def get_category(self, obj):
        if obj.category is None:
            return None
        return {
            "id": obj.category.id,
            "name": obj.category.name,
            "type": obj.category.type,
            "is_system": obj.category.is_system,
            "icon": obj.category.icon,
            "color": obj.category.color,
        }

    def get_savings(self, obj):
        if obj.savings is None:
            return None
        return {
            "id": obj.savings.id,
            "name": obj.savings.name,
            "status": obj.savings.status,
        }


class GeneralSpendingLimitSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GeneralSpendingLimit
        fields = ["id", "user", "budget_plan", "budget_amount"]

    def get_user(self, obj):
        user = obj.user.username
        return user


class CategorySpendingLimitSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CategorySpendingLimit
        fields = ["id", "user", "category", "budget_plan", "budget_amount"]

    def get_user(self, obj):
        user = obj.user.username
        return user

    def get_category(self, obj):
        category = obj.category.name
        return category


class SavingPlanSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SavingPlan
        fields = [
            "id",
            "user",
            "name",
            "savings_amount",
            "savings_reached_amount",
            "savings_reached",
            "deadline",
            "status",
        ]

    def get_user(self, obj):
        user = obj.user.username
        return user


class RecurringTransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    frequency = serializers.ChoiceField(choices=['Daily', 'Weekly', 'Monthly', 'Yearly'])

    class Meta:
        model = RecurringTransaction
        fields = [
            "id",
            "user",
            "category",
            "amount",
            "frequency",
            "next_due_date",
            "end_date",
            "active",
        ]

    def get_user(self, obj):
        return obj.user.username

    def get_category(self, obj):
        return obj.category.name if obj.category else None


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
