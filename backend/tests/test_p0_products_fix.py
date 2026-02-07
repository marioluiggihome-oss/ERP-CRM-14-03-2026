"""
Test P0 Bug Fix: 733 new products (COSTADOS, REGLETAS, ZOCALOS, CORNISAS, ESTANTES, VITRINAS) 
now have module='montada' and appear in frontend.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProductsP0Fix:
    """Test that the P0 bug fix for 733 products is working correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data['tokens']['access_token']
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_total_products_count(self):
        """Verify that 6,438 products are loaded correctly"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200, f"Failed to get products: {response.text}"
        products = response.json()
        assert len(products) == 6438, f"Expected 6438 products, got {len(products)}"
    
    def test_costados_category_exists(self):
        """Verify COSTADOS category has 241 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        costados = [p for p in products if p.get('category', '').upper() == 'COSTADOS']
        assert len(costados) == 241, f"Expected 241 COSTADOS, got {len(costados)}"
    
    def test_regletas_category_exists(self):
        """Verify REGLETAS category has 40 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        regletas = [p for p in products if p.get('category', '').upper() == 'REGLETAS']
        assert len(regletas) == 40, f"Expected 40 REGLETAS, got {len(regletas)}"
    
    def test_zocalos_category_exists(self):
        """Verify ZOCALOS category has 8 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        zocalos = [p for p in products if p.get('category', '').upper() == 'ZOCALOS']
        assert len(zocalos) == 8, f"Expected 8 ZOCALOS, got {len(zocalos)}"
    
    def test_cornisas_category_exists(self):
        """Verify CORNISAS category has 7 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        cornisas = [p for p in products if p.get('category', '').upper() == 'CORNISAS']
        assert len(cornisas) == 7, f"Expected 7 CORNISAS, got {len(cornisas)}"
    
    def test_estantes_category_exists(self):
        """Verify ESTANTES category has 115 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        estantes = [p for p in products if p.get('category', '').upper() == 'ESTANTES']
        assert len(estantes) == 115, f"Expected 115 ESTANTES, got {len(estantes)}"
    
    def test_vitrinas_category_exists(self):
        """Verify VITRINAS category has 161 products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        vitrinas = [p for p in products if p.get('category', '').upper() == 'VITRINAS']
        assert len(vitrinas) == 161, f"Expected 161 VITRINAS, got {len(vitrinas)}"
    
    def test_all_new_categories_have_module_montada(self):
        """Verify all new category products have module='montada'"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        
        new_categories = ['COSTADOS', 'REGLETAS', 'ZOCALOS', 'CORNISAS', 'ESTANTES', 'VITRINAS']
        for cat in new_categories:
            cat_products = [p for p in products if p.get('category', '').upper() == cat]
            for p in cat_products:
                assert p.get('module') == 'montada', f"Product {p.get('code')} in {cat} has module={p.get('module')}"
    
    def test_search_costado_returns_products(self):
        """Verify searching 'COSTADO' returns products"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        
        # Simulate frontend search
        search_term = 'COSTADO'
        matching = [p for p in products if search_term.upper() in p.get('name', '').upper() or 
                    search_term.upper() in p.get('code', '').upper() or
                    search_term.upper() in p.get('category', '').upper()]
        assert len(matching) >= 241, f"Expected at least 241 products matching 'COSTADO', got {len(matching)}"


class TestClientDeletion:
    """Test client deletion functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data['tokens']['access_token']
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_create_and_delete_client(self):
        """Test creating and deleting a client"""
        # Create a test client
        client_data = {
            "nombre": "TEST_CLIENT_TO_DELETE",
            "tipo": "potencial",
            "email": "test_delete@example.com",
            "telefono": "123456789"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/clients", json=client_data)
        assert create_response.status_code == 200, f"Failed to create client: {create_response.text}"
        created_client = create_response.json()
        client_id = created_client.get('id')
        assert client_id, "Client ID not returned"
        
        # Verify client exists
        get_response = self.session.get(f"{BASE_URL}/api/clients/{client_id}")
        assert get_response.status_code == 200, f"Failed to get client: {get_response.text}"
        
        # Delete the client
        delete_response = self.session.delete(f"{BASE_URL}/api/clients/{client_id}")
        assert delete_response.status_code == 200, f"Failed to delete client: {delete_response.text}"
        
        # Verify client is deleted
        verify_response = self.session.get(f"{BASE_URL}/api/clients/{client_id}")
        assert verify_response.status_code == 404, f"Client should be deleted but got: {verify_response.status_code}"
    
    def test_get_all_clients(self):
        """Test getting all clients"""
        response = self.session.get(f"{BASE_URL}/api/clients")
        assert response.status_code == 200, f"Failed to get clients: {response.text}"
        clients = response.json()
        assert isinstance(clients, list), "Expected list of clients"


class TestAuthentication:
    """Test authentication with MARIO/MARIO credentials"""
    
    def test_login_with_mario_credentials(self):
        """Test login with MARIO/MARIO"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get('success') == True, "Login should return success=true"
        assert 'user' in data, "Response should contain user"
        assert 'tokens' in data, "Response should contain tokens"
        
        # Verify user data
        user = data['user']
        assert user.get('username') == 'MARIO', f"Expected username MARIO, got {user.get('username')}"
        assert user.get('isAdmin') == True, "MARIO should be admin"
        
        # Verify tokens
        tokens = data['tokens']
        assert 'access_token' in tokens, "Should have access_token"
        assert 'refresh_token' in tokens, "Should have refresh_token"
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "INVALID",
            "password": "INVALID"
        })
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"


class TestProductsAPI:
    """Test products API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data['tokens']['access_token']
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_products_montada(self):
        """Test getting products with module=montada"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        assert len(products) > 0
        
        # Verify product structure
        first_product = products[0]
        assert 'id' in first_product
        assert 'code' in first_product
        assert 'name' in first_product
        assert 'category' in first_product
        assert 'module' in first_product
    
    def test_all_categories_present(self):
        """Test that all expected categories are present"""
        response = self.session.get(f"{BASE_URL}/api/products?module=montada")
        assert response.status_code == 200
        products = response.json()
        
        categories = set(p.get('category', '') for p in products)
        
        expected_categories = [
            'ALTOS', 'BAJOS', 'COLUMNAS', 'SEMICOLUMNAS', 'PUERTAS',
            'COSTADOS', 'REGLETAS', 'ZOCALOS', 'CORNISAS', 'ESTANTES', 'VITRINAS'
        ]
        
        for cat in expected_categories:
            assert cat in categories, f"Category {cat} not found in products"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
