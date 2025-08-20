from rest_framework import status
from rest_framework.response import Response


def create_success_response(message, data=None, status_code=status.HTTP_200_OK):
    """
    Utility function to create standardized success responses
    """
    response = {
        'status': 'success',
        'message': message,
    }
    if data is not None:
        response['data'] = data
    return Response(data=response, status=status_code)


def create_error_response(message, status_code=status.HTTP_200_OK):
    """
    Utility function to create standardized error responses
    """
    response = {
        'status': 'error',
        'message': message,
    }
    return Response(data=response, status=status_code)


def create_transaction_response(serializer_data, limit_message, savings_message,recurring_message):
    """
    Utility function to create standardized transaction response
    """
    response = {
        'status': 'success',
        'message': 'Transaction was successfully added',
        'data': serializer_data,
        'limit': limit_message,
        'savings_message': savings_message,
        'recurring_message':recurring_message
    }
    return Response(data=response, status=status.HTTP_201_CREATED)


def validate_category_exists(category_id, user):
    """
    Utility function to validate if a category exists for a user
    """
    from Tracker.models import Category
    try:
        category = Category.objects.get(id=category_id, user=user)
        return category, None
    except Category.DoesNotExist:
        return None, 'Category does not exist'


def validate_saving_plan_exists(savings_id, user):
    """
    Utility function to validate if a saving plan exists for a user
    """
    from Tracker.models import SavingPlan
    try:
        saving = SavingPlan.objects.get(id=savings_id, user=user)
        return saving, None
    except SavingPlan.DoesNotExist:
        return None, 'Saving plan does not exist'
