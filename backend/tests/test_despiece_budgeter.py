"""
Test suite for DESPIECE Budgeter module
Tests: Products API, Filters, Budgets CRUD, ALVIC seed data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://kitchen-erp-staging.preview.emergentagent.com')


class TestDespieceBudgeterProducts:
    """Tests for DESPIECE products endpoints"""
    
    def test_get_products_list(self):
        """Test getting list of DESPIECE products"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have ALVIC products seeded"
        
        # Verify product structure
        product = data[0]
        assert "id" in product
        assert "code" in product
        assert "name" in product
        assert "manufacturer" in product
        assert "priceZ1" in product
    
    def test_get_products_with_manufacturer_filter(self):
        """Test filtering products by manufacturer"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?manufacturer=ALVIC")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        for product in data:
            assert product["manufacturer"].upper() == "ALVIC"
    
    def test_get_products_with_collection_filter(self):
        """Test filtering products by collection"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?collection=LUXE")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        for product in data:
            assert "LUXE" in product["collection"].upper()
    
    def test_get_products_with_finish_filter(self):
        """Test filtering products by finish"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?finish=Brillo")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        for product in data:
            assert "brillo" in product["finish"].lower()
    
    def test_get_products_with_thickness_filter(self):
        """Test filtering products by thickness"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?thickness=18")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        for product in data:
            assert product["thickness"] == 18
    
    def test_get_products_with_search(self):
        """Test searching products by code or name"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?search=LUXE")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0
        for product in data:
            assert "LUXE" in product["code"].upper() or "LUXE" in product["name"].upper() or "LUXE" in product.get("collection", "").upper()


class TestDespieceBudgeterFilters:
    """Tests for DESPIECE filter options endpoint"""
    
    def test_get_filter_options(self):
        """Test getting available filter options"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products/filters")
        assert response.status_code == 200
        
        data = response.json()
        assert "manufacturers" in data
        assert "collections" in data
        assert "finishes" in data
        assert "thicknesses" in data
        assert "colors" in data
        
        # Verify ALVIC is in manufacturers
        assert "ALVIC" in data["manufacturers"]
        
        # Verify collections exist
        assert len(data["collections"]) > 0
        assert "LUXE" in data["collections"]
        assert "ZENIT" in data["collections"]
        
        # Verify finishes exist
        assert len(data["finishes"]) > 0


class TestDespieceBudgeterBudgets:
    """Tests for DESPIECE budgets CRUD"""
    
    def test_create_budget(self):
        """Test creating a new DESPIECE budget"""
        budget_data = {
            "budgetNumber": "TEST-DESP-001",
            "customerName": "Test Customer",
            "customerAddress": "Test Address 123",
            "projectRef": "REF-TEST-001",
            "manufacturer": "ALVIC",
            "collection": "LUXE",
            "items": [
                {
                    "productId": "desp-cf7f168c",
                    "productCode": "LUXE-BL-001",
                    "productName": "LUXE Blanco Brillo",
                    "manufacturer": "ALVIC",
                    "color": "Blanco",
                    "finish": "Brillo",
                    "thickness": 18,
                    "width": 600,
                    "height": 800,
                    "quantity": 2,
                    "areaM2": 0.48,
                    "unitPrice": 41.04,
                    "totalPrice": 82.08
                }
            ],
            "totalArea": 0.96,
            "totalPrice": 82.08,
            "userId": "admin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/despiece-budgeter/budgets",
            json=budget_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["budgetNumber"] == "TEST-DESP-001"
        assert data["customerName"] == "Test Customer"
        assert len(data["items"]) == 1
        
        # Store budget ID for cleanup
        return data["id"]
    
    def test_get_budgets_list(self):
        """Test getting list of DESPIECE budgets"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/budgets")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_budget_by_id(self):
        """Test getting a specific budget by ID"""
        # First create a budget
        budget_data = {
            "budgetNumber": "TEST-DESP-002",
            "customerName": "Test Customer 2",
            "items": [],
            "totalArea": 0,
            "totalPrice": 0
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/despiece-budgeter/budgets",
            json=budget_data
        )
        assert create_response.status_code == 200
        budget_id = create_response.json()["id"]
        
        # Get the budget
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/budgets/{budget_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == budget_id
        assert data["budgetNumber"] == "TEST-DESP-002"
    
    def test_update_budget(self):
        """Test updating a DESPIECE budget"""
        # First create a budget
        budget_data = {
            "budgetNumber": "TEST-DESP-003",
            "customerName": "Original Name",
            "items": [],
            "totalArea": 0,
            "totalPrice": 0
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/despiece-budgeter/budgets",
            json=budget_data
        )
        assert create_response.status_code == 200
        budget_id = create_response.json()["id"]
        
        # Update the budget
        update_data = {
            "customerName": "Updated Name",
            "totalPrice": 100.50
        }
        
        response = requests.put(
            f"{BASE_URL}/api/despiece-budgeter/budgets/{budget_id}",
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["customerName"] == "Updated Name"
        assert data["totalPrice"] == 100.50
    
    def test_delete_budget(self):
        """Test deleting a DESPIECE budget"""
        # First create a budget
        budget_data = {
            "budgetNumber": "TEST-DESP-DELETE",
            "customerName": "To Delete",
            "items": [],
            "totalArea": 0,
            "totalPrice": 0
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/despiece-budgeter/budgets",
            json=budget_data
        )
        assert create_response.status_code == 200
        budget_id = create_response.json()["id"]
        
        # Delete the budget
        response = requests.delete(f"{BASE_URL}/api/despiece-budgeter/budgets/{budget_id}")
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/despiece-budgeter/budgets/{budget_id}")
        assert get_response.status_code == 404


class TestDespieceBudgeterStats:
    """Tests for DESPIECE statistics endpoint"""
    
    def test_get_stats(self):
        """Test getting DESPIECE module statistics"""
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "totalProducts" in data
        assert "totalBudgets" in data
        assert "manufacturers" in data
        assert "collections" in data
        assert data["totalProducts"] > 0


class TestDespieceBudgeterSeed:
    """Tests for ALVIC seed data endpoint"""
    
    def test_seed_alvic_products(self):
        """Test seeding ALVIC sample products"""
        response = requests.post(f"{BASE_URL}/api/despiece-budgeter/seed-alvic")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "created" in data or "updated" in data
        assert data["total"] > 0


class TestDespieceBudgeterCalculations:
    """Tests for price calculations in DESPIECE budgeter"""
    
    def test_area_calculation(self):
        """Test that area is calculated correctly (width * height in m2)"""
        # Get a product
        response = requests.get(f"{BASE_URL}/api/despiece-budgeter/products?limit=1")
        assert response.status_code == 200
        
        products = response.json()
        assert len(products) > 0
        
        product = products[0]
        price_per_m2 = product["priceZ1"]
        
        # Calculate expected area for 600x800mm piece
        width_m = 600 / 1000  # 0.6m
        height_m = 800 / 1000  # 0.8m
        expected_area = width_m * height_m  # 0.48 m2
        expected_price = expected_area * price_per_m2
        
        assert expected_area == 0.48
        assert expected_price > 0


# Cleanup test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_budgets():
    """Cleanup test budgets after all tests"""
    yield
    # Delete test budgets
    response = requests.get(f"{BASE_URL}/api/despiece-budgeter/budgets")
    if response.status_code == 200:
        budgets = response.json()
        for budget in budgets:
            if budget.get("budgetNumber", "").startswith("TEST-DESP"):
                requests.delete(f"{BASE_URL}/api/despiece-budgeter/budgets/{budget['id']}")
