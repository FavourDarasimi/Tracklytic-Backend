from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=10 * 60,
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,
        )

        response.data = {'message': 'Login successful'}
        return response

class Logout(APIView):
    def post(self,request:Request):
        response = Response({
            'status': 'success',
            'message': 'User Logged out'
        })
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

    # day2
# Create your views here.
