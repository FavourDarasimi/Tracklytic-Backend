import os
from google import genai
import json
import base64
import re
from pathlib import Path
from rest_framework import status
from rest_framework.response import Response
import re

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


def create_error_response(message, status_code=status.HTTP_400_BAD_REQUEST):
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




client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def extract_transaction_data(file_path):
    """
    Extract transaction data from receipt image/PDF using Gemini AI.
    Returns a dict matching the Transaction model fields.
    """
    file_path = Path(file_path)
    
    # --- Read file and encode ---
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    encoded = base64.b64encode(file_bytes).decode("utf-8")

    # Determine MIME type
    suffix = file_path.suffix.lower()
    mime_map = {
        ".pdf":  "application/pdf",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(suffix, "image/jpeg")

    # --- Build prompt ---
    prompt = """
    You are a financial receipt parser. Analyze this receipt/transaction document and extract the following fields.
    Respond ONLY with a valid JSON object — no markdown, no explanation.

    Fields to extract:
    {
        "party_name": "Name of the sender or recipient (other party in transaction). String or null.",
        "amount": "Transaction amount as a positive integer (no decimals, no currency symbols). Integer or null.",
        "type": "Transaction type. Must be exactly one of: 'Expense' or 'Income' (case-sensitive, capitalize first letter). String or null.",        
        "category": "Best-guess category for the transaction (e.g. Food, Transport, Salary, Utilities, Shopping, Healthcare, Entertainment, Transfer). String or null.",
        "notes": "Brief summary of the transaction or any extra details on the receipt. Max 500 chars. String or null.",
        "transaction_date": "Date/time of transaction in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) if found, else null."
    }

    Rules:
    - amount must be a plain integer (e.g. 5000, not "₦5,000" or 5000.00)
    - type must be capitalized exactly: 'Expense' or 'Income'    
    - If a field cannot be determined, use null
    - Do not invent data that is not present in the receipt
    """

    # --- Call Gemini ---
    from google.genai import types
    contents = [
        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
        prompt,
    ]
    
  

       # Try models in order, fall back if one is unavailable
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview","gemini-2.5-flash-lite","gemini-2.0-flash-lite"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )

            raw = response.text.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}

            return {
                "party_name":       data.get("party_name"),
                "amount":           data.get("amount"),
                "type":             data.get("type"),
                "category":         data.get("category"),
                "notes":            data.get("notes"),
                "transaction_date": data.get("transaction_date"),
            }

        except Exception as e:
            last_error = str(e)
            print(f"[WARNING] {model_name} failed: {e}, trying next model...")
            continue

    # All models failed
    raise Exception(f"All Gemini models unavailable. Last error: {last_error}")
