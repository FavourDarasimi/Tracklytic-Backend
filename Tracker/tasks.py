from datetime import date

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.db import transaction

from Tracker.models import RecurringTransaction, Transaction


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
