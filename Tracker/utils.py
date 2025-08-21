from rest_framework import status
from rest_framework.response import Response
import easyocr
from pdf2image import convert_from_path
import re
import numpy as np

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


# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])
def extract_transaction_data(file_path):
    text = ""

    # Handle PDFs
    if file_path.lower().endswith(".pdf"):
        try:
            images = convert_from_path(file_path)
            for img in images:
                img_np = np.array(img)  # ✅ convert PIL -> NumPy
                result = reader.readtext(img_np, detail=0)
                text += "\n".join(result) + "\n"
        except Exception as e:
            print(f"[WARNING] Could not process PDF: {e}")
            text = "PDF could not be processed"
    else:
        # Handle images
        result = reader.readtext(file_path, detail=0)
        text = "\n".join(result)

    # --- Extract Amount ---
    amount_match = re.search(r'(\₦|\$|NGN)?\s?(\d+[.,]?\d{0,2})', text)
    amount = None
    if amount_match:
        amount = amount_match.group(2).replace(",", "")
        amount = int(float(amount))

    # --- Extract Sender & Receiver ---
    sender = None
    receiver = None

    # Look for sender/receiver keywords in text
    sender_match = re.search(r'(Sender|From)[:\s]+([A-Za-z\s]+)', text, re.IGNORECASE)
    if sender_match:
        sender = sender_match.group(2).strip().split("\n")[0]

    receiver_match = re.search(r'(Recipient|Receiver|To)[:\s]+([A-Za-z\s]+)', text, re.IGNORECASE)
    if receiver_match:
        receiver = receiver_match.group(2).strip().split("\n")[0]

    return {
        "amount": amount,
        "sender": sender,
        "receiver": receiver,
        "notes": text
    }


def detect_transaction_type(text, user_name=None):
    text_lower = text.lower()

    expense_keywords = ["debit", "debited", "paid", "transfer out", "outward", "purchase", "pos"]
    income_keywords = ["credit", "credited", "deposit", "received", "incoming", "transfer in"]

    if any(word in text_lower for word in expense_keywords):
        return "Expense"
    elif any(word in text_lower for word in income_keywords):
        return "Income"

    # Fallback: check sender/receiver vs user
    if user_name:
        if f"sender {user_name.lower()}" in text_lower:
            return "Expense"
        if f"receiver {user_name.lower()}" in text_lower:
            return "Income"

    return ""  # Unable to determine type


def assign_party_name(transaction_type, sender, receiver):
    """Expense → Receiver, Income → Sender"""
    if transaction_type == "Expense":
        return receiver
    elif transaction_type == "Income":
        return sender
    return None
