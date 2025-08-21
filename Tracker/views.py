from datetime import date
from tkinter import N
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render
from rest_framework.views import APIView
from unicodedata import category
from Tracker.models import Category, GeneralSpendingLimit, CategorySpendingLimit, RecurringTransaction, Transaction, SavingPlan
from Tracker.serializers import RecurringTransactionSerializer, TransactionSerializer, CategorySerializer, \
    GeneralSpendingLimitSerializer, CategorySpendingLimitSerializer, SavingPlanSerializer
from .utils import assign_party_name, create_success_response, create_error_response, create_transaction_response, detect_transaction_type, extract_transaction_data, validate_category_exists
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


# class AddSubCategory(APIView):
#     def post(self, request:Request):
#         data = request.data
#         category_id = data.get('category')
#         serializer = SubCategorySerializer(data=data)
#         if serializer.is_valid():
#             category, category_error = validate_category_exists(category_id, request.user)
#             if category_error:
#                 return create_error_response(category_error)
            
#             serializer.validated_data['user'] = request.user
#             serializer.validated_data['category'] = category
#             name = serializer.validated_data['name']
#             serializer.validated_data['tag'] = f'{category.tag}__{name.lower()}'
#             serializer.save()
#             return create_success_response('Sub Category Added', serializer.data, status.HTTP_201_CREATED)
#         return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddTransacion(APIView):
    def post(self, request:Request, *args, **kwargs):
        data = request.data
        serializer = TransactionSerializer(data=data)
        if serializer.is_valid():
            # Process transaction data using service
            processed_data, error = TransactionService.process_transaction_data(data, request.user)
            if error:
                return create_error_response(error)
            
            # Set validated data
            serializer.validated_data['user'] = request.user
            
            # Check if savings are applicable
            if processed_data['saving'] is not None:

                serializer.validated_data['category'] = processed_data['category']
                serializer.validated_data['savings'] = processed_data['saving']
                
                # Determine savings note using service
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

            
            
            # Save transaction
            transaction_instance = serializer.save()

    # Check if transaction is recurring   
            recurring = transaction_instance.recurring
            category = processed_data['category']
            amount = transaction_instance.amount
            recurring_message=None
            if recurring:
                # Create recurring transaction using service
                recurring_message=TransactionService.create_recurring_transaction(data, request.user,category, amount, transaction_instance)

            # Process savings and limits
            savings_message = SavingsService.process_savings_from_income(transaction_instance)
            limit_message = BudgetService.get_general_limit_status(request.user)
            
            return create_transaction_response(serializer.data, limit_message, savings_message,recurring_message)
            
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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



class UploadReceipt(APIView):
    def post(self, request):
        receipt = request.FILES.get("receipt")

        if not receipt:
            return Response({"error": "No receipt uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Save to a temp file for OCR
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(receipt.name)[-1])
        for chunk in receipt.chunks():
            temp_file.write(chunk)
        temp_file.close()

        # Run OCR on the temp file
        extracted_data = extract_transaction_data(temp_file.name)

        # Detect type and assign party name
        transaction_type = detect_transaction_type(
            extracted_data.get("notes"), 
            user_name=request.user.username
        )

        party_name = assign_party_name(
            transaction_type,
            sender=extracted_data.get("sender"),
            receiver=extracted_data.get("receiver")
        )

        # Clean up temp file
        os.remove(temp_file.name)

        if not extracted_data:
            return Response({"error": "No transaction data found in receipt"}, status=status.HTTP_400_BAD_REQUEST)

        # Build transaction data (including user + file)
        data = {
            "user": request.user.id,
            "party_name": party_name,
            "amount": extracted_data.get("amount"),
            "type": transaction_type,
            "date": extracted_data.get("date"),
            "receipt": receipt
        }

        # Use serializer to validate & save
        serializer = TransactionSerializer(data=data)
        if serializer.is_valid():
            serializer.validated_data['user'] = request.user
            transaction = serializer.save()
            return Response({
                "status": "success",
                "message": "Transaction data extracted successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
