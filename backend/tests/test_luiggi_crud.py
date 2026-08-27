# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Backend API Tests for LUIGGI HOME ERP/CRM
Tests: Auth, Users CRUD, Products CRUD, Materials CRUD, Settings
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============================================
# AUTH TESTS
# ============================================

class TestAuth:
    """Test authentication endpoints"""
    
    def test_login_success_mario(self):
        """Test login with MARIO/MARIO credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "MARIO", "password": "MARIO"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "user" in data
        assert data["user"]["username"] == "MARIO"
        assert data["user"]["isAdmin"] == True
    
    def test_login_case_insensitive(self):
        """Test login is case insensitive for username"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "mario", "password": "MARIO"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "INVALID", "password": "WRONG"}
        )
        assert response.status_code == 401
    
    def test_init_endpoint(self):
        """Test init endpoint creates admin if not exists"""
        response = requests.post(f"{BASE_URL}/api/init")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


# ============================================
# USERS CRUD TESTS
# ============================================

class TestUsersCRUD:
    """Test Users CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_user_id = None
        yield
        # Cleanup: Delete test user if created
        if self.test_user_id:
            try:
                requests.delete(f"{BASE_URL}/api/users/{self.test_user_id}")
            except:
                pass
    
    def test_get_all_users(self):
        """Test getting all users"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least admin user
        assert len(data) >= 1
        # Check admin exists
        admin = next((u for u in data if u["id"] == "admin"), None)
        assert admin is not None
        assert admin["username"] == "MARIO"
    
    def test_create_user_comercial(self):
        """Test creating a new Comercial user"""
        unique_name = f"TEST_COMERCIAL_{uuid.uuid4().hex[:6]}"
        user_data = {
            "username": unique_name,
            "password": "TEST123",
            "clientName": "Test Comercial S.L.",
            "isActive": True,
            "isAdmin": False,
            "isRepresentative": True,
            "allowedModules": ["montada", "despiece"],
            "commercialDiscount": 30,
            "canSeeCost": True,
            "canSeeRetail": True,
            "canUseAIAnalysis": False,
            "canManageArticles": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users",
            json=user_data
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response data
        assert "id" in data
        assert data["username"] == unique_name.upper()
        assert data["clientName"] == "Test Comercial S.L."
        assert data["isRepresentative"] == True
        assert data["commercialDiscount"] == 30
        
        self.test_user_id = data["id"]
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/users/{self.test_user_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["username"] == unique_name.upper()
    
    def test_create_user_tienda(self):
        """Test creating a new Tienda user"""
        unique_name = f"TEST_TIENDA_{uuid.uuid4().hex[:6]}"
        user_data = {
            "username": unique_name,
            "password": "TIENDA123",
            "clientName": "Cocinas Madrid Test",
            "isActive": True,
            "isAdmin": False,
            "isRepresentative": False,
            "allowedModules": ["montada"],
            "commercialDiscount": 20
        }
        
        response = requests.post(
            f"{BASE_URL}/api/users",
            json=user_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["isRepresentative"] == False
        assert data["isAdmin"] == False
        self.test_user_id = data["id"]
    
    def test_create_duplicate_username_fails(self):
        """Test that creating user with duplicate username fails"""
        response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "username": "MARIO",
                "password": "TEST",
                "clientName": "Duplicate Test"
            }
        )
        assert response.status_code == 400
    
    def test_update_user(self):
        """Test updating a user"""
        # First create a user
        unique_name = f"TEST_UPDATE_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "username": unique_name,
                "password": "TEST123",
                "clientName": "Original Name",
                "commercialDiscount": 10
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        self.test_user_id = user_id
        
        # Update the user
        update_response = requests.put(
            f"{BASE_URL}/api/users/{user_id}",
            json={
                "clientName": "Updated Name",
                "commercialDiscount": 25
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["clientName"] == "Updated Name"
        assert updated["commercialDiscount"] == 25
        
        # Verify with GET
        get_response = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["clientName"] == "Updated Name"
    
    def test_delete_user(self):
        """Test deleting a user"""
        # First create a user
        unique_name = f"TEST_DELETE_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/users",
            json={
                "username": unique_name,
                "password": "TEST123",
                "clientName": "To Delete"
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Delete the user
        delete_response = requests.delete(f"{BASE_URL}/api/users/{user_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion with GET
        get_response = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert get_response.status_code == 404
    
    def test_cannot_delete_admin(self):
        """Test that admin user cannot be deleted"""
        response = requests.delete(f"{BASE_URL}/api/users/admin")
        assert response.status_code == 400


# ============================================
# PRODUCTS CRUD TESTS
# ============================================

class TestProductsCRUD:
    """Test Products CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_product_ids = []
        yield
        # Cleanup: Delete test products
        for pid in self.test_product_ids:
            try:
                requests.delete(f"{BASE_URL}/api/products/{pid}")
            except:
                pass
    
    def test_get_all_products(self):
        """Test getting all products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_products_by_module_montada(self):
        """Test getting products filtered by montada module"""
        response = requests.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_products_by_module_despiece(self):
        """Test getting products filtered by despiece module"""
        response = requests.get(f"{BASE_URL}/api/products?module=despiece")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_product_montada(self):
        """Test creating a product in montada catalog with zone points"""
        product_data = {
            "code": f"TEST-M-{uuid.uuid4().hex[:6]}",
            "name": "Test Alto 1 Puerta 35cm",
            "category": "Altos",
            "series": "Altos 35cm",
            "width": 35,
            "height": 70,
            "depth": 33,
            "module": "montada",
            "zonePoints": {
                "Z1": 100, "Z2": 110, "Z3": 120, "Z4": 130,
                "Z5": 140, "Z6": 150, "Z7": 160, "Z8": 170,
                "Z9": 180, "Z10": 190, "Z11": 200, "Z12": 210
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["code"] == product_data["code"].upper()
        assert data["name"] == product_data["name"]
        assert data["module"] == "montada"
        assert data["zonePoints"]["Z1"] == 100
        assert data["points"] == 100  # Should be set from Z1
        
        self.test_product_ids.append(data["id"])
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/products/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["code"] == product_data["code"].upper()
    
    def test_create_product_despiece(self):
        """Test creating a product in despiece catalog with base points"""
        product_data = {
            "code": f"TEST-D-{uuid.uuid4().hex[:6]}",
            "name": "Test Componente Despiece",
            "category": "Componentes",
            "width": 60,
            "height": 80,
            "depth": 58,
            "module": "despiece",
            "points": 50,
            "zonePoints": {
                "Z1": 50, "Z2": 50, "Z3": 50, "Z4": 50,
                "Z5": 50, "Z6": 50, "Z7": 50, "Z8": 50,
                "Z9": 50, "Z10": 50, "Z11": 50, "Z12": 50
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["module"] == "despiece"
        self.test_product_ids.append(data["id"])
    
    def test_create_products_bulk(self):
        """Test bulk product creation"""
        products = [
            {
                "code": f"BULK-1-{uuid.uuid4().hex[:6]}",
                "name": "Bulk Product 1",
                "module": "montada",
                "points": 100
            },
            {
                "code": f"BULK-2-{uuid.uuid4().hex[:6]}",
                "name": "Bulk Product 2",
                "module": "montada",
                "points": 150
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/products/bulk",
            json=products
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        for product in data:
            self.test_product_ids.append(product["id"])
    
    def test_update_product(self):
        """Test updating a product"""
        # Create product first
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            json={
                "code": f"TEST-UPD-{uuid.uuid4().hex[:6]}",
                "name": "Original Product Name",
                "module": "montada",
                "points": 100
            }
        )
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]
        self.test_product_ids.append(product_id)
        
        # Update product
        update_response = requests.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={
                "code": f"TEST-UPD-{uuid.uuid4().hex[:6]}",
                "name": "Updated Product Name",
                "module": "montada",
                "points": 200
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated Product Name"
        
        # Verify with GET
        get_response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == "Updated Product Name"
    
    def test_delete_product(self):
        """Test deleting a product"""
        # Create product first
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            json={
                "code": f"TEST-DEL-{uuid.uuid4().hex[:6]}",
                "name": "To Delete",
                "module": "montada",
                "points": 100
            }
        )
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]
        
        # Delete product
        delete_response = requests.delete(f"{BASE_URL}/api/products/{product_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/products/{product_id}")
        assert get_response.status_code == 404
    
    def test_delete_products_bulk(self):
        """Test bulk product deletion"""
        # Create products first
        products = []
        for i in range(3):
            response = requests.post(
                f"{BASE_URL}/api/products",
                json={
                    "code": f"BULK-DEL-{i}-{uuid.uuid4().hex[:6]}",
                    "name": f"Bulk Delete {i}",
                    "module": "montada",
                    "points": 100
                }
            )
            assert response.status_code == 200
            products.append(response.json()["id"])
        
        # Bulk delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/products/bulk/delete",
            json=products
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert "3 productos eliminados" in data["message"]
        
        # Verify all deleted
        for pid in products:
            get_response = requests.get(f"{BASE_URL}/api/products/{pid}")
            assert get_response.status_code == 404


# ============================================
# MATERIALS CRUD TESTS
# ============================================

class TestMaterialsCRUD:
    """Test Materials CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_material_ids = []
        yield
        # Cleanup: Delete test materials
        for mid in self.test_material_ids:
            try:
                requests.delete(f"{BASE_URL}/api/materials/{mid}")
            except:
                pass
    
    def test_get_all_materials(self):
        """Test getting all materials"""
        response = requests.get(f"{BASE_URL}/api/materials")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_material(self):
        """Test creating a new material"""
        material_data = {
            "name": f"Test Material {uuid.uuid4().hex[:6]}",
            "fixedIncrement": 15.5,
            "thickness": 18
        }
        
        response = requests.post(
            f"{BASE_URL}/api/materials",
            json=material_data
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["name"] == material_data["name"]
        assert data["fixedIncrement"] == 15.5
        assert data["thickness"] == 18
        
        self.test_material_ids.append(data["id"])
    
    def test_update_material(self):
        """Test updating a material"""
        # Create material first
        create_response = requests.post(
            f"{BASE_URL}/api/materials",
            json={
                "name": f"Test Update Material {uuid.uuid4().hex[:6]}",
                "fixedIncrement": 10,
                "thickness": 16
            }
        )
        assert create_response.status_code == 200
        material_id = create_response.json()["id"]
        self.test_material_ids.append(material_id)
        
        # Update material
        update_response = requests.put(
            f"{BASE_URL}/api/materials/{material_id}",
            json={
                "name": "Updated Material Name",
                "fixedIncrement": 20,
                "thickness": 22
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated Material Name"
        assert updated["fixedIncrement"] == 20


# ============================================
# SETTINGS TESTS
# ============================================

class TestSettings:
    """Test Settings endpoints"""
    
    def test_get_settings(self):
        """Test getting global settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        
        # Check expected fields exist
        assert "pointValueMontada" in data
        assert "pointValueDespiece" in data
        assert "brandColor" in data
    
    def test_update_settings(self):
        """Test updating global settings"""
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings")
        original = get_response.json()
        
        # Update settings
        update_response = requests.put(
            f"{BASE_URL}/api/settings",
            json={
                "pointValueMontada": 1.5,
                "brandColor": "#ff5500"
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["pointValueMontada"] == 1.5
        assert updated["brandColor"] == "#ff5500"
        
        # Restore original settings
        requests.put(
            f"{BASE_URL}/api/settings",
            json={
                "pointValueMontada": original.get("pointValueMontada", 1.0),
                "brandColor": original.get("brandColor", "#ea580c")
            }
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
