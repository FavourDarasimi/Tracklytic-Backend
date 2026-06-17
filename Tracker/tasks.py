import os
from datetime import date

import requests
from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.db import transaction

from Tracker.models import CurrencyExchangeRate, RecurringTransaction, Transaction


@shared_task
def process_due_recurring_transactions():
    due = RecurringTransaction.objects.filter(
        active=True, next_due_date__lte=date.today()
    ).select_related('user', 'category')

    created_count = 0
    deactivated_count = 0

    for rt in due:
        with transaction.atomic():
            Transaction.objects.create(
                user=rt.user,
                category=rt.category,
                amount=rt.amount,
                type="Expense",
                party_name=f"Recurring: {rt.category.name}",
                recurring=True,
            )

            delta = {
                'Daily': relativedelta(days=1),
                'Weekly': relativedelta(weeks=1),
                'Monthly': relativedelta(months=1),
                'Yearly': relativedelta(years=1),
            }.get(rt.frequency)

            if delta:
                rt.next_due_date += delta

            if rt.end_date and rt.next_due_date > rt.end_date:
                rt.active = False
                deactivated_count += 1

            rt.save()
            created_count += 1

    return f"Created {created_count} transactions, deactivated {deactivated_count} recurring plans"


@shared_task
def update_exchange_rates():
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    if not api_key:
        return "EXCHANGE_RATE_API_KEY not set, skipping rate update"

    base = "USD"
    try:
        resp = requests.get(
            f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("conversion_rates", {})

        from Account.models import CURRENCIES
        supported = [code for code, _ in CURRENCIES]

        count = 0
        for target, rate in rates.items():
            if target in supported and target != base:
                CurrencyExchangeRate.objects.update_or_create(
                    base_currency=base,
                    target_currency=target,
                    defaults={"rate": rate},
                )
                count += 1

        for target in supported:
            if target != base and target in rates:
                inverse_rate = 1.0 / rates[target]
                CurrencyExchangeRate.objects.update_or_create(
                    base_currency=target,
                    target_currency=base,
                    defaults={"rate": inverse_rate},
                )

        return f"Updated {count} exchange rates"
    except requests.RequestException as e:
        return f"Failed to update exchange rates: {e}"
