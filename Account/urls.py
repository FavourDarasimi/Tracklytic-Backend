# yourapp/urls.py
from django.urls import path, include
from .views import CustomTokenObtainPairView, Logout

urlpatterns = [
    path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('logout/', Logout.as_view()),
#day2
]