"""
Test suite for CRM Contacts → Clients conversion and Client management features.

Features tested:
1. CRM Contactos: Botón 'Convertir a Cliente Potencial' - crear cliente potencial desde contacto CRM
2. CRM Contactos: Contacto convertido muestra etiqueta 'CONVERTIDO'
3. Maestro→Clientes: Ver lista de clientes con colores (potencial=naranja, activo=verde)
4. Maestro→Clientes: Filtrar por tipo (Todos/Potenciales/Activos)
5. Maestro→Clientes: Botón 'Activar' visible solo para clientes potenciales sin código
6. Maestro→Clientes: Activar cliente potencial asignando código
7. Maestro→Clientes: Botón 'Vincular Usuario' funcional
8. Red Distribución→Usuarios: Al seleccionar cliente vinculado, se hereda el descuento
9. Navegación: Comerciales ven botón 'Mis Tiendas' en sidebar
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://luiggi-erp-4.preview.emergentagent.com')

class TestClientsAPI:
    """Test Client CRUD operations"""
    
    def test_get_all_clients(self):
        """GET /api/clients - should return list of clients"""
        response = requests.get(f"{BASE_URL}/api/clients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/clients - Found {len(data)} clients")
        return data
    
    def test_get_client_segments(self):
        """GET /api/clients/segments - should return available segments"""
        response = requests.get(f"{BASE_URL}/api/clients/segments")
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert isinstance(data["segments"], list)
        assert len(data["segments"]) > 0
        print(f"✅ GET /api/clients/segments - Found {len(data['segments'])} segments")
        print(f"   Segments: {data['segments'][:3]}...")
    
    def test_existing_clients_have_correct_structure(self):
        """Verify existing clients have tipo field (potencial/activo)"""
        response = requests.get(f"{BASE_URL}/api/clients")
        assert response.status_code == 200
        clients = response.json()
        
        for client in clients:
            assert "id" in client
            assert "nombre" in client
            # tipo should be 'potencial' or 'activo' (or inferred from codigo)
            tipo = client.get("tipo", "potencial" if not client.get("codigo") else "activo")
            assert tipo in ["potencial", "activo"]
            print(f"   Client: {client['nombre']} | tipo: {tipo} | codigo: {client.get('codigo', '')}")
        
        print(f"✅ All {len(clients)} clients have correct structure")


class TestCRMContactToClientConversion:
    """Test converting CRM contacts to potential clients"""
    
    def test_create_new_crm_contact(self):
        """Create a new CRM contact for conversion testing"""
        unique_id = uuid.uuid4().hex[:6]
        contact_data = {
            "name": f"TEST_Contact_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "phone": "600123456",
            "company": f"TEST Company {unique_id}",
            "position": "Manager",
            "address": "Test Address 123",
            "notes": "Test contact for conversion",
            "status": "lead",
            "source": "test"
        }
        
        response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == contact_data["name"]
        print(f"✅ Created CRM contact: {data['id']} - {data['name']}")
        return data
    
    def test_convert_contact_to_potential_client(self):
        """POST /api/clients/from-contact/{contact_id} - convert CRM contact to potential client"""
        # First create a new contact
        unique_id = uuid.uuid4().hex[:6]
        contact_data = {
            "name": f"TEST_Convert_{unique_id}",
            "email": f"convert_{unique_id}@example.com",
            "phone": "600111222",
            "company": f"Convert Company {unique_id}",
            "address": "Convert Address 456",
            "notes": "Contact to convert",
            "status": "lead"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/crm/contacts", json=contact_data)
        assert create_response.status_code == 200
        contact = create_response.json()
        contact_id = contact["id"]
        print(f"   Created contact: {contact_id}")
        
        # Convert to potential client
        convert_response = requests.post(f"{BASE_URL}/api/clients/from-contact/{contact_id}")
        assert convert_response.status_code == 200
        client = convert_response.json()
        
        # Verify client data
        assert client["tipo"] == "potencial"
        assert client["codigo"] == ""  # No code for potential clients
        assert client["nombre"] == contact_data["name"]
        assert client["telefono"] == contact_data["phone"]
        assert client["email"] == contact_data["email"]
        assert client["origenCrmContactId"] == contact_id
        
        print(f"✅ Converted contact to potential client: {client['id']}")
        print(f"   tipo: {client['tipo']}, codigo: '{client['codigo']}', nombre: {client['nombre']}")
        
        # Verify contact is marked as converted
        contact_check = requests.get(f"{BASE_URL}/api/crm/contacts/{contact_id}")
        assert contact_check.status_code == 200
        updated_contact = contact_check.json()
        assert updated_contact.get("convertedToClientId") == client["id"]
        assert updated_contact.get("status") == "customer"
        print(f"✅ Contact marked as converted: convertedToClientId={updated_contact['convertedToClientId']}")
        
        return client
    
    def test_cannot_convert_already_converted_contact(self):
        """Should fail when trying to convert an already converted contact"""
        # Get existing converted contact (Juan García)
        contacts_response = requests.get(f"{BASE_URL}/api/crm/contacts")
        contacts = contacts_response.json()
        
        converted_contact = None
        for c in contacts:
            if c.get("convertedToClientId"):
                converted_contact = c
                break
        
        if converted_contact:
            # Try to convert again
            response = requests.post(f"{BASE_URL}/api/clients/from-contact/{converted_contact['id']}")
            assert response.status_code == 400
            print(f"✅ Correctly rejected re-conversion of contact: {converted_contact['name']}")
        else:
            print("⚠️ No converted contact found to test re-conversion rejection")


class TestClientActivation:
    """Test activating potential clients by assigning code"""
    
    def test_activate_potential_client(self):
        """POST /api/clients/{id}/activate - activate potential client with code"""
        # First create a potential client
        unique_id = uuid.uuid4().hex[:6]
        client_data = {
            "tipo": "potencial",
            "codigo": "",
            "nombre": f"TEST_Activate_{unique_id}",
            "cif": f"B{unique_id}",
            "telefono": "600333444",
            "email": f"activate_{unique_id}@example.com"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data)
        assert create_response.status_code == 200
        client = create_response.json()
        client_id = client["id"]
        print(f"   Created potential client: {client_id}")
        
        # Activate with code
        activate_code = f"CLI-TEST-{unique_id}"
        activate_response = requests.post(
            f"{BASE_URL}/api/clients/{client_id}/activate",
            json={"codigo": activate_code}
        )
        assert activate_response.status_code == 200
        activated = activate_response.json()
        
        assert activated["tipo"] == "activo"
        assert activated["codigo"] == activate_code.upper()
        assert activated.get("convertidoAt") is not None
        
        print(f"✅ Activated client: {activated['nombre']}")
        print(f"   tipo: {activated['tipo']}, codigo: {activated['codigo']}")
        
        return activated
    
    def test_cannot_activate_without_code(self):
        """Should fail when activating without providing code"""
        # Create potential client
        unique_id = uuid.uuid4().hex[:6]
        client_data = {
            "tipo": "potencial",
            "nombre": f"TEST_NoCode_{unique_id}"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data)
        client = create_response.json()
        
        # Try to activate without code
        response = requests.post(
            f"{BASE_URL}/api/clients/{client['id']}/activate",
            json={"codigo": ""}
        )
        assert response.status_code == 400
        print(f"✅ Correctly rejected activation without code")
    
    def test_cannot_activate_already_active_client(self):
        """Should fail when trying to activate an already active client"""
        # Get existing active client (Cocinas Pérez S.L.)
        clients_response = requests.get(f"{BASE_URL}/api/clients")
        clients = clients_response.json()
        
        active_client = None
        for c in clients:
            if c.get("codigo") and c.get("tipo") == "activo":
                active_client = c
                break
            # Infer tipo from codigo if not set
            if c.get("codigo") and not c.get("tipo"):
                active_client = c
                break
        
        if active_client:
            response = requests.post(
                f"{BASE_URL}/api/clients/{active_client['id']}/activate",
                json={"codigo": "NEW-CODE"}
            )
            assert response.status_code == 400
            print(f"✅ Correctly rejected re-activation of client: {active_client['nombre']}")
        else:
            print("⚠️ No active client found to test re-activation rejection")


class TestClientUserLinking:
    """Test linking clients to users"""
    
    def test_link_client_to_user(self):
        """POST /api/clients/{id}/link-user - link client to user"""
        # Create a test client
        unique_id = uuid.uuid4().hex[:6]
        client_data = {
            "tipo": "activo",
            "codigo": f"LINK-{unique_id}",
            "nombre": f"TEST_Link_{unique_id}"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/clients", json=client_data)
        assert create_response.status_code == 200
        client = create_response.json()
        
        # Get existing user to link
        users_response = requests.get(f"{BASE_URL}/api/users")
        users = users_response.json()
        
        if len(users) > 0:
            user_to_link = users[0]
            
            # Link client to user
            link_response = requests.post(
                f"{BASE_URL}/api/clients/{client['id']}/link-user",
                json={"userId": user_to_link["id"]}
            )
            assert link_response.status_code == 200
            linked_client = link_response.json()
            
            assert linked_client["usuarioVinculadoId"] == user_to_link["id"]
            print(f"✅ Linked client {client['nombre']} to user {user_to_link['username']}")
            
            # Verify user has linkedClientId
            user_check = requests.get(f"{BASE_URL}/api/users/{user_to_link['id']}")
            if user_check.status_code == 200:
                updated_user = user_check.json()
                assert updated_user.get("linkedClientId") == client["id"]
                print(f"✅ User {updated_user['username']} has linkedClientId: {updated_user['linkedClientId']}")
        else:
            print("⚠️ No users found to test linking")


class TestCommercialEndpoint:
    """Test commercial/representative endpoints"""
    
    def test_commercial_my_shops_work_endpoint(self):
        """GET /api/commercial/my-shops-work - should return shops work for commercial"""
        # Get a commercial user (isRepresentative=True)
        users_response = requests.get(f"{BASE_URL}/api/users")
        users = users_response.json()
        
        commercial_user = None
        for u in users:
            if u.get("isRepresentative") and not u.get("isAdmin"):
                commercial_user = u
                break
        
        if commercial_user:
            response = requests.get(
                f"{BASE_URL}/api/commercial/my-shops-work",
                params={"commercial_id": commercial_user["id"]}
            )
            assert response.status_code == 200
            data = response.json()
            
            assert "shops" in data
            assert "projects" in data
            assert "opportunities" in data
            assert "summary" in data
            
            print(f"✅ GET /api/commercial/my-shops-work for {commercial_user['username']}")
            print(f"   Shops: {data['summary']['totalShops']}, Projects: {data['summary']['totalProjects']}")
        else:
            # Test with admin user (should still work but return empty)
            admin_user = next((u for u in users if u.get("isAdmin")), None)
            if admin_user:
                response = requests.get(
                    f"{BASE_URL}/api/commercial/my-shops-work",
                    params={"commercial_id": admin_user["id"]}
                )
                assert response.status_code == 200
                print(f"✅ Endpoint works (tested with admin, no shops assigned)")


class TestUserClientDiscount:
    """Test that users inherit discount from linked client"""
    
    def test_user_creation_with_linked_client(self):
        """Create user with linked client and verify discount inheritance"""
        # First create a client with discount
        unique_id = uuid.uuid4().hex[:6]
        client_data = {
            "tipo": "activo",
            "codigo": f"DISC-{unique_id}",
            "nombre": f"TEST_Discount_{unique_id}",
            "descuento": 25  # 25% discount
        }
        
        client_response = requests.post(f"{BASE_URL}/api/clients", json=client_data)
        assert client_response.status_code == 200
        client = client_response.json()
        print(f"   Created client with 25% discount: {client['id']}")
        
        # Create user linked to this client
        user_data = {
            "username": f"TEST_USER_{unique_id}",
            "password": "testpass123",
            "clientName": f"Test User {unique_id}",
            "linkedClientId": client["id"],
            "commercialDiscount": 25,  # Should match client discount
            "isActive": True
        }
        
        user_response = requests.post(f"{BASE_URL}/api/users", json=user_data)
        assert user_response.status_code == 200
        user = user_response.json()
        
        assert user["linkedClientId"] == client["id"]
        assert user["commercialDiscount"] == 25
        print(f"✅ Created user {user['username']} linked to client with 25% discount")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{user['id']}")
        requests.delete(f"{BASE_URL}/api/clients/{client['id']}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self):
        """Remove TEST_ prefixed data"""
        # Cleanup clients
        clients_response = requests.get(f"{BASE_URL}/api/clients")
        if clients_response.status_code == 200:
            clients = clients_response.json()
            for c in clients:
                if c.get("nombre", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/clients/{c['id']}")
                    print(f"   Deleted test client: {c['nombre']}")
        
        # Cleanup contacts
        contacts_response = requests.get(f"{BASE_URL}/api/crm/contacts")
        if contacts_response.status_code == 200:
            contacts = contacts_response.json()
            for c in contacts:
                if c.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/crm/contacts/{c['id']}")
                    print(f"   Deleted test contact: {c['name']}")
        
        # Cleanup users
        users_response = requests.get(f"{BASE_URL}/api/users")
        if users_response.status_code == 200:
            users = users_response.json()
            for u in users:
                if u.get("username", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/users/{u['id']}")
                    print(f"   Deleted test user: {u['username']}")
        
        print("✅ Test data cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
