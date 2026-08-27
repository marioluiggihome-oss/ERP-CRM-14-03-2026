# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test suite for new roles and features:
- Director Comercial role (isAdmin)
- Responsable Delegación role (isResponsableDelegacion)
- canAuthorizePermissions field
- Tienda linked to Comercial (linkedRepresentativeId)
- isTienda role
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUserModelNewFields:
    """Test new user model fields: isResponsableDelegacion, canAuthorizePermissions, isTienda, linkedRepresentativeId"""
    
    def test_get_users_returns_new_fields(self):
        """Verify GET /api/users returns all new fields"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        
        users = response.json()
        assert len(users) > 0
        
        # Check first user has all new fields
        user = users[0]
        assert 'isResponsableDelegacion' in user, "Missing isResponsableDelegacion field"
        assert 'canAuthorizePermissions' in user, "Missing canAuthorizePermissions field"
        assert 'isTienda' in user, "Missing isTienda field"
        assert 'linkedRepresentativeId' in user, "Missing linkedRepresentativeId field"
        print(f"SUCCESS: User {user.get('username')} has all new fields")
    
    def test_create_responsable_delegacion_user(self):
        """Test creating a user with Responsable Delegación role"""
        user_data = {
            "username": "TEST_RESP_DELEG",
            "password": "test123",
            "clientName": "Test Responsable Delegación",
            "isResponsableDelegacion": True,
            "canAuthorizePermissions": True,
            "isActive": True
        }
        
        response = requests.post(f"{BASE_URL}/api/users", json=user_data)
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user['isResponsableDelegacion'] == True
        assert created_user['canAuthorizePermissions'] == True
        print(f"SUCCESS: Created Responsable Delegación user: {created_user['username']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{created_user['id']}")
    
    def test_create_tienda_linked_to_comercial(self):
        """Test creating a Tienda user linked to a Comercial"""
        # First get a comercial user to link to
        users_response = requests.get(f"{BASE_URL}/api/users")
        users = users_response.json()
        comercial = next((u for u in users if u.get('isRepresentative') or u.get('isAdmin')), None)
        
        if not comercial:
            pytest.skip("No comercial user found to link to")
        
        user_data = {
            "username": "TEST_TIENDA_LINKED",
            "password": "test123",
            "clientName": "Test Tienda Vinculada",
            "isTienda": True,
            "linkedRepresentativeId": comercial['id'],
            "isActive": True
        }
        
        response = requests.post(f"{BASE_URL}/api/users", json=user_data)
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user['isTienda'] == True
        assert created_user['linkedRepresentativeId'] == comercial['id']
        print(f"SUCCESS: Created Tienda linked to {comercial['clientName']}: {created_user['username']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{created_user['id']}")
    
    def test_update_user_responsable_delegacion(self):
        """Test updating a user to Responsable Delegación role"""
        # Create a test user first
        user_data = {
            "username": "TEST_UPDATE_RESP",
            "password": "test123",
            "clientName": "Test Update to Responsable",
            "isActive": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/users", json=user_data)
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # Update to Responsable Delegación
        update_data = {
            "isResponsableDelegacion": True,
            "canAuthorizePermissions": True
        }
        
        update_response = requests.put(f"{BASE_URL}/api/users/{created_user['id']}", json=update_data)
        assert update_response.status_code == 200
        
        updated_user = update_response.json()
        assert updated_user['isResponsableDelegacion'] == True
        assert updated_user['canAuthorizePermissions'] == True
        print(f"SUCCESS: Updated user to Responsable Delegación: {updated_user['username']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{created_user['id']}")


class TestDirectorComercialRole:
    """Test Director Comercial role (isAdmin) display and permissions"""
    
    def test_mario_is_director_comercial(self):
        """Verify MARIO user has isAdmin=True (Director Comercial)"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        
        users = response.json()
        mario = next((u for u in users if u.get('username') == 'MARIO'), None)
        
        assert mario is not None, "MARIO user not found"
        assert mario['isAdmin'] == True, "MARIO should be Director Comercial (isAdmin=True)"
        print(f"SUCCESS: MARIO is Director Comercial (isAdmin={mario['isAdmin']})")


class TestTiendaRole:
    """Test Tienda/Punto de Venta role"""
    
    def test_tienda_user_exists(self):
        """Verify there's a Tienda user in the system"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        
        users = response.json()
        tienda_users = [u for u in users if u.get('isTienda') == True]
        
        assert len(tienda_users) > 0, "No Tienda users found"
        print(f"SUCCESS: Found {len(tienda_users)} Tienda user(s)")
        
        for tienda in tienda_users:
            print(f"  - {tienda['clientName']} (@{tienda['username']}) linked to: {tienda.get('linkedRepresentativeId', 'None')}")
    
    def test_tienda_linked_to_comercial_not_client(self):
        """Verify Tienda users are linked to Comercial/Responsable/Director (not clients)"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        
        users = response.json()
        tienda_users = [u for u in users if u.get('isTienda') == True and u.get('linkedRepresentativeId')]
        
        if not tienda_users:
            pytest.skip("No linked Tienda users found")
        
        for tienda in tienda_users:
            linked_id = tienda.get('linkedRepresentativeId')
            # Verify the linked ID is a user ID (not a client ID)
            linked_user = next((u for u in users if u.get('id') == linked_id), None)
            
            if linked_user:
                assert linked_user.get('isAdmin') or linked_user.get('isResponsableDelegacion') or linked_user.get('isRepresentative'), \
                    f"Tienda {tienda['username']} is linked to non-comercial user"
                print(f"SUCCESS: Tienda {tienda['username']} is correctly linked to {linked_user['clientName']}")


class TestAPIEndpoints:
    """Test API endpoints work correctly with new fields"""
    
    def test_health_check(self):
        """Basic health check"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        print("SUCCESS: API health check passed")
    
    def test_users_endpoint(self):
        """Test users endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        print(f"SUCCESS: Users endpoint returned {len(users)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
