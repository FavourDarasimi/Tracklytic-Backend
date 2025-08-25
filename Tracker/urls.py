from django.urls import path, include
from .views import AddTransacion, AddCategory, AiClient,  GetUserCategories, \
    AddGeneralSpendingLimit, \
    AddCategorySpendingLimit, EditGeneralSpendingLimit, EditCategorySpendingLimit, AddSavingPlan, \
    CheckStatusOfUserSavingPlans, RenewSavingGoal, UserSavingPlan,UploadReceipt

urlpatterns = [
    path('add/category/',AddCategory.as_view()),
    # path('add/subcategory/',AddSubCategory.as_view()),
    path('add/transaction/',AddTransacion.as_view()),
    path('get/categories/',GetUserCategories.as_view()),
    path('add/general/budget/',AddGeneralSpendingLimit.as_view()),
    path('add/category/budget/',AddCategorySpendingLimit.as_view()),
    path('edit/general/budget/<int:pk>/',EditGeneralSpendingLimit.as_view()),
    path('edit/category/budget/<int:pk>/',EditCategorySpendingLimit.as_view()),
#day2
    path('add/saving/plan/',AddSavingPlan.as_view()),
    path('check/saving/plan/status/',CheckStatusOfUserSavingPlans.as_view()),
    path('renew/saving/plan/<int:pk>',RenewSavingGoal.as_view()),
    path('user/saving/plan/',UserSavingPlan.as_view()),
    path('transaction/upload/receipt/',UploadReceipt.as_view()),

    path('ai/insights/',AiClient.as_view()),
]