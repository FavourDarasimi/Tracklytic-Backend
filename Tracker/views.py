from datetime import date
from tkinter import N
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render
from rest_framework.views import APIView, csrf_exempt
from rest_framework.generics import ListAPIView
from unicodedata import category
from Tracker.ai_client import generate_spending_advice
from Tracker.models import Category, GeneralSpendingLimit, CategorySpendingLimit, RecurringTransaction, Transaction, SavingPlan
from Tracker.serializers import RecurringTransactionSerializer, TransactionSerializer, CategorySerializer, \
    GeneralSpendingLimitSerializer, CategorySpendingLimitSerializer, SavingPlanSerializer,ListTransactionSerializer
from .utils import create_success_response, create_error_response, create_transaction_response,  extract_transaction_data, validate_category_exists
from .services import TransactionService, SavingPlanService, BudgetService, SavingsService
import tempfile, os


class AddCategory(APIView):
    def post(self, request:Request):
        data = request.data
        serializer = CategorySerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            serializer.validated_data['tag'] = serializer.validated_data['name'].lower()
            serializer.save()
            return create_success_response('Category Added', serializer.data, status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetUserCategories(APIView):
    def get(self, request:Request):
        categories = Category.objects.filter(user=request.user)
        serializer = CategorySerializer(categories,many=True)
        if len(categories) > 0:
            return create_success_response('Categories retrieved successfully', serializer.data)
        else:
            return create_success_response('No categories found for this user')



class AddTransacion(APIView):
    def post(self, request: Request, *args, **kwargs):

        # --- Parse receipt if uploaded, merge into data ---
        data, parse_error = TransactionService.parse_receipt_if_uploaded(request)
        if parse_error:
            return create_error_response(parse_error)

        serializer = TransactionSerializer(data=data)
        if serializer.is_valid():
            processed_data, error = TransactionService.process_transaction_data(data, request.user)
            if error:
                return create_error_response(error)

            serializer.validated_data['user'] = request.user

            if processed_data['saving'] is not None:
                serializer.validated_data['category'] = processed_data['category']
                serializer.validated_data['savings'] = processed_data['saving']

                savings_percentage = serializer.validated_data['savings_percentage']
                transaction_type = serializer.validated_data['type']
                add_savings = serializer.validated_data['add_savings']

                savings_note = TransactionService.determine_savings_note(
                    processed_data['saving'],
                    savings_percentage,
                    transaction_type,
                    add_savings
                )
                serializer.validated_data['savings_note'] = savings_note

            transaction_instance = serializer.save()

            recurring = transaction_instance.recurring
            category = processed_data['category']
            amount = transaction_instance.amount
            recurring_message = None
            if recurring:
                recurring_message = TransactionService.create_recurring_transaction(
                    data, request.user, category, amount, transaction_instance
                )

            savings_message = SavingsService.process_savings_from_income(transaction_instance)
            limit_message = BudgetService.get_general_limit_status(request.user)

            return create_transaction_response(
                serializer.data, limit_message, savings_message, recurring_message
            )

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListTransactionsView(ListAPIView):
    serializer_class = ListTransactionSerializer

    def get_queryset(self):
        transaction = Transaction.object.filter(user=self.request.user,is_deleted=False)
        return transaction             


class AddRecurringTransaction(APIView):
    def post(self, request:Request):
        data = request.data
        serializer = RecurringTransactionSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user

class AddGeneralSpendingLimit(APIView):
    def post(self, request:Request):
        data = request.data
        budget_exists, error_message = BudgetService.check_general_budget_exists(request.user)
        if budget_exists:
            return create_error_response(error_message)
        
        serializer = GeneralSpendingLimitSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            serializer.save()
            return create_success_response('Budget Added', serializer.data, status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditGeneralSpendingLimit(APIView):
    def put(self, request:Request,pk):
        data = request.data
        try:
            general_budget = GeneralSpendingLimit.objects.get(id=pk,user=request.user)
            serializer = GeneralSpendingLimitSerializer(instance=general_budget, data=data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return create_success_response('General Budget Updated', serializer.data)
        except GeneralSpendingLimit.DoesNotExist:
            return create_error_response('General Budget does not exist')
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddCategorySpendingLimit(APIView):
    def post(self, request:Request):
        data = request.data
        category_id = data.get('category')
        serializer = CategorySpendingLimitSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            
            # Validate category exists
            category, category_error = validate_category_exists(category_id, request.user)
            if category_error:
                return create_error_response(category_error)
            
            # Check if category already has budget
            budget_exists, error_message = BudgetService.check_category_budget_exists(category_id, request.user)
            if budget_exists:
                return create_error_response(error_message)
            
            serializer.validated_data["category"] = category
            serializer.save()
            return create_success_response(f'Budget Added for {category.name}', serializer.data, status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCategorySpendingLimit(APIView):
    def put(self, request:Request,pk):
        data = request.data
        try:
            category_budget = CategorySpendingLimit.objects.get(id=pk,user=request.user)
            serializer = CategorySpendingLimitSerializer(instance=category_budget, data=data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return create_success_response(f'{category_budget.category.name} Budget Updated', serializer.data)
        except CategorySpendingLimit.DoesNotExist:
            return create_error_response('Budget for this Category does not exist')
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#day2
class AddSavingPlan(APIView):
    def post(self,request:Request):
        data = request.data
        serializer = SavingPlanSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            serializer.validated_data["status"] = "Active"
            serializer.save()
            return create_success_response('Saving Plan Added', serializer.data, status.HTTP_201_CREATED)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RenewSavingGoal(APIView):
    def put(self,request:Request,pk):
        data = request.data
        try:
            saving_plan = SavingPlan.objects.get(id=pk,user=request.user)
            serializer = SavingPlanSerializer(instance=saving_plan, data=data,partial=True)
            if serializer.is_valid():
                new_saving_plan_amount = serializer.validated_data['savings_amount']
                
                # Use service to renew saving plan
                success, message = SavingPlanService.renew_saving_plan(saving_plan, new_saving_plan_amount)
                if not success:
                    return create_error_response(message)
                
                return create_success_response(message, serializer.data)
        except SavingPlan.DoesNotExist:
            return create_error_response('Saving Plan does not exist')
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckStatusOfUserSavingPlans(APIView):
    def get(self,request:Request):
        try:
            saving_plans = SavingPlan.objects.filter(user=request.user)
            for plan in saving_plans:
                # Use service to update saving plan status
                SavingPlanService.update_saving_plan_status(plan)
            return create_success_response('Status Checked Successfully')
        except SavingPlan.DoesNotExist:
            return create_error_response('Saving Plan does not exist')


class UserSavingPlan(APIView):
    def get(self,request:Request):
        saving_plan = SavingPlan.objects.filter(user=request.user)
        serializer = SavingPlanSerializer(saving_plan,many=True)
        return create_success_response('Saving plans retrieved successfully', serializer.data)



class ParseReceiptView(APIView):
    """
    Receives a receipt file, runs Gemini extraction,
    returns extracted fields as JSON — does NOT save anything.
    """

    def post(self, request, *args, **kwargs):
        receipt = request.FILES.get("receipt")

        if not receipt:
            return create_error_response('No file uploaded', status.HTTP_400_BAD_REQUEST)

        # Save to temp file
        suffix = os.path.splitext(receipt.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in receipt.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            extracted = extract_transaction_data(tmp_path)

        except Exception as e:
            return create_error_response('Receipt parsing temporarily unavailable', status.HTTP_503_SERVICE_UNAVAILABLE)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        return create_success_response('Receipt data Extracted Successfully', extracted)


    

class AiClient(APIView):
    def get(self, request:Request):
        user = request.user

    # Fetch recent data
        transactions = Transaction.objects.filter(user=user).order_by("-transaction_date")[:20]  # last 20 transactions
        general_limit = GeneralSpendingLimit.objects.filter(user=user).first()
        category_limits = CategorySpendingLimit.objects.filter(user=user)
        saving_plans = SavingPlan.objects.filter(user=user)

        limits = {
            "general": general_limit,
            "categories": category_limits
        }

        advice = generate_spending_advice(user, transactions, limits, saving_plans)
        return create_success_response('Ai Insights', advice)
    


# Create your views here.
