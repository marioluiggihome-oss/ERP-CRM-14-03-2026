# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test suite for bulk-upsert endpoint and Telemetría IA features.
Tests:
1. POST /api/products/bulk-upsert - create new products
2. POST /api/products/bulk-upsert - update existing products with different tariffs
3. Verify zonePoints merge correctly (T1, T2, T3 for MV)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://erp-home-kitchen.preview.emergentagent.com')

class TestBulkUpsert:
    """Tests for bulk-upsert endpoint to prevent product duplication"""
    
    def setup_method(self, method):
        """Setup test data with unique codes for each test method"""
        self.test_code_prefix = f"TEST-UPSERT-{uuid.uuid4().hex[:6]}"
        self.test_products = [
            {
                "code": f"{self.test_code_prefix}-001",
                "name": "Test Product 1",
                "category": "ALTOS",
                "series": "TEST",
                "width": 600,
                "height": 700,
                "depth": 350,
                "manufacturer": "MV",
                "module": "montada",
                "points": 100,
                "zonePoints": {"T1": 100}
            },
            {
                "code": f"{self.test_code_prefix}-002",
                "name": "Test Product 2",
                "category": "BAJOS",
                "series": "TEST",
                "width": 800,
                "height": 900,
                "depth": 600,
                "manufacturer": "MV",
                "module": "montada",
                "points": 150,
                "zonePoints": {"T1": 150}
            }
        ]
    
    def teardown_method(self, method):
        """Cleanup: delete test products after each test"""
        self._cleanup_test_products()
    
    def _cleanup_test_products(self):
        """Delete test products created during tests"""
        try:
            # Get all products and filter by test prefix
            response = requests.get(f"{BASE_URL}/api/products?library=MV")
            if response.status_code == 200:
                products = response.json()
                test_product_ids = [p['id'] for p in products if p.get('code', '').startswith(self.test_code_prefix)]
                if test_product_ids:
                    requests.delete(
                        f"{BASE_URL}/api/products/bulk/delete",
                        json=test_product_ids,
                        headers={"Content-Type": "application/json"}
                    )
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_bulk_upsert_create_new_products(self):
        """Test creating new products via bulk-upsert"""
        # Create products with T1 tariff
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": self.test_products,
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "created" in data, "Response should contain 'created' count"
        assert "updated" in data, "Response should contain 'updated' count"
        assert data["created"] == 2, f"Expected 2 created, got {data['created']}"
        assert data["updated"] == 0, f"Expected 0 updated, got {data['updated']}"
        assert data["tariff"] == "T1", f"Expected tariff T1, got {data['tariff']}"
        
        print(f"✅ Created {data['created']} new products with T1 tariff")
    
    def test_bulk_upsert_update_with_different_tariff(self):
        """Test updating existing products with T2 tariff - should merge zonePoints"""
        # First, create products with T1
        create_response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": self.test_products,
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 200
        
        # Now update same products with T2 tariff (different prices)
        updated_products = [
            {
                "code": self.test_products[0]["code"],
                "name": self.test_products[0]["name"],
                "points": 120,  # Different price for T2
                "zonePoints": {"T1": 120}  # Will be stored as T2
            },
            {
                "code": self.test_products[1]["code"],
                "name": self.test_products[1]["name"],
                "points": 180,  # Different price for T2
                "zonePoints": {"T1": 180}
            }
        ]
        
        update_response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": updated_products,
                "tariff": "T2",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        data = update_response.json()
        assert data["created"] == 0, f"Expected 0 created (products exist), got {data['created']}"
        assert data["updated"] == 2, f"Expected 2 updated, got {data['updated']}"
        assert data["tariff"] == "T2", f"Expected tariff T2, got {data['tariff']}"
        
        print(f"✅ Updated {data['updated']} products with T2 tariff")
    
    def test_bulk_upsert_verify_zonepoints_merge(self):
        """Test that zonePoints are merged correctly with multiple tariffs"""
        # Create with T1
        requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [self.test_products[0]],
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Update with T2
        requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [{
                    "code": self.test_products[0]["code"],
                    "name": self.test_products[0]["name"],
                    "points": 120,
                    "zonePoints": {"T1": 120}
                }],
                "tariff": "T2",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Update with T3
        requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [{
                    "code": self.test_products[0]["code"],
                    "name": self.test_products[0]["name"],
                    "points": 140,
                    "zonePoints": {"T1": 140}
                }],
                "tariff": "T3",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Verify the product has all three tariffs in zonePoints
        response = requests.get(f"{BASE_URL}/api/products?library=MV")
        assert response.status_code == 200
        
        products = response.json()
        # Backend converts codes to uppercase
        expected_code = self.test_products[0]["code"].upper()
        test_product = next((p for p in products if p.get('code') == expected_code), None)
        
        assert test_product is not None, f"Test product {expected_code} not found"
        
        zone_points = test_product.get('zonePoints', {})
        assert "T1" in zone_points, f"T1 should be in zonePoints: {zone_points}"
        assert "T2" in zone_points, f"T2 should be in zonePoints: {zone_points}"
        assert "T3" in zone_points, f"T3 should be in zonePoints: {zone_points}"
        
        assert zone_points["T1"] == 100, f"T1 should be 100, got {zone_points['T1']}"
        assert zone_points["T2"] == 120, f"T2 should be 120, got {zone_points['T2']}"
        assert zone_points["T3"] == 140, f"T3 should be 140, got {zone_points['T3']}"
        
        print(f"✅ zonePoints correctly merged: {zone_points}")
    
    def test_bulk_upsert_no_duplicates(self):
        """Test that bulk-upsert doesn't create duplicate products"""
        # Create products
        requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": self.test_products,
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Try to create same products again with same tariff
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": self.test_products,
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should update, not create
        assert data["created"] == 0, f"Expected 0 created (no duplicates), got {data['created']}"
        assert data["updated"] == 2, f"Expected 2 updated, got {data['updated']}"
        
        # Verify no duplicates in database
        products_response = requests.get(f"{BASE_URL}/api/products?library=MV")
        products = products_response.json()
        
        # Count products with our test codes (backend converts to uppercase)
        test_codes = [p["code"].upper() for p in self.test_products]
        matching_products = [p for p in products if p.get('code') in test_codes]
        
        assert len(matching_products) == 2, f"Expected 2 products (no duplicates), found {len(matching_products)}"
        
        print(f"✅ No duplicates created - {len(matching_products)} unique products")
    
    def test_bulk_upsert_zc_library(self):
        """Test bulk-upsert with ZC library and Z1-Z12 zones"""
        zc_products = [
            {
                "code": f"{self.test_code_prefix}-ZC-001",
                "name": "Test ZC Product",
                "category": "ALTOS",
                "series": "TEST",
                "width": 600,
                "height": 700,
                "depth": 350,
                "manufacturer": "Zona Cocinas",
                "module": "montada",
                "points": 50,
                "zonePoints": {"Z1": 50}
            }
        ]
        
        # Create with Z1
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": zc_products,
                "tariff": "Z1",
                "library": "ZC"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 1
        assert data["tariff"] == "Z1"
        
        # Update with Z2
        zc_products[0]["points"] = 55
        zc_products[0]["zonePoints"] = {"Z1": 55}
        
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": zc_products,
                "tariff": "Z2",
                "library": "ZC"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 1
        assert data["tariff"] == "Z2"
        
        # Cleanup ZC test product
        try:
            products_response = requests.get(f"{BASE_URL}/api/products?library=ZC")
            if products_response.status_code == 200:
                products = products_response.json()
                zc_test_ids = [p['id'] for p in products if p.get('code', '').startswith(f"{self.test_code_prefix}-ZC")]
                if zc_test_ids:
                    requests.delete(
                        f"{BASE_URL}/api/products/bulk/delete",
                        json=zc_test_ids,
                        headers={"Content-Type": "application/json"}
                    )
        except:
            pass
        
        print(f"✅ ZC library bulk-upsert working correctly")


