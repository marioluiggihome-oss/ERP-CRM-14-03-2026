# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test P1 and P2 Features:
- P1: Business type filtering (cocina/armarios) in CRM Pipeline
- P1: businessType field in opportunities
- P1: Create opportunity from armario project
- P2: Admin metrics trends endpoint
- P2: Monthly trends data for charts
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP1BusinessTypeFiltering:
    """P1: Test business type filtering in CRM opportunities"""
    
    def test_get_opportunities_without_filter(self):
        """Test getting all opportunities without businessType filter"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/opportunities returns {len(data)} opportunities")
    
    def test_get_opportunities_filter_cocina(self):
        """Test filtering opportunities by businessType=cocina"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities?businessType=cocina")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned opportunities have businessType=cocina
        for opp in data:
            assert opp.get("businessType") == "cocina", f"Expected cocina, got {opp.get('businessType')}"
        print(f"✓ GET /api/crm/opportunities?businessType=cocina returns {len(data)} cocina opportunities")
    
    def test_get_opportunities_filter_armarios(self):
        """Test filtering opportunities by businessType=armarios"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities?businessType=armarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned opportunities have businessType=armarios
        for opp in data:
            assert opp.get("businessType") == "armarios", f"Expected armarios, got {opp.get('businessType')}"
        print(f"✓ GET /api/crm/opportunities?businessType=armarios returns {len(data)} armarios opportunities")


class TestP1OpportunityBusinessType:
    """P1: Test businessType field in opportunities"""
    
    @pytest.fixture
    def test_contact(self):
        """Create a test contact for opportunities"""
        contact_data = {
            "name": "TEST_P1_Contact",
            "email": "test_p1@example.com",
            "phone": "123456789",
            "company": "Test Company P1"
        }
        response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert response.status_code == 200
        contact = response.json()
        yield contact
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")
    
    def test_create_opportunity_with_cocina_type(self, test_contact):
        """Test creating opportunity with businessType=cocina"""
        opp_data = {
            "title": "TEST_P1_Cocina_Opportunity",
            "contactId": test_contact["id"],
            "contactName": test_contact["name"],
            "value": 5000,
            "businessType": "cocina"
        }
        response = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        assert response.status_code == 200
        opp = response.json()
        assert opp["businessType"] == "cocina"
        print(f"✓ Created opportunity with businessType=cocina: {opp['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
    
    def test_create_opportunity_with_armarios_type(self, test_contact):
        """Test creating opportunity with businessType=armarios"""
        opp_data = {
            "title": "TEST_P1_Armarios_Opportunity",
            "contactId": test_contact["id"],
            "contactName": test_contact["name"],
            "value": 3000,
            "businessType": "armarios"
        }
        response = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        assert response.status_code == 200
        opp = response.json()
        assert opp["businessType"] == "armarios"
        print(f"✓ Created opportunity with businessType=armarios: {opp['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
    
    def test_default_business_type_is_cocina(self, test_contact):
        """Test that default businessType is cocina when not specified"""
        opp_data = {
            "title": "TEST_P1_Default_Type_Opportunity",
            "contactId": test_contact["id"],
            "contactName": test_contact["name"],
            "value": 2000
            # businessType not specified
        }
        response = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        assert response.status_code == 200
        opp = response.json()
        assert opp["businessType"] == "cocina", f"Expected default cocina, got {opp.get('businessType')}"
        print(f"✓ Default businessType is cocina: {opp['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")


class TestP1CreateFromArmario:
    """P1: Test creating opportunity from armario project"""
    
    @pytest.fixture
    def test_armario_project(self):
        """Create a test armario project"""
        project_data = {
            "name": "TEST_P1_Armario_Project",
            "customerName": "TEST_P1_Armario_Customer",
            "width": 300,
            "height": 250,
            "depth": 60,
            "modules": 3,
            "doorType": "correderas",
            "totalPrice": 4500
        }
        response = requests.post(f"{BASE_URL}/api/armarios/projects", json=project_data)
        if response.status_code == 200:
            data = response.json()
            # Response structure is {"success": true, "project": {...}}
            project = data.get("project", data)
            yield project
            # Cleanup
            requests.delete(f"{BASE_URL}/api/armarios/projects/{project['id']}")
        else:
            # If creation fails, yield None
            print(f"Warning: Could not create armario project: {response.text}")
            yield None
    
    def test_create_opportunity_from_armario(self, test_armario_project):
        """Test POST /api/crm/opportunities/from-armario/{project_id}"""
        if test_armario_project is None:
            pytest.skip("Armario project creation failed")
        
        project_id = test_armario_project["id"]
        response = requests.post(f"{BASE_URL}/api/crm/opportunities/from-armario/{project_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "opportunity" in data
        assert "contact" in data
        assert "message" in data
        
        opp = data["opportunity"]
        assert opp["businessType"] == "armarios", f"Expected armarios, got {opp.get('businessType')}"
        assert "Armarios" in opp["title"]
        assert opp["linkedProjectId"] == project_id
        
        print(f"✓ Created opportunity from armario: {opp['id']} with businessType=armarios")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
        if data.get("contact"):
            requests.delete(f"{BASE_URL}/api/crm/contacts/{data['contact']['id']}")


class TestP2AdminMetricsTrends:
    """P2: Test admin metrics trends endpoint"""
    
    def test_get_trends_endpoint_exists(self):
        """Test GET /api/admin/metrics/trends returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert response.status_code == 200
        print("✓ GET /api/admin/metrics/trends returns 200")
    
    def test_trends_response_structure(self):
        """Test trends response has required structure"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "monthly" in data, "Missing 'monthly' field"
        assert "funnel" in data, "Missing 'funnel' field"
        assert "byBusinessType" in data, "Missing 'byBusinessType' field"
        
        print(f"✓ Trends response has required structure: monthly, funnel, byBusinessType")
    
    def test_monthly_trends_data(self):
        """Test monthly trends data structure"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert response.status_code == 200
        data = response.json()
        
        monthly = data.get("monthly", [])
        assert isinstance(monthly, list)
        
        if len(monthly) > 0:
            # Verify monthly data structure
            sample = monthly[0]
            expected_fields = ["month", "monthLabel", "won", "wonValue", "lost", "lostValue", 
                             "created", "createdValue", "cocina", "cocinaValue", "armarios", "armariosValue"]
            for field in expected_fields:
                assert field in sample, f"Missing field '{field}' in monthly data"
            
            print(f"✓ Monthly trends has {len(monthly)} months with correct structure")
        else:
            print("✓ Monthly trends is empty (no data yet)")
    
    def test_funnel_data(self):
        """Test funnel data structure"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert response.status_code == 200
        data = response.json()
        
        funnel = data.get("funnel", [])
        assert isinstance(funnel, list)
        
        # Verify funnel stages
        expected_stages = ["lead", "contacted", "proposal", "negotiation"]
        stage_ids = [f["stage"] for f in funnel]
        
        for stage in expected_stages:
            assert stage in stage_ids, f"Missing stage '{stage}' in funnel"
        
        # Verify funnel item structure
        for item in funnel:
            assert "stage" in item
            assert "name" in item
            assert "count" in item
            assert "value" in item
        
        print(f"✓ Funnel data has {len(funnel)} stages with correct structure")
    
    def test_business_type_distribution(self):
        """Test business type distribution data"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert response.status_code == 200
        data = response.json()
        
        by_type = data.get("byBusinessType", {})
        
        # Verify cocina and armarios exist
        assert "cocina" in by_type, "Missing 'cocina' in byBusinessType"
        assert "armarios" in by_type, "Missing 'armarios' in byBusinessType"
        
        # Verify structure
        for bt in ["cocina", "armarios"]:
            assert "count" in by_type[bt], f"Missing 'count' in {bt}"
            assert "value" in by_type[bt], f"Missing 'value' in {bt}"
            assert "won" in by_type[bt], f"Missing 'won' in {bt}"
            assert "wonValue" in by_type[bt], f"Missing 'wonValue' in {bt}"
        
        print(f"✓ Business type distribution: cocina={by_type['cocina']['count']}, armarios={by_type['armarios']['count']}")


