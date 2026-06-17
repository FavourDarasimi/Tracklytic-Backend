from django.urls import path, include
from .views import CustomTokenObtainPairView, Logout, UserProfileView

urlpatterns = [
    # path('jwt/create/', CustomTokenObtainPairView.as_view()),
    path('logout/', Logout.as_view()),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]