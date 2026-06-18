from django.contrib import admin

from Tracker.models import Category, Transaction, GeneralBudget, CategoryBudget, SavingPlan, RecurringTransaction

admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(GeneralBudget)
admin.site.register(CategoryBudget)
admin.site.register(SavingPlan)
admin.site.register(RecurringTransaction)
