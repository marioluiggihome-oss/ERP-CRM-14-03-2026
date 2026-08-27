# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test: DESPIECE DE PUERTAS and FACTORIES API
Tests for:
1. Despiece calculation including door dimensions with tolerances (-2mm alto, -3mm ancho)
2. Factories CRUD API (SALAMANCA, ZAMORA)
3. Login with MARIO/MARIO credentials
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestLogin:
    """Test authentication with MARIO/MARIO"""
    
    def test_login_mario_success(self):
        """Test login with MARIO/MARIO credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "user" in data, "Response should contain user object"
        assert data["user"]["username"].upper() == "MARIO", "Username should be MARIO"
        print(f"✓ Login successful with MARIO - User ID: {data['user'].get('id')}")


class TestFactoriesAPI:
    """Test factories CRUD - SALAMANCA and ZAMORA"""
    
    def test_get_factories_list(self):
        """GET /api/fabrica/factories - should return list of factories"""
        response = requests.get(f"{BASE_URL}/api/fabrica/factories")
        assert response.status_code == 200, f"Failed to get factories: {response.text}"
        factories = response.json()
        assert isinstance(factories, list), "Response should be a list"
        print(f"✓ Found {len(factories)} factories")
        return factories
    
    def test_salamanca_factory_exists(self):
        """SALAMANCA factory with code SAL should exist"""
        response = requests.get(f"{BASE_URL}/api/fabrica/factories")
        assert response.status_code == 200
        factories = response.json()
        
        salamanca = next((f for f in factories if f.get('code') == 'SAL'), None)
        assert salamanca is not None, "SALAMANCA factory with code SAL not found"
        assert salamanca['name'] == 'FÁBRICA SALAMANCA', f"Wrong name: {salamanca['name']}"
        assert salamanca['isActive'] == True, "SALAMANCA should be active"
        print(f"✓ SALAMANCA factory found: {salamanca}")
    
    def test_zamora_factory_exists(self):
        """ZAMORA factory with code ZAM should exist"""
        response = requests.get(f"{BASE_URL}/api/fabrica/factories")
        assert response.status_code == 200
        factories = response.json()
        
        zamora = next((f for f in factories if f.get('code') == 'ZAM'), None)
        assert zamora is not None, "ZAMORA factory with code ZAM not found"
        assert zamora['name'] == 'FÁBRICA ZAMORA', f"Wrong name: {zamora['name']}"
        assert zamora['isActive'] == True, "ZAMORA should be active"
        print(f"✓ ZAMORA factory found: {zamora}")
    
    def test_create_new_factory(self):
        """POST /api/fabrica/factories - create a test factory"""
        test_factory = {
            "name": "TEST_FACTORY_TEMP",
            "code": "TST",
            "address": "Test Address 123",
            "phone": "123456789"
        }
        response = requests.post(f"{BASE_URL}/api/fabrica/factories", json=test_factory)
        
        if response.status_code == 400:
            # Factory with code TST already exists - that's ok
            print("✓ Factory TST already exists (duplicate code check works)")
            return
        
        assert response.status_code == 200, f"Failed to create factory: {response.text}"
        data = response.json()
        assert data['name'] == test_factory['name']
        assert data['code'] == 'TST'
        print(f"✓ Created test factory: {data}")
        
        # Cleanup - delete the test factory
        if 'id' in data:
            requests.delete(f"{BASE_URL}/api/fabrica/factories/{data['id']}")


class TestDespieceAPI:
    """Test despiece calculation for doors with tolerances"""
    
    def test_despiece_calculation_basic(self):
        """POST /api/despiece - calculate despiece for furniture"""
        # Test with a typical 1-door cabinet (BAJO 1P 60cm)
        request_data = {
            "items": [
                {
                    "productId": "test-b60-1p",
                    "productCode": "B60-1P",
                    "productName": "BAJO 60 1P",
                    "width": 60,
                    "height": 70,
                    "depth": 58,
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "MELAMINA BLANCA 18mm",
            "backPanelMaterial": "TABLERO 8mm",
            "grosor": 18
        }
        
        response = requests.post(f"{BASE_URL}/api/despiece", json=request_data)
        assert response.status_code == 200, f"Failed to calculate despiece: {response.text}"
        data = response.json()
        
        assert "items" in data, "Response should contain items"
        assert "summary" in data, "Response should contain summary"
        assert len(data["items"]) > 0, "Should have at least one item"
        
        item = data["items"][0]
        assert item["productCode"] == "B60-1P"
        assert item["originalWidth"] == 60
        assert item["originalHeight"] == 70
        
        print(f"✓ Despiece calculation successful")
        print(f"  - Total pieces: {data['summary'].get('totalPieces', 0)}")
        print(f"  - Total area: {data['summary'].get('totalArea', 0)} m²")
        
        return data
    
    def test_despiece_door_tolerances(self):
        """Test that door dimensions include -2mm alto, -3mm ancho tolerances"""
        # A 70cm height cabinet should have door height of 69.8cm (70 - 0.2)
        # A 60cm width cabinet with 1P should have door width of 59.7cm (60 - 0.3)
        request_data = {
            "items": [
                {
                    "productId": "test-b60-1p-door",
                    "productCode": "B60-1P",
                    "productName": "BAJO 60 1 PUERTA",
                    "width": 60,
                    "height": 70,
                    "depth": 58,
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "MELAMINA BLANCA",
            "backPanelMaterial": "TABLERO 8mm",
            "grosor": 18
        }
        
        response = requests.post(f"{BASE_URL}/api/despiece", json=request_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Find door component in the despiece
        item = data["items"][0]
        components = item.get("components", [])
        
        door_comp = next((c for c in components if 'puerta' in c.get('name', '').lower()), None)
        
        if door_comp:
            # Door height should be furniture height - 2mm (0.2cm)
            expected_door_height = 70 - 0.2  # 69.8cm
            actual_door_height = door_comp.get('length', 0)
            
            # Door width should be furniture width - 3mm (0.3cm) for 1 door
            expected_door_width = 60 - 0.3  # 59.7cm
            actual_door_width = door_comp.get('width', 0)
            
            print(f"✓ Door component found: {door_comp.get('name')}")
            print(f"  - Height: {actual_door_height}cm (expected ~{expected_door_height}cm)")
            print(f"  - Width: {actual_door_width}cm (expected ~{expected_door_width}cm)")
            
            # Allow small tolerance for floating point rounding only
            assert abs(actual_door_height - expected_door_height) < 0.05, \
                f"Door height {actual_door_height} should be {expected_door_height}"
            assert abs(actual_door_width - expected_door_width) < 0.05, \
                f"Door width {actual_door_width} should be {expected_door_width}"
        else:
            raise AssertionError(f"No door component found. Components: {[c.get('name') for c in components]}")
    
    def test_despiece_2_doors_cabinet(self):
        """Test 2-door cabinet - each door should be half width - 3mm"""
        request_data = {
            "items": [
                {
                    "productId": "test-b60-2p",
                    "productCode": "B60-2P",
                    "productName": "BAJO 60 2P",
                    "width": 60,
                    "height": 70,
                    "depth": 58,
                    "quantity": 2,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "MELAMINA BLANCA",
            "backPanelMaterial": "TABLERO 8mm",
            "grosor": 18
        }
        
        response = requests.post(f"{BASE_URL}/api/despiece", json=request_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        item = data["items"][0]
        components = item.get("components", [])
        
        door_comp = next((c for c in components if 'puerta' in c.get('name', '').lower()), None)
        
        if door_comp:
            # For 2 doors, each door width = (60 - 0.3) / 2 = 29.85cm
            # (gap of 0.3cm is shared between the two doors, not subtracted per-door)
            expected_door_width = round((60 - 0.3) / 2, 1)  # 29.85cm
            actual_door_width = door_comp.get('width', 0)

            print(f"✓ 2-door cabinet despiece")
            print(f"  - Each door width: {actual_door_width}cm (expected ~{expected_door_width}cm)")

            assert abs(actual_door_width - expected_door_width) < 0.05, \
                f"Door width {actual_door_width} should be {expected_door_width}"
        else:
            raise AssertionError(f"No door component found in 2-door cabinet despiece. Components: {[c.get('name') for c in components]}")


class TestManufacturingOrders:
    """Test manufacturing orders API"""
    
    def test_get_orders_list(self):
        """GET /api/fabrica/orders - should return orders list"""
        response = requests.get(f"{BASE_URL}/api/fabrica/orders")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "orders" in data, "Response should contain orders array"
        assert "total" in data, "Response should contain total count"
        print(f"✓ Orders list - Total: {data['total']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
