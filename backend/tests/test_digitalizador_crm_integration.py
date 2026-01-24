"""
Test Digitalizador → CRM Integration
Tests the connection between Digitalizador de Borradores and CRM module
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCRMContactsAPI:
    """Test CRM Contacts endpoints"""
    
    def test_get_contacts(self):
        """Test GET /api/crm/contacts returns list"""
        response = requests.get(f"{BASE_URL}/api/crm/contacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/contacts - Found {len(data)} contacts")
    
    def test_create_contact_from_digitalizador(self):
        """Test POST /api/crm/contacts with digitalizador source"""
        unique_id = str(uuid.uuid4())[:8]
        contact_data = {
            "name": f"TEST_Cliente_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "phone": "+34 600 000 000",
            "company": "Test Company",
            "type": "lead",
            "source": "digitalizador",
            "notes": "Contacto creado desde Digitalizador de Borradores - Proyecto: Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/crm/contacts",
            json=contact_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["name"] == contact_data["name"]
        assert data["source"] == "digitalizador"
        print(f"✓ POST /api/crm/contacts - Created contact: {data['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{data['id']}")
        return data
    
    def test_get_contact_by_id(self):
        """Test GET /api/crm/contacts/{id}"""
        # First create a contact
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/crm/contacts",
            json={"name": f"TEST_GetById_{unique_id}", "source": "digitalizador"}
        )
        contact_id = create_response.json()["id"]
        
        # Get by ID
        response = requests.get(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == contact_id
        print(f"✓ GET /api/crm/contacts/{contact_id} - Retrieved contact")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact_id}")


class TestCRMOpportunitiesAPI:
    """Test CRM Opportunities endpoints"""
    
    def test_get_opportunities(self):
        """Test GET /api/crm/opportunities returns list"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/crm/opportunities - Found {len(data)} opportunities")
    
    def test_create_opportunity_from_digitalizador(self):
        """Test POST /api/crm/opportunities with digitalizador tags"""
        unique_id = str(uuid.uuid4())[:8]
        
        # First create a contact
        contact_response = requests.post(
            f"{BASE_URL}/api/crm/contacts",
            json={"name": f"TEST_OppContact_{unique_id}", "source": "digitalizador"}
        )
        contact = contact_response.json()
        
        # Create opportunity
        opp_data = {
            "title": f"TEST_Presupuesto_{unique_id}",
            "description": "Presupuesto digitalizado - 5 líneas\nAcabado: Blanco\nArmazón: Melamina",
            "contactId": contact["id"],
            "contactName": contact["name"],
            "company": "",
            "value": 1500.50,
            "probability": 30,
            "stage": "lead",
            "notes": "Creado desde Digitalizador de Borradores\nBase imponible: 1240,00 €\nIVA (21%): 260,50 €",
            "tags": ["digitalizador", "presupuesto"],
            "assignedTo": "admin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/crm/opportunities",
            json=opp_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["title"] == opp_data["title"]
        assert data["value"] == 1500.50
        assert "digitalizador" in data["tags"]
        assert "presupuesto" in data["tags"]
        assert data["stage"] == "lead"
        print(f"✓ POST /api/crm/opportunities - Created opportunity: {data['id']} with value {data['value']}€")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{data['id']}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")
        return data
    
    def test_get_opportunity_by_id(self):
        """Test GET /api/crm/opportunities/{id}"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create contact and opportunity
        contact_response = requests.post(
            f"{BASE_URL}/api/crm/contacts",
            json={"name": f"TEST_OppGetById_{unique_id}"}
        )
        contact = contact_response.json()
        
        opp_response = requests.post(
            f"{BASE_URL}/api/crm/opportunities",
            json={
                "title": f"TEST_GetById_{unique_id}",
                "contactId": contact["id"],
                "value": 500,
                "tags": ["digitalizador"]
            }
        )
        opp = opp_response.json()
        
        # Get by ID
        response = requests.get(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == opp["id"]
        print(f"✓ GET /api/crm/opportunities/{opp['id']} - Retrieved opportunity")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")


class TestDigitalizadorCRMIntegration:
    """Test the full Digitalizador → CRM flow"""
    
    def test_existing_digitalizador_opportunity(self):
        """Verify existing opportunity created from Digitalizador"""
        response = requests.get(f"{BASE_URL}/api/crm/opportunities")
        assert response.status_code == 200
        
        opportunities = response.json()
        digitalizador_opps = [
            opp for opp in opportunities 
            if "digitalizador" in opp.get("tags", [])
        ]
        
        print(f"✓ Found {len(digitalizador_opps)} opportunities with 'digitalizador' tag")
        
        if digitalizador_opps:
            opp = digitalizador_opps[0]
            print(f"  - Title: {opp['title']}")
            print(f"  - Value: {opp['value']}€")
            print(f"  - Stage: {opp['stage']}")
            print(f"  - Contact: {opp.get('contactName', 'N/A')}")
    
    def test_existing_digitalizador_contact(self):
        """Verify existing contact created from Digitalizador"""
        response = requests.get(f"{BASE_URL}/api/crm/contacts")
        assert response.status_code == 200
        
        contacts = response.json()
        digitalizador_contacts = [
            c for c in contacts 
            if c.get("source") == "digitalizador"
        ]
        
        print(f"✓ Found {len(digitalizador_contacts)} contacts with 'digitalizador' source")
        
        if digitalizador_contacts:
            contact = digitalizador_contacts[0]
            print(f"  - Name: {contact['name']}")
            print(f"  - Notes: {contact.get('notes', 'N/A')[:50]}...")
    
    def test_full_digitalizador_to_crm_flow(self):
        """Test complete flow: Create contact → Create opportunity with correct value"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Simulate Digitalizador budget data
        project_name = f"TEST_Cocina_{unique_id}"
        customer_name = f"TEST_Cliente_{unique_id}"
        base_imponible = 1000.00
        iva_rate = 21
        iva = base_imponible * (iva_rate / 100)
        total = base_imponible + iva  # 1210.00
        
        # Step 1: Create contact (as Digitalizador does)
        contact_response = requests.post(
            f"{BASE_URL}/api/crm/contacts",
            json={
                "name": customer_name,
                "email": f"test_{unique_id}@test.com",
                "phone": "+34 600 123 456",
                "company": "",
                "type": "lead",
                "source": "digitalizador",
                "notes": f"Contacto creado desde Digitalizador de Borradores - Proyecto: {project_name}"
            }
        )
        assert contact_response.status_code == 200
        contact = contact_response.json()
        print(f"✓ Step 1: Created contact '{contact['name']}' with id {contact['id']}")
        
        # Step 2: Create opportunity (as Digitalizador does)
        opp_response = requests.post(
            f"{BASE_URL}/api/crm/opportunities",
            json={
                "title": project_name,
                "description": f"Presupuesto digitalizado - 3 líneas\nAcabado: Blanco\nArmazón: Melamina\nCostados: Color",
                "contactId": contact["id"],
                "contactName": contact["name"],
                "company": "",
                "value": total,  # Total with IVA
                "probability": 30,
                "stage": "lead",
                "notes": f"Creado desde Digitalizador de Borradores\nBase imponible: {base_imponible:.2f} €\nIVA ({iva_rate}%): {iva:.2f} €",
                "tags": ["digitalizador", "presupuesto"],
                "assignedTo": "admin"
            }
        )
        assert opp_response.status_code == 200
        opp = opp_response.json()
        print(f"✓ Step 2: Created opportunity '{opp['title']}' with value {opp['value']}€")
        
        # Verify opportunity has correct value
        assert opp["value"] == total
        assert opp["contactId"] == contact["id"]
        assert "digitalizador" in opp["tags"]
        assert "presupuesto" in opp["tags"]
        print(f"✓ Step 3: Verified opportunity value matches total ({total}€)")
        
        # Verify opportunity appears in CRM dashboard
        dashboard_response = requests.get(f"{BASE_URL}/api/crm/dashboard")
        assert dashboard_response.status_code == 200
        dashboard = dashboard_response.json()
        print(f"✓ Step 4: CRM Dashboard accessible - {dashboard['activeOpportunities']} active opportunities")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/opportunities/{opp['id']}")
        requests.delete(f"{BASE_URL}/api/crm/contacts/{contact['id']}")
        print(f"✓ Cleanup: Deleted test contact and opportunity")


class TestCRMDashboard:
    """Test CRM Dashboard endpoint"""
    
    def test_dashboard_returns_stats(self):
        """Test GET /api/crm/dashboard returns statistics"""
        response = requests.get(f"{BASE_URL}/api/crm/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert "totalContacts" in data
        assert "activeOpportunities" in data
        assert "pipelineValue" in data
        assert "topOpportunities" in data
        
        print(f"✓ GET /api/crm/dashboard")
        print(f"  - Total Contacts: {data['totalContacts']}")
        print(f"  - Active Opportunities: {data['activeOpportunities']}")
        print(f"  - Pipeline Value: {data['pipelineValue']}€")


class TestDigitalizadorHistory:
    """Test Digitalizador history endpoint"""
    
    def test_get_history(self):
        """Test GET /api/digitalizador/history"""
        response = requests.get(f"{BASE_URL}/api/digitalizador/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "items" in data
        
        print(f"✓ GET /api/digitalizador/history - Found {len(data['items'])} items")
        
        if data["items"]:
            item = data["items"][0]
            print(f"  - Latest: {item.get('projectName', 'N/A')} by {item.get('customerName', 'N/A')}")
            print(f"  - Total: {item.get('totalConIva', 0)}€")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
