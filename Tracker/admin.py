from django.contrib import admin

from Tracker.models import Category, Transaction, GeneralSpendingLimit, CategorySpendingLimit, SavingPlan,RecurringTransaction

admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(GeneralSpendingLimit)
admin.site.register(CategorySpendingLimit)
#day2
admin.site.register(SavingPlan)
admin.site.register(RecurringTransaction)
# Register your models here.
