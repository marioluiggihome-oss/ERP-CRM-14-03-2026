# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test Suite for Authentication and Permissions - LUIGGI HOME
Tests:
1. Traditional login (MARIO/MARIO)
2. Permission check: canAccessArmarios
3. Email registration flow
4. Email verification
5. Login with email
6. 2FA enable/verify flow
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = "MARIO"
TEST_PASSWORD = "MARIO"
TEST_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_NEW_PASSWORD = "Test1234Abc"


class TestTraditionalLogin:
    """Test traditional username/password login"""
    
    def test_login_success_mario(self):
        """Test MARIO/MARIO login works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "user" in data
        assert "tokens" in data
        
        user = data["user"]
        assert user["username"] == "MARIO"
        assert user["isAdmin"] == True
        
        # Verify tokens structure
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
    def test_login_invalid_credentials(self):
        """Test login with wrong credentials fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "WRONG", "password": "WRONG"}
        )
        assert response.status_code == 401


class TestArmarioPermission:
    """Test Armarios module permission check"""
    
    def test_mario_does_not_have_armarios_permission(self):
        """Verify MARIO user does NOT have canAccessArmarios permission"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        user = data["user"]
        
        # CRITICAL: MARIO should NOT have canAccessArmarios
        assert user.get("canAccessArmarios") == False, \
            f"MARIO should NOT have canAccessArmarios permission, but got: {user.get('canAccessArmarios')}"
        
        # MARIO is admin, so isAdmin should be True
        assert user.get("isAdmin") == True
        
    def test_get_users_shows_armarios_permission(self):
        """Verify users endpoint returns canAccessArmarios field"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) > 0
        
        # Find MARIO user
        mario = next((u for u in users if u.get("username") == "MARIO"), None)
        assert mario is not None, "MARIO user not found"
        
        # Verify canAccessArmarios field exists and is False
        assert "canAccessArmarios" in mario
        assert mario["canAccessArmarios"] == False


class TestEmailRegistration:
    """Test email registration flow"""
    
    def test_register_new_user(self):
        """Test registering a new user with email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": TEST_NEW_PASSWORD,
                "firstName": "Test",
                "lastName": "User",
                "company": "Test Company",
                "phone": "123456789"
            }
        )
        
        # Should succeed with 200
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("requiresEmailVerification") == True
        assert "userId" in data
        
    def test_register_duplicate_email_fails(self):
        """Test registering with existing email fails"""
        # First registration
        email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        response1 = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": TEST_NEW_PASSWORD,
                "firstName": "Test",
                "lastName": "User"
            }
        )
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        response2 = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": TEST_NEW_PASSWORD,
                "firstName": "Test2",
                "lastName": "User2"
            }
        )
        assert response2.status_code == 400
        
    def test_register_password_mismatch_fails(self):
        """Test registration with mismatched passwords fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": "DifferentPassword123",
                "firstName": "Test",
                "lastName": "User"
            }
        )
        assert response.status_code == 400
        
    def test_register_weak_password_fails(self):
        """Test registration with weak password fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password": "weak",
                "confirmPassword": "weak",
                "firstName": "Test",
                "lastName": "User"
            }
        )
        assert response.status_code == 400


class TestEmailVerification:
    """Test email verification flow"""
    
    def test_verify_email_wrong_code_fails(self):
        """Test verification with wrong code fails"""
        # Register first
        email = f"test_verify_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": TEST_NEW_PASSWORD,
                "firstName": "Test",
                "lastName": "User"
            }
        )
        
        # Try to verify with wrong code
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-email",
            json={"email": email, "code": "000000"}
        )
        assert response.status_code == 400
        
    def test_verify_nonexistent_user_fails(self):
        """Test verification for non-existent user fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-email",
            json={"email": "nonexistent@example.com", "code": "123456"}
        )
        assert response.status_code == 404


class TestLoginWithEmail:
    """Test login with email endpoint"""
    
    def test_login_email_unverified_fails(self):
        """Test login with unverified email fails"""
        # Register but don't verify
        email = f"test_unverified_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": email,
                "password": TEST_NEW_PASSWORD,
                "confirmPassword": TEST_NEW_PASSWORD,
                "firstName": "Test",
                "lastName": "User"
            }
        )
        
        # Try to login
        response = requests.post(
            f"{BASE_URL}/api/auth/login-email",
            json={"email": email, "password": TEST_NEW_PASSWORD}
        )
        assert response.status_code == 401
        
    def test_login_email_wrong_password_fails(self):
        """Test login with wrong password fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login-email",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


class Test2FAEndpoints:
    """Test 2FA enable/verify endpoints"""
    
    def test_2fa_enable_requires_auth(self):
        """Test 2FA enable requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/2fa/enable",
            json={"userId": "admin"}
        )
        # Should fail without auth token
        assert response.status_code in [401, 403]
        
    def test_2fa_verify_requires_auth(self):
        """Test 2FA verify requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/2fa/verify",
            json={"userId": "admin", "code": "123456"}
        )
        # Should fail without auth token
        assert response.status_code in [401, 403]
        
    def test_2fa_status_requires_auth(self):
        """Test 2FA status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/2fa/status/admin")
        # Should fail without auth token
        assert response.status_code in [401, 403]


class Test2FAWithAuth:
    """Test 2FA with authenticated user"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for MARIO user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["tokens"]["access_token"]
        pytest.skip("Could not get auth token")
        
    def test_2fa_enable_with_auth(self, auth_token):
        """Test 2FA enable with valid auth token"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/auth/2fa/enable",
            json={"userId": "admin"},
            headers=headers
        )
        
        # Should succeed or return already enabled
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "secret" in data
            assert "qrCodeUrl" in data
            assert "backupCodes" in data
            assert len(data["backupCodes"]) == 8
            
    def test_2fa_status_with_auth(self, auth_token):
        """Test 2FA status with valid auth token"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/auth/2fa/status/admin",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "backupCodesRemaining" in data


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def test_refresh_token_works(self):
        """Test refresh token generates new access token"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        
        # Use refresh token
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
    def test_refresh_invalid_token_fails(self):
        """Test refresh with invalid token fails"""
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401


class TestAuthMe:
    """Test /auth/me endpoint"""
    
    def test_auth_me_with_valid_token(self):
        """Test getting current user info with valid token"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        assert login_response.status_code == 200
        
        access_token = login_response.json()["tokens"]["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "user" in data
        assert data["user"]["username"] == "MARIO"
        
    def test_auth_me_without_token_fails(self):
        """Test getting current user without token fails"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
