import logging

from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer,UserCreatePasswordRetypeSerializer
from .models import CustomUser

logger = logging.getLogger(__name__)

class CustomUserCreateSerializer(UserCreatePasswordRetypeSerializer):
    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password']

    

    def perform_create(self, validated_data):
        logger.debug("perform_create called with data: %s", validated_data)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False,
        )
        return user
        
  
class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name','last_name', 'created_at']

#day2