class TestBulkUpsertErrorHandling:
    """Test error handling in bulk-upsert endpoint"""
    
    def test_empty_products_list(self):
        """Test bulk-upsert with empty products list"""
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [],
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 0
        assert data["updated"] == 0
        
        print("✅ Empty products list handled correctly")
    
    def test_product_without_code(self):
        """Test bulk-upsert with product missing code"""
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [{"name": "No Code Product", "points": 100}],
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 0
        assert len(data.get("errors", [])) > 0
        
        print("✅ Product without code handled correctly")


class TestApiJsBulkUpsert:
    """Test that api.js bulkUpsert method handles responses correctly"""
    
    def test_api_endpoint_returns_valid_json(self):
        """Verify the endpoint returns valid JSON (no body stream issues)"""
        test_code = f"TEST-API-{uuid.uuid4().hex[:6]}"
        
        response = requests.post(
            f"{BASE_URL}/api/products/bulk-upsert",
            json={
                "products": [{
                    "code": test_code,
                    "name": "API Test Product",
                    "points": 100,
                    "zonePoints": {"T1": 100}
                }],
                "tariff": "T1",
                "library": "MV"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Verify response is valid JSON
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/json')
        
        # Verify we can parse the response
        data = response.json()
        assert isinstance(data, dict)
        assert "created" in data
        assert "updated" in data
        
        # Cleanup
        try:
            products_response = requests.get(f"{BASE_URL}/api/products?library=MV")
            if products_response.status_code == 200:
                products = products_response.json()
                test_ids = [p['id'] for p in products if p.get('code') == test_code]
                if test_ids:
                    requests.delete(
                        f"{BASE_URL}/api/products/bulk/delete",
                        json=test_ids,
                        headers={"Content-Type": "application/json"}
                    )
        except:
            pass
        
        print("✅ API returns valid JSON response (no body stream issues)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
