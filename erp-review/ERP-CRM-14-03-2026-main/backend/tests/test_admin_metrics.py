"""
Test suite for Admin Metrics API - Director Comercial Panel
Tests the GET /api/admin/metrics endpoint for metrics dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminMetricsAPI:
    """Tests for /api/admin/metrics endpoint"""
    
    def test_admin_metrics_endpoint_returns_200(self):
        """Test that admin metrics endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Admin metrics endpoint returns 200 OK")
    
    def test_admin_metrics_has_global_section(self):
        """Test that response contains global metrics section"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        assert "global" in data, "Response missing 'global' section"
        global_metrics = data["global"]
        
        # Verify all required global fields
        required_fields = [
            "totalUsers", "totalDirectores", "totalResponsables", 
            "totalComerciales", "totalTiendas", "totalColaboradores",
            "totalOpportunities", "wonOpportunities", "activeOpportunities",
            "totalValue", "pipelineValue", "totalProjects", "totalContacts",
            "conversionRate"
        ]
        
        for field in required_fields:
            assert field in global_metrics, f"Global metrics missing field: {field}"
        
        print(f"✓ Global metrics contains all {len(required_fields)} required fields")
    
    def test_admin_metrics_has_by_user_array(self):
        """Test that response contains byUser array with user metrics"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        assert "byUser" in data, "Response missing 'byUser' section"
        assert isinstance(data["byUser"], list), "byUser should be a list"
        
        # If there are users, verify structure
        if len(data["byUser"]) > 0:
            user_metrics = data["byUser"][0]
            required_user_fields = [
                "userId", "userName", "role", "totalOpportunities",
                "wonOpportunities", "activeOpportunities", "totalValue",
                "pipelineValue", "conversionRate", "totalContacts",
                "totalShops", "totalProjects", "shops"
            ]
            
            for field in required_user_fields:
                assert field in user_metrics, f"User metrics missing field: {field}"
            
            print(f"✓ byUser array contains users with all {len(required_user_fields)} required fields")
        else:
            print("✓ byUser array is empty (no comerciales/responsables)")
    
    def test_admin_metrics_has_top_performers(self):
        """Test that response contains topPerformers array"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        assert "topPerformers" in data, "Response missing 'topPerformers' section"
        assert isinstance(data["topPerformers"], list), "topPerformers should be a list"
        
        # Top performers should be limited to 10
        assert len(data["topPerformers"]) <= 10, "topPerformers should have max 10 entries"
        
        print(f"✓ topPerformers array present with {len(data['topPerformers'])} entries")
    
    def test_admin_metrics_has_role_breakdown(self):
        """Test that response contains roleBreakdown section"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        assert "roleBreakdown" in data, "Response missing 'roleBreakdown' section"
        role_breakdown = data["roleBreakdown"]
        
        required_roles = ["directores", "responsables", "comerciales", "tiendas", "colaboradores"]
        for role in required_roles:
            assert role in role_breakdown, f"roleBreakdown missing: {role}"
        
        print(f"✓ roleBreakdown contains all {len(required_roles)} role counts")
    
    def test_admin_metrics_values_are_numeric(self):
        """Test that numeric fields contain valid numbers"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        global_metrics = data["global"]
        
        # Check numeric fields
        numeric_fields = [
            "totalUsers", "totalDirectores", "totalResponsables",
            "totalComerciales", "totalTiendas", "totalColaboradores",
            "totalOpportunities", "wonOpportunities", "activeOpportunities",
            "totalValue", "pipelineValue", "totalProjects", "totalContacts",
            "conversionRate"
        ]
        
        for field in numeric_fields:
            value = global_metrics[field]
            assert isinstance(value, (int, float)), f"{field} should be numeric, got {type(value)}"
            assert value >= 0, f"{field} should be non-negative, got {value}"
        
        print("✓ All global numeric fields contain valid non-negative numbers")
    
    def test_admin_metrics_conversion_rate_valid_range(self):
        """Test that conversion rate is between 0 and 100"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        global_rate = data["global"]["conversionRate"]
        assert 0 <= global_rate <= 100, f"Global conversion rate out of range: {global_rate}"
        
        # Check user conversion rates
        for user in data["byUser"]:
            user_rate = user["conversionRate"]
            assert 0 <= user_rate <= 100, f"User {user['userName']} conversion rate out of range: {user_rate}"
        
        print("✓ All conversion rates are within valid range (0-100)")
    
    def test_admin_metrics_user_roles_correct(self):
        """Test that user roles are correctly labeled"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        valid_roles = ["Comercial", "Resp. Delegación"]
        
        for user in data["byUser"]:
            assert user["role"] in valid_roles, f"Invalid role: {user['role']}"
        
        print(f"✓ All user roles are valid ({', '.join(valid_roles)})")
    
    def test_admin_metrics_shops_structure(self):
        """Test that shops array has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        data = response.json()
        
        for user in data["byUser"]:
            assert isinstance(user["shops"], list), f"shops should be a list for user {user['userName']}"
            
            for shop in user["shops"]:
                assert "id" in shop, "Shop missing 'id' field"
                assert "name" in shop, "Shop missing 'name' field"
        
        print("✓ All shops have correct structure (id, name)")


class TestAdminAllWorkAPI:
    """Tests for /api/admin/all-work endpoint (Trabajos tab)"""
    
    def test_admin_all_work_endpoint_returns_200(self):
        """Test that admin all-work endpoint returns 200 OK"""
        response = requests.get(f"{BASE_URL}/api/admin/all-work")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Admin all-work endpoint returns 200 OK")
    
    def test_admin_all_work_has_required_sections(self):
        """Test that response contains all required sections"""
        response = requests.get(f"{BASE_URL}/api/admin/all-work")
        data = response.json()
        
        required_sections = ["projects", "opportunities", "digitalizaciones", "users", "summary"]
        for section in required_sections:
            assert section in data, f"Response missing '{section}' section"
        
        print(f"✓ All-work response contains all {len(required_sections)} required sections")
    
    def test_admin_all_work_summary_structure(self):
        """Test that summary has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/all-work")
        data = response.json()
        
        summary = data["summary"]
        required_fields = ["totalProjects", "totalOpportunities", "totalDigitalizaciones", "totalUsers"]
        
        for field in required_fields:
            assert field in summary, f"Summary missing field: {field}"
            assert isinstance(summary[field], int), f"{field} should be integer"
        
        print("✓ Summary has correct structure with all required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
