from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import (
    CategoryViewSet, TransactionViewSet, RecurringTransactionViewSet,
    GeneralBudgetViewSet, CategoryBudgetViewSet, SavingPlanViewSet,
    DashboardOverview, ParseReceiptView, AiClient, CheckStatusOfUserSavingPlans,
    RenewSavingGoal,
)

router = SimpleRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('recurring-transactions', RecurringTransactionViewSet, basename='recurring-transaction')
router.register('general-budgets', GeneralBudgetViewSet, basename='general-budget')
router.register('category-budgets', CategoryBudgetViewSet, basename='category-budget')
router.register('saving-plans', SavingPlanViewSet, basename='saving-plan')

urlpatterns = [
    path('dashboard/overview/', DashboardOverview.as_view()),
    path('transaction/upload/receipt/', ParseReceiptView.as_view()),
    path('ai/insights/', AiClient.as_view()),
    path('check/saving/plan/status/', CheckStatusOfUserSavingPlans.as_view()),
    path('renew/saving/plan/<int:pk>/', RenewSavingGoal.as_view()),
]

urlpatterns += router.urls