class TestP2AdminMetricsBase:
    """P2: Test base admin metrics endpoint"""
    
    def test_get_metrics_endpoint(self):
        """Test GET /api/admin/metrics returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 200
        print("✓ GET /api/admin/metrics returns 200")
    
    def test_metrics_response_structure(self):
        """Test metrics response has required structure"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "global" in data, "Missing 'global' field"
        assert "byUser" in data, "Missing 'byUser' field"
        assert "topPerformers" in data, "Missing 'topPerformers' field"
        
        print("✓ Metrics response has required structure")
    
    def test_global_metrics_fields(self):
        """Test global metrics has required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/metrics")
        assert response.status_code == 200
        data = response.json()
        
        global_metrics = data.get("global", {})
        expected_fields = [
            "totalValue", "pipelineValue", "conversionRate", 
            "totalOpportunities", "wonOpportunities", "activeOpportunities",
            "totalContacts", "totalProjects"
        ]
        
        for field in expected_fields:
            assert field in global_metrics, f"Missing field '{field}' in global metrics"
        
        print(f"✓ Global metrics has all required fields")


class TestIntegrationP1P2:
    """Integration tests for P1 and P2 features"""
    
    def test_create_opportunities_and_verify_trends(self):
        """Create opportunities with different businessTypes and verify trends"""
        # First, create a contact
        contact_data = {
            "name": "TEST_Integration_Contact",
            "email": "test_integration@example.com"
        }
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert contact_resp.status_code == 200
        contact = contact_resp.json()
        
        # Create cocina opportunity
        cocina_opp = {
            "title": "TEST_Integration_Cocina",
            "contactId": contact["id"],
            "value": 10000,
            "businessType": "cocina",
            "stage": "won"
        }
        cocina_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json=cocina_opp)
        assert cocina_resp.status_code == 200
        cocina = cocina_resp.json()
        
        # Create armarios opportunity
        armarios_opp = {
            "title": "TEST_Integration_Armarios",
            "contactId": contact["id"],
            "value": 5000,
            "businessType": "armarios",
            "stage": "proposal"
        }
        armarios_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json=armarios_opp)
        assert armarios_resp.status_code == 200
        armarios = armarios_resp.json()
        
        # Verify trends include both types
        trends_resp = requests.get(f"{BASE_URL}/api/admin/metrics/trends")
        assert trends_resp.status_code == 200
        trends = trends_resp.json()
        
        by_type = trends.get("byBusinessType", {})
        assert by_type.get("cocina", {}).get("count", 0) >= 1
        assert by_type.get("armarios", {}).get("count", 0) >= 1
        
        print("✓ Integration test: Created opportunities and verified trends")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{cocina['id']}")
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{armarios['id']}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
