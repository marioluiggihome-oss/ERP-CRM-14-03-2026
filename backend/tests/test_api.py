"""
Backend API Tests for LUIGGI HOME ERP/CRM
Tests: Health check, status endpoints, and AI product analysis
"""
import pytest
import requests
import os
from io import BytesIO
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndStatus:
    """Test basic API health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root API endpoint returns Hello World"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello World"
    
    def test_status_post(self):
        """Test creating a status check"""
        response = requests.post(
            f"{BASE_URL}/api/status",
            json={"client_name": "TEST_CLIENT"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["client_name"] == "TEST_CLIENT"
        assert "timestamp" in data
    
    def test_status_get(self):
        """Test retrieving status checks"""
        response = requests.get(f"{BASE_URL}/api/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAnalyzeProductSheets:
    """Test AI product analysis endpoint"""
    
    def create_test_image(self):
        """Create a simple test image"""
        img = Image.new('RGB', (200, 200), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    def test_analyze_endpoint_exists(self):
        """Test that the analyze endpoint exists and accepts POST"""
        # Create test image
        img_buffer = self.create_test_image()
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-product-sheets",
            data={"module": "montada"},
            files={"files": ("test.png", img_buffer, "image/png")}
        )
        
        # Should return 200 (success) or error from AI processing
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        if data["success"]:
            assert "products" in data
            assert "count" in data
    
    def test_analyze_montada_module(self):
        """Test analysis with montada module"""
        img_buffer = self.create_test_image()
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-product-sheets",
            data={"module": "montada"},
            files={"files": ("product_sheet.png", img_buffer, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"] and data.get("products"):
            product = data["products"][0]
            # Check product has expected fields
            assert "id" in product
            assert "manufacturer" in product
            assert product["manufacturer"] == "Luiggi Home Master"
            assert "importedAt" in product
            assert "originalFilename" in product
    
    def test_analyze_despiece_module(self):
        """Test analysis with despiece module"""
        img_buffer = self.create_test_image()
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-product-sheets",
            data={"module": "despiece"},
            files={"files": ("product_sheet.png", img_buffer, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_analyze_multiple_files(self):
        """Test analysis with multiple files"""
        img_buffer1 = self.create_test_image()
        img_buffer2 = self.create_test_image()
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-product-sheets",
            data={"module": "montada"},
            files=[
                ("files", ("test1.png", img_buffer1, "image/png")),
                ("files", ("test2.png", img_buffer2, "image/png"))
            ]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            assert data["count"] == 2


class TestErrorHandling:
    """Test API error handling"""
    
    def test_invalid_endpoint(self):
        """Test 404 for invalid endpoint"""
        response = requests.get(f"{BASE_URL}/api/nonexistent")
        assert response.status_code == 404
    
    def test_analyze_missing_module(self):
        """Test analyze endpoint without module parameter"""
        img = Image.new('RGB', (100, 100), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-product-sheets",
            files={"files": ("test.png", buffer, "image/png")}
        )
        
        # Should return 422 (validation error) for missing required field
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
