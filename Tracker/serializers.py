from rest_framework import serializers

from Account.serializers import CustomUserSerializer
from .models import Category, Transaction,  GeneralSpendingLimit, CategorySpendingLimit, SavingPlan,RecurringTransaction


# class SubCategorySerializer(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField(read_only=True)
#     category = serializers.SerializerMethodField(read_only=True)

#     class Meta:
#         model = SubCategory
#         fields = ['id','user','category','name','tag']

#     def get_user(self,obj):
#         user = obj.user.username
#         return user

#     def get_category(self,obj):
#         category = obj.category.name
#         return category

class CategorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Category
        fields = ['id','user','name','tag']

    def get_user(self,obj):
        user = obj.user.username
        return user

   

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Transaction
        fields = ['id','user','party_name','amount','type','category','notes','receipt','transaction_date','created_at','add_savings','savings_percentage','savings','savings_note','recurring']

    def get_user(self,obj):
        user = obj.user.username
        return user

class GeneralSpendingLimitSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = GeneralSpendingLimit
        fields = ['id','user','budget_plan','budget_amount']

    def get_user(self,obj):
        user = obj.user.username
        return user

class CategorySpendingLimitSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CategorySpendingLimit
        fields = ['id', 'user','category','budget_plan', 'budget_amount']

    def get_user(self, obj):
        user = obj.user.username
        return user

    def get_category(self, obj):
        category = obj.category.name
        return category
#day2

class SavingPlanSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = SavingPlan
        fields = ['id','user','name','savings_amount','savings_reached_amount','savings_reached','deadline','status']

    def get_user(self, obj):
        user = obj.user.username
        return user
    

class RecurringTransactionSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = RecurringTransaction
        fields = ['id', 'user', 'category', 'amount', 'frequency', 'next_due_date', 'end_date', 'active']
