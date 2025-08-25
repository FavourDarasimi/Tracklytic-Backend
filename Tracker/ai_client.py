from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

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

    User: {user.username}
    Recent Transactions:
    {tx_summary}

    Spending Limits:
    {limit_summary if limit_summary else 'No limits set'}

    Saving Plans:
    {saving_summary if saving_summary else 'No saving plans set'}

    Task:
    1. Summarize their spending behavior.
    2. Highlight any overspending or risky categories.
    3. Suggest at least 3 personalized tips to improve money management.
    4. If possible, suggest how they can reach their saving goals faster.
    5. Keep advice clear and encouraging.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text