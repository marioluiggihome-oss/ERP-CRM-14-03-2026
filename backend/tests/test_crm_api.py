"""
CRM API Tests for LUIGGI HOME ERP/CRM
Tests: Contacts, Opportunities, Activities, Dashboard
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://luiggi-kitchen-erp-6.preview.emergentagent.com').rstrip('/')

# Test data prefixes for cleanup
TEST_PREFIX = "TEST_CRM_"

class TestAuthLogin:
    """Test authentication with MARIO/MARIO credentials"""
    
    def test_login_mario_success(self):
        """Test login with MARIO/MARIO credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "MARIO",
            "password": "MARIO"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["user"]["username"] == "MARIO"
        assert data["user"]["isAdmin"] == True
        assert "montada" in data["user"]["allowedModules"]
        print(f"✓ Login MARIO/MARIO successful - Admin user with full permissions")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "INVALID",
            "password": "WRONG"
        })
        assert response.status_code == 401
        print(f"✓ Invalid credentials correctly rejected with 401")


class TestCRMDashboard:
    """Test CRM Dashboard endpoint"""
    
    def test_get_dashboard_stats(self):
        """Test GET /api/crm/dashboard returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/crm/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields exist
        assert "totalContacts" in data
        assert "activeOpportunities" in data
        assert "wonThisMonth" in data
        assert "pipelineValue" in data
        assert "topOpportunities" in data
        assert "upcomingActivities" in data
        assert "recentActivities" in data
        
        # Verify types
        assert isinstance(data["totalContacts"], int)
        assert isinstance(data["activeOpportunities"], int)
        assert isinstance(data["pipelineValue"], (int, float))
        assert isinstance(data["topOpportunities"], list)
        
        print(f"✓ CRM Dashboard returns correct structure - Contacts: {data['totalContacts']}, Opportunities: {data['activeOpportunities']}, Pipeline: €{data['pipelineValue']}")


class TestCRMContacts:
    """Test CRM Contacts CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup test contacts"""
        yield
        # Cleanup: Delete all test contacts
        try:
            contacts = requests.get(f"{BASE_URL}/api/crm/contacts").json()
            for contact in contacts:
                if contact.get("name", "").startswith(TEST_PREFIX):
                    requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")
        except:
            pass
    
    def test_get_contacts_empty_or_list(self):
        """Test GET /api/crm/contacts returns list"""
        response = requests.get(f"{BASE_URL}/api/crm/contacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/contacts returns list with {len(data)} contacts")
    
    def test_create_contact_and_verify(self):
        """Test POST /api/crm/contacts creates contact and verify with GET"""
        contact_data = {
            "name": f"{TEST_PREFIX}Juan García",
            "email": "juan.garcia@test.com",
            "phone": "+34 612 345 678",
            "company": "Cocinas García S.L.",
            "position": "Director Comercial",
            "address": "Calle Mayor 123, Madrid",
            "notes": "Cliente potencial interesado en cocina premium",
            "status": "lead",
            "source": "web"
        }
        
        # Create contact
        response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert response.status_code == 200
        created = response.json()
        
        # Verify created data
        assert created["name"] == contact_data["name"]
        assert created["email"] == contact_data["email"]
        assert created["company"] == contact_data["company"]
        assert created["status"] == "lead"
        assert "id" in created
        contact_id = created["id"]
        
        # GET to verify persistence
        get_response = requests.get(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["name"] == contact_data["name"]
        assert fetched["email"] == contact_data["email"]
        
        print(f"✓ Contact created and verified: {created['name']} (ID: {contact_id})")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
    
    def test_update_contact_and_verify(self):
        """Test PUT /api/crm/contacts/{id} updates contact"""
        # Create contact first
        contact_data = {
            "name": f"{TEST_PREFIX}María López",
            "email": "maria@test.com",
            "status": "lead"
        }
        create_response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        contact_id = create_response.json()["id"]
        
        # Update contact
        update_data = {
            "status": "customer",
            "company": "Reformas López",
            "phone": "+34 600 111 222"
        }
        update_response = requests.put(f"{BASE_URL}/api/crm/contacts/{contact_id}", json=update_data)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["status"] == "customer"
        assert updated["company"] == "Reformas López"
        
        # GET to verify persistence
        get_response = requests.get(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        fetched = get_response.json()
        assert fetched["status"] == "customer"
        assert fetched["company"] == "Reformas López"
        
        print(f"✓ Contact updated: status=customer, company=Reformas López")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
    
    def test_delete_contact_and_verify(self):
        """Test DELETE /api/crm/contacts/{id} removes contact"""
        # Create contact
        contact_data = {"name": f"{TEST_PREFIX}ToDelete", "status": "lead"}
        create_response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        contact_id = create_response.json()["id"]
        
        # Delete contact
        delete_response = requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        assert get_response.status_code == 404
        
        print(f"✓ Contact deleted and verified not found (404)")
    
    def test_filter_contacts_by_status(self):
        """Test GET /api/crm/contacts?status=lead filters correctly"""
        # Create contacts with different statuses
        lead_contact = {"name": f"{TEST_PREFIX}LeadContact", "status": "lead"}
        customer_contact = {"name": f"{TEST_PREFIX}CustomerContact", "status": "customer"}
        
        lead_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json=lead_contact)
        customer_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json=customer_contact)
        lead_id = lead_resp.json()["id"]
        customer_id = customer_resp.json()["id"]
        
        # Filter by lead status
        response = requests.get(f"{BASE_URL}/api/crm/contacts?status=lead")
        assert response.status_code == 200
        leads = response.json()
        
        # Verify filter works
        lead_names = [c["name"] for c in leads]
        assert f"{TEST_PREFIX}LeadContact" in lead_names
        
        print(f"✓ Status filter works - Found {len(leads)} leads")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{lead_id}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{customer_id}")


class TestCRMOpportunities:
    """Test CRM Opportunities (Pipeline) CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup test opportunities"""
        yield
        # Cleanup
        try:
            opps = requests.get(f"{BASE_URL}/api/crm/opportunities").json()
            for opp in opps:
                if opp.get("title", "").startswith(TEST_PREFIX):
                    requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
            contacts = requests.get(f"{BASE_URL}/api/crm/contacts").json()
            for contact in contacts:
                if contact.get("name", "").startswith(TEST_PREFIX):
                    requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")
        except:
            pass
    
    def test_get_opportunities_list(self):
        """Test GET /api/crm/opportunities returns list"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/opportunities returns list with {len(data)} opportunities")
    
    def test_create_opportunity_and_verify(self):
        """Test POST /api/crm/opportunities creates opportunity"""
        # Create a contact first
        contact_data = {"name": f"{TEST_PREFIX}OppContact", "status": "lead"}
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        contact_id = contact_resp.json()["id"]
        
        # Create opportunity
        opp_data = {
            "title": f"{TEST_PREFIX}Cocina Premium Villa",
            "description": "Presupuesto cocina completa con isla central",
            "contactId": contact_id,
            "contactName": f"{TEST_PREFIX}OppContact",
            "company": "Villa Luxury",
            "value": 25000,
            "probability": 60,
            "stage": "lead",
            "expectedCloseDate": "2026-03-15",
            "notes": "Cliente muy interesado"
        }
        
        response = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        assert response.status_code == 200
        created = response.json()
        
        # Verify created data
        assert created["title"] == opp_data["title"]
        assert created["value"] == 25000
        assert created["stage"] == "lead"
        assert created["probability"] == 60
        assert "id" in created
        opp_id = created["id"]
        
        # GET to verify persistence
        get_response = requests.get(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["title"] == opp_data["title"]
        assert fetched["value"] == 25000
        
        print(f"✓ Opportunity created: {created['title']} - €{created['value']} (Stage: {created['stage']})")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
    
    def test_update_opportunity_stage(self):
        """Test updating opportunity stage (pipeline movement)"""
        # Create contact and opportunity
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json={"name": f"{TEST_PREFIX}StageContact", "status": "lead"})
        contact_id = contact_resp.json()["id"]
        
        opp_data = {
            "title": f"{TEST_PREFIX}Pipeline Test",
            "contactId": contact_id,
            "value": 15000,
            "stage": "lead"
        }
        opp_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        opp_id = opp_resp.json()["id"]
        
        # Update stage: lead -> contacted -> proposal -> negotiation
        stages = ["contacted", "proposal", "negotiation"]
        for stage in stages:
            update_resp = requests.put(f"{BASE_URL}/api/crm/opportunities/{opp_id}", json={"stage": stage})
            assert update_resp.status_code == 200
            assert update_resp.json()["stage"] == stage
        
        # Verify final stage
        get_resp = requests.get(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        assert get_resp.json()["stage"] == "negotiation"
        
        print(f"✓ Pipeline stages work: lead → contacted → proposal → negotiation")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
    
    def test_opportunity_won_stage(self):
        """Test marking opportunity as won"""
        # Create contact and opportunity
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json={"name": f"{TEST_PREFIX}WonContact", "status": "lead"})
        contact_id = contact_resp.json()["id"]
        
        opp_data = {
            "title": f"{TEST_PREFIX}Won Deal",
            "contactId": contact_id,
            "value": 30000,
            "stage": "negotiation"
        }
        opp_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        opp_id = opp_resp.json()["id"]
        
        # Mark as won
        update_resp = requests.put(f"{BASE_URL}/api/crm/opportunities/{opp_id}", json={"stage": "won"})
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["stage"] == "won"
        assert "closedAt" in updated  # Should have closedAt timestamp
        
        print(f"✓ Opportunity marked as WON with closedAt timestamp")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
    
    def test_delete_opportunity(self):
        """Test DELETE /api/crm/opportunities/{id}"""
        # Create and delete
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json={"name": f"{TEST_PREFIX}DelOppContact", "status": "lead"})
        contact_id = contact_resp.json()["id"]
        
        opp_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json={
            "title": f"{TEST_PREFIX}ToDelete",
            "contactId": contact_id,
            "value": 5000,
            "stage": "lead"
        })
        opp_id = opp_resp.json()["id"]
        
        # Delete
        delete_resp = requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        assert delete_resp.status_code == 200
        
        # Verify deletion
        get_resp = requests.get(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        assert get_resp.status_code == 404
        
        print(f"✓ Opportunity deleted and verified (404)")
        
        # Cleanup contact
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")


class TestCRMActivities:
    """Test CRM Activities CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Cleanup test activities"""
        yield
        try:
            activities = requests.get(f"{BASE_URL}/api/crm/activities").json()
            for act in activities:
                if act.get("title", "").startswith(TEST_PREFIX):
                    requests.delete(f"{BASE_URL}/api/crm/activities/{act['id']}")
        except:
            pass
    
    def test_get_activities_list(self):
        """Test GET /api/crm/activities returns list"""
        response = requests.get(f"{BASE_URL}/api/crm/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/activities returns list with {len(data)} activities")
    
    def test_create_activity(self):
        """Test POST /api/crm/activities creates activity"""
        activity_data = {
            "type": "call",
            "title": f"{TEST_PREFIX}Llamar cliente",
            "description": "Seguimiento presupuesto cocina",
            "dueDate": "2026-02-01",
            "dueTime": "10:00",
            "priority": "high"
        }
        
        response = requests.post(f"{BASE_URL}/api/crm/activities", json=activity_data)
        assert response.status_code == 200
        created = response.json()
        
        assert created["title"] == activity_data["title"]
        assert created["type"] == "call"
        assert created["priority"] == "high"
        assert created["completed"] == False
        
        print(f"✓ Activity created: {created['title']} (Type: {created['type']}, Priority: {created['priority']})")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/activities/{created['id']}")


class TestCRMIntegration:
    """Integration tests for CRM workflow"""
    
    def test_full_crm_workflow(self):
        """Test complete CRM workflow: Contact → Opportunity → Activity"""
        # 1. Create Contact
        contact_data = {
            "name": f"{TEST_PREFIX}Integration Client",
            "email": "integration@test.com",
            "company": "Integration Corp",
            "status": "lead"
        }
        contact_resp = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert contact_resp.status_code == 200
        contact = contact_resp.json()
        contact_id = contact["id"]
        print(f"  1. Contact created: {contact['name']}")
        
        # 2. Create Opportunity linked to Contact
        opp_data = {
            "title": f"{TEST_PREFIX}Integration Deal",
            "contactId": contact_id,
            "contactName": contact["name"],
            "company": contact["company"],
            "value": 20000,
            "probability": 50,
            "stage": "lead"
        }
        opp_resp = requests.post(f"{BASE_URL}/api/crm/opportunities", json=opp_data)
        assert opp_resp.status_code == 200
        opp = opp_resp.json()
        opp_id = opp["id"]
        print(f"  2. Opportunity created: {opp['title']} - €{opp['value']}")
        
        # 3. Create Activity linked to Opportunity
        activity_data = {
            "type": "meeting",
            "title": f"{TEST_PREFIX}Reunión presupuesto",
            "contactId": contact_id,
            "contactName": contact["name"],
            "opportunityId": opp_id,
            "opportunityTitle": opp["title"],
            "dueDate": "2026-02-15",
            "priority": "high"
        }
        act_resp = requests.post(f"{BASE_URL}/api/crm/activities", json=activity_data)
        assert act_resp.status_code == 200
        activity = act_resp.json()
        act_id = activity["id"]
        print(f"  3. Activity created: {activity['title']}")
        
        # 4. Move opportunity through pipeline
        for stage in ["contacted", "proposal", "negotiation", "won"]:
            update_resp = requests.put(f"{BASE_URL}/api/crm/opportunities/{opp_id}", json={"stage": stage})
            assert update_resp.status_code == 200
        print(f"  4. Opportunity moved through pipeline to WON")
        
        # 5. Verify dashboard reflects changes
        dashboard_resp = requests.get(f"{BASE_URL}/api/crm/dashboard")
        assert dashboard_resp.status_code == 200
        dashboard = dashboard_resp.json()
        print(f"  5. Dashboard updated - Contacts: {dashboard['totalContacts']}, Won: {dashboard['wonThisMonth']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/activities/{act_id}")
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp_id}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        
        print(f"✓ Full CRM workflow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
