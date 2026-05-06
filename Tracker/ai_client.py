from google import genai
from dotenv import load_dotenv
import os
import time
import json

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def extract_json_array(response):
    try:
        parts = response.candidates[0].content.parts
        text = " ".join([p.text for p in parts if hasattr(p, "text")]).strip()

        # محاولة تحويل إلى JSON
        data = json.loads(text)

        if isinstance(data, list):
            return data

        return None

    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return None

def generate_fallback_insights(transactions, limits, saving_plans):
    insights = []

    if not transactions:
        return [{
            "type": "info",
            "title": "No Data",
            "message": "No transactions yet. Start tracking to get insights."
        }]

    total_expense = sum(t.amount for t in transactions if t.type == "Expense")
    total_income = sum(t.amount for t in transactions if t.type == "Income")

    balance = total_income - total_expense

    if balance < 0:
        insights.append({
            "type": "warning",
            "title": "Overspending",
            "message": "You are spending more than you earn."
        })
    else:
        insights.append({
            "type": "success",
            "title": "Positive Balance",
            "message": "You have a positive balance."
        })

    # Top category
    category_totals = {}
    for t in transactions:
        if t.type == "Expense" and t.category:
            category_totals[t.category.name] = category_totals.get(t.category.name, 0) + t.amount

    if category_totals:
        top_category = max(category_totals, key=category_totals.get)
        insights.append({
            "type": "info",
            "title": "Top Spending",
            "message": f"Your highest spending category is {top_category}."
        })

    # Savings hint
    if saving_plans:
        insights.append({
            "type": "info",
            "title": "Savings",
            "message": "Consider allocating more funds toward your savings goals."
        })

    insights.append({
        "type": "info",
        "title": "Habit",
        "message": "Track daily spending to improve financial habits."
    })

    return insights


def generate_spending_advice(user, transactions, limits, saving_plans):
    """
    user: User object
    transactions: QuerySet of Transaction objects
    limits: dict with general + category limits
    saving_plans: QuerySet of SavingPlan objects
    """

    # Format transactions
    tx_summary = "\n".join(
        [f"{t.transaction_date.date()} | {t.category.name if t.category else 'Uncategorized'} | {t.type} | ₦{t.amount}" 
         for t in transactions]
    )

    # Format general/category limits
    limit_summary = []
    if limits.get("general"):
        limit_summary.append(f"General Limit: ₦{limits['general'].budget_amount} ({limits['general'].budget_plan})")
    for c_limit in limits.get("categories", []):
        limit_summary.append(f"{c_limit.category.name}: ₦{c_limit.budget_amount} ({c_limit.budget_plan})")
    limit_summary = "\n".join(limit_summary)

    # Format saving plans
    saving_summary = "\n".join(
        [f"{s.name} - Target: ₦{s.savings_amount}, Reached: ₦{s.savings_reached_amount}, Status: {s.status}" 
         for s in saving_plans]
    )

    prompt = f"""
        You are a financial advisor AI.

        Analyze the user's financial data and return structured insights.

        User: {user.username}

        Recent Transactions:
        {tx_summary}

        Budget / Spending Limits:
        {limit_summary if limit_summary else 'No budget limits set'}

        Saving Plans:
        {saving_summary if saving_summary else 'No saving plans set'}

        Your task:
        - Analyze income, spending, and budget
        - Identify financial health
        - Provide actionable advice

        IMPORTANT:
        - Return ONLY valid JSON
        - Do NOT include explanations, markdown, or extra text
        - Output must be a JSON array of objects

        Each object must follow this format:
        {{
        "type": "info" | "warning" | "success",
        "title": "Short title",
        "message": "Clear 1–2 sentence insight"
        }}

        Rules:
        - Use "warning" for overspending or risky behavior
        - Use "success" for positive financial habits
        - Use "info" for general observations or tips
        - Return 4–6 insights

        Example:
        [
        {{
            "type": "warning",
            "title": "Overspending",
            "message": "You are spending more than you earn this month."
        }},
        {{
            "type": "info",
            "title": "Top Category",
            "message": "Your highest spending category is Food."
        }}
        ]
        """

    models_to_try = [
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    MAX_RETRIES = 2
    last_error = None

    for model_name in models_to_try:
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                text = extract_json_array(response)
                if text:
                    return text

            except Exception as e:
                last_error = str(e)
                time.sleep(1.5 * (attempt + 1))

    return generate_fallback_insights(transactions, limits, saving_plans)