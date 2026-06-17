import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    def test_register_user_success(self):
        client = APIClient()
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
            "re_password": "StrongPass123!",
        }
        response = client.post("/auth/v1/users/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="test@example.com").exists()

    def test_register_user_password_mismatch(self):
        client = APIClient()
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "StrongPass123!",
            "re_password": "DifferentPass123!",
        }
        response = client.post("/auth/v1/users/", data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    def test_login_success(self):
        User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="StrongPass123!",
        )
        client = APIClient()
        response = client.post(
            "/auth/v1/jwt/create/",
            {"email": "test@example.com", "password": "StrongPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_login_invalid_credentials(self):
        client = APIClient()
        response = client.post(
            "/auth/v1/jwt/create/",
            {"email": "nonexistent@example.com", "password": "wrong"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_access_denied(self):
        client = APIClient()
        response = client.get("/api/v1/categories/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
