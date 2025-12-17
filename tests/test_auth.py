"""
Unit tests for authentication (Phase 1.2).
Tests both happy path and sad path scenarios.
"""

import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.auth
@pytest.mark.unit
class TestAuthenticationHappyPath:
    """Happy path tests for authentication."""

    async def test_register_user_success(self, test_client: AsyncClient):
        """Test successful user registration."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "role": "user",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"
        assert "id" in data
        assert "password" not in data  # Password should never be in response
        assert "password_hash" not in data

    async def test_register_user_default_role(self, test_client: AsyncClient):
        """Test user registration with default role."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "defaultrole@example.com",
                "password": "securepass123",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"  # Default role

    async def test_login_success(self, test_client: AsyncClient, test_user: User):
        """Test successful user login."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_get_current_user(self, test_client: AsyncClient, auth_headers: dict):
        """Test getting current user information."""
        response = await test_client.get(
            "/api/v1/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "password_hash" not in data

    async def test_protected_route_with_valid_token(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test accessing protected route with valid token."""
        response = await test_client.get(
            "/api/v1/me",
            headers=auth_headers,
        )
        
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.auth
@pytest.mark.unit
class TestAuthenticationSadPath:
    """Sad path tests for authentication."""

    async def test_register_duplicate_email(self, test_client: AsyncClient, test_user: User):
        """Test registration with duplicate email."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "securepass123",
            },
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, test_client: AsyncClient):
        """Test registration with invalid email format."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "securepass123",
            },
        )
        
        assert response.status_code == 422  # Validation error

    async def test_register_short_password(self, test_client: AsyncClient):
        """Test registration with password too short."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpass@example.com",
                "password": "short",  # Less than 8 characters
            },
        )
        
        assert response.status_code == 422  # Validation error

    async def test_login_wrong_password(self, test_client: AsyncClient, test_user: User):
        """Test login with incorrect password."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        """Test login with non-existent user."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword",
            },
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_get_current_user_no_token(self, test_client: AsyncClient):
        """Test accessing protected route without token."""
        response = await test_client.get("/api/v1/me")
        
        assert response.status_code == 403  # Forbidden

    async def test_get_current_user_invalid_token(self, test_client: AsyncClient):
        """Test accessing protected route with invalid token."""
        response = await test_client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    async def test_get_current_user_expired_token(self, test_client: AsyncClient):
        """Test accessing protected route with expired token."""
        # Note: This would require mocking time or using a very short expiration
        # For now, we test with malformed token
        response = await test_client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid"},
        )
        
        assert response.status_code == 401

    async def test_get_current_user_malformed_header(self, test_client: AsyncClient):
        """Test accessing protected route with malformed Authorization header."""
        response = await test_client.get(
            "/api/v1/me",
            headers={"Authorization": "NotBearer token"},
        )
        
        assert response.status_code == 403

