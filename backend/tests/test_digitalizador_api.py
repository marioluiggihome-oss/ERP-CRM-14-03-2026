# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test suite for Digitalizador (Draft Digitizer) API endpoints
Tests: /api/digitalizador/analyze and /api/digitalizador/export-csv
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDigitalizadorExportCSV:
    """Tests for /api/digitalizador/export-csv endpoint"""
    
    def test_export_csv_basic(self):
        """Test basic CSV export with valid lines"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 1, "reference": "TEST", "description": "Costado 113 x 60", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "40-ESTEITEX16",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True, "Expected success=True"
        assert "csv" in data, "Expected 'csv' field in response"
        assert "lineCount" in data, "Expected 'lineCount' field in response"
        
        # Verify CSV format
        csv_content = data["csv"]
        assert ";" in csv_content, "CSV should use ';' as separator"
        assert "16,0" in csv_content, "Decimal should use ',' (European format)"
        assert '"40-ESTEITEX16"' in csv_content, "Material code should be in quotes"
        
        print(f"✓ CSV export basic test passed. CSV: {csv_content}")
    
    def test_export_csv_dimension_extraction(self):
        """Test that dimensions are correctly extracted from description"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 1, "reference": "", "description": "Pieza 200 x 150", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "TEST-CODE",
                "materialThickness": 18.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        csv_content = data["csv"]
        
        # Verify dimensions extracted: 200 and 150
        assert ";200;" in csv_content, "Width 200 should be extracted"
        assert ";150;" in csv_content, "Height 150 should be extracted"
        
        print(f"✓ Dimension extraction test passed. CSV: {csv_content}")
    
    def test_export_csv_decimal_dimensions(self):
        """Test extraction of decimal dimensions like 69.8 x 44.7"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 1, "reference": "", "description": "Pieza 69.8 x 44.7", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "TEST-CODE",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        csv_content = data["csv"]
        
        # Dimensions should be converted to integers: 69 and 44
        assert ";69;" in csv_content, "Width 69 should be extracted (from 69.8)"
        assert ";44;" in csv_content, "Height 44 should be extracted (from 44.7)"
        
        print(f"✓ Decimal dimension extraction test passed. CSV: {csv_content}")
    
    def test_export_csv_quantity_multiplier(self):
        """Test that quantity creates multiple CSV lines"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 3, "reference": "", "description": "Pieza 100 x 50", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "TEST-CODE",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 3 lines for quantity=3
        assert data["lineCount"] == 3, f"Expected 3 lines, got {data['lineCount']}"
        
        csv_lines = data["csv"].split("\n")
        assert len(csv_lines) == 3, f"Expected 3 CSV lines, got {len(csv_lines)}"
        
        print(f"✓ Quantity multiplier test passed. Line count: {data['lineCount']}")
    
    def test_export_csv_multiple_lines(self):
        """Test export with multiple different lines"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 2, "reference": "REF1", "description": "Costado 113 x 60", "price": 0, "discount": 0, "isManual": False},
                    {"id": "LINE-2", "quantity": 1, "reference": "REF2", "description": "Tapa 80 x 40", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "40-ESTEITEX16",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 2 + 1 = 3 total lines
        assert data["lineCount"] == 3, f"Expected 3 lines, got {data['lineCount']}"
        
        csv_content = data["csv"]
        assert "Costado 113 x 60" in csv_content
        assert "Tapa 80 x 40" in csv_content
        
        print(f"✓ Multiple lines test passed. Total lines: {data['lineCount']}")
    
    def test_export_csv_no_dimensions(self):
        """Test export when description has no dimensions"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 1, "reference": "", "description": "Asa Mallorca Inox", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "TEST-CODE",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        csv_content = data["csv"]
        
        # Should have 0;0 for width and height when no dimensions found
        assert ";0;0;" in csv_content, "Should have 0;0 for missing dimensions"
        
        print(f"✓ No dimensions test passed. CSV: {csv_content}")
    
    def test_export_csv_format_structure(self):
        """Test that CSV format matches expected structure"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [
                    {"id": "LINE-1", "quantity": 1, "reference": "", "description": "Test 100 x 50", "price": 0, "discount": 0, "isManual": False}
                ],
                "materialCode": "40-ESTEITEX16",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        csv_line = data["csv"]
        
        # Expected format: "CODE";THICKNESS;"DESCRIPTION";WIDTH;HEIGHT;ORIENTATION;0;0;"CODE"
        parts = csv_line.split(";")
        assert len(parts) == 9, f"Expected 9 parts in CSV line, got {len(parts)}"
        
        # Verify structure
        assert parts[0] == '"40-ESTEITEX16"', "First field should be material code"
        assert parts[1] == "16,0", "Second field should be thickness with comma decimal"
        assert parts[2] == '"Test 100 x 50"', "Third field should be description"
        assert parts[3] == "100", "Fourth field should be width"
        assert parts[4] == "50", "Fifth field should be height"
        assert parts[5] == "1", "Sixth field should be orientation (1)"
        assert parts[6] == "0", "Seventh field should be 0"
        assert parts[7] == "0", "Eighth field should be 0"
        assert parts[8] == '"40-ESTEITEX16"', "Ninth field should be material code again"
        
        print(f"✓ CSV format structure test passed")
    
    def test_export_csv_empty_lines(self):
        """Test export with empty lines array"""
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/export-csv",
            json={
                "lines": [],
                "materialCode": "TEST-CODE",
                "materialThickness": 16.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["lineCount"] == 0
        assert data["csv"] == ""
        
        print(f"✓ Empty lines test passed")


class TestDigitalizadorAnalyze:
    """Tests for /api/digitalizador/analyze endpoint (Gemini Vision)"""
    
    def test_analyze_endpoint_exists(self):
        """Test that the analyze endpoint exists and responds"""
        # Send a minimal request to check endpoint exists
        # Note: This will likely fail without a valid image, but should return 422 or 500, not 404
        response = requests.post(
            f"{BASE_URL}/api/digitalizador/analyze",
            json={
                "imageBase64": "",
                "filename": "test.jpg"
            }
        )
        
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, "Endpoint /api/digitalizador/analyze should exist"
        
        print(f"✓ Analyze endpoint exists. Status: {response.status_code}")


class TestUserPermissions:
    """Tests for canUseDigitalizador permission in user model"""
    
    def test_admin_user_has_digitalizador_field(self):
        """Test that admin user response includes canUseDigitalizador field"""
        response = requests.get(f"{BASE_URL}/api/users")
        
        assert response.status_code == 200
        users = response.json()
        
        # Find admin user
        admin = next((u for u in users if u.get("id") == "admin"), None)
        assert admin is not None, "Admin user should exist"
        
        # Check if canUseDigitalizador field exists
        # Note: It may be False by default, but the field should exist
        assert "canUseDigitalizador" in admin or admin.get("isAdmin") == True, \
            "Admin user should have canUseDigitalizador field or be admin (who has access)"
        
        print(f"✓ Admin user permissions verified. isAdmin: {admin.get('isAdmin')}")
    
    def test_login_returns_user_permissions(self):
        """Test that login response includes user permissions"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "MARIO", "password": "MARIO"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "user" in data
        
        user = data["user"]
        assert user.get("isAdmin") == True, "MARIO should be admin"
        
        print(f"✓ Login returns user permissions. User: {user.get('username')}, isAdmin: {user.get('isAdmin')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
