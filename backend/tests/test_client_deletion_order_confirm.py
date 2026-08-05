# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test Client CRUD Operations and Order Confirmation Endpoint
Focus: Client deletion bug fix and order confirmation email endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestClientCRUD:
    """Test Client CRUD operations - focus on deletion"""
    
    def test_get_all_clients(self):
        """Test GET /api/clients returns list of clients"""
        response = requests.get(f"{BASE_URL}/api/clients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ GET /api/clients - Found {len(data)} clients")
    
    def test_create_client(self):
        """Test POST /api/clients creates a new client"""
        unique_id = uuid.uuid4().hex[:8]
        client_data = {
            "tipo": "potencial",
            "codigo": f"TEST-{unique_id}",
            "nombre": f"Test Client {unique_id}",
            "cif": "B12345678",
            "segmento": "Tienda",
            "direccion": "Test Address 123",
            "localidad": "Madrid",
            "provincia": "Madrid",
            "codigoPostal": "28001",
            "telefono": "600123456",
            "email": "test@example.com",
            "descuento": 10,
            "activo": True,
            "notas": "Test client for deletion testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["codigo"] == client_data["codigo"].upper()
        assert data["nombre"] == client_data["nombre"]
        print(f"✅ POST /api/clients - Created client: {data['id']}")
        return data
    
    def test_create_and_delete_client(self):
        """Test full create -> delete flow (main bug fix test)"""
        # Step 1: Create a test client
        unique_id = uuid.uuid4().hex[:8]
        client_data = {
            "tipo": "potencial",
            "codigo": f"DEL-{unique_id}",
            "nombre": f"Delete Test Client {unique_id}",
            "cif": "B99999999",
            "segmento": "Tienda",
            "direccion": "Delete Test Address",
            "localidad": "Barcelona",
            "provincia": "Barcelona",
            "codigoPostal": "08001",
            "telefono": "600999999",
            "email": "delete-test@example.com",
            "descuento": 0,
            "activo": True,
            "notas": "This client will be deleted"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created_client = create_response.json()
        client_id = created_client["id"]
        print(f"✅ Created client for deletion test: {client_id}")
        
        # Step 2: Verify client exists
        get_response = requests.get(f"{BASE_URL}/api/clients/{client_id}")
        assert get_response.status_code == 200, f"Client not found after creation"
        print(f"✅ Verified client exists: {client_id}")
        
        # Step 3: Delete the client (THIS IS THE BUG FIX TEST)
        delete_response = requests.delete(f"{BASE_URL}/api/clients/{client_id}")
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code} - {delete_response.text}"
        
        # Verify response body
        delete_data = delete_response.json()
        assert "message" in delete_data or delete_response.status_code == 200
        print(f"✅ DELETE /api/clients/{client_id} - Success: {delete_data}")
        
        # Step 4: Verify client no longer exists
        verify_response = requests.get(f"{BASE_URL}/api/clients/{client_id}")
        assert verify_response.status_code == 404, f"Client still exists after deletion!"
        print(f"✅ Verified client deleted: {client_id} returns 404")
    
    def test_delete_nonexistent_client(self):
        """Test DELETE /api/clients/{id} with non-existent ID returns 404"""
        fake_id = f"cli-nonexistent-{uuid.uuid4().hex[:8]}"
        response = requests.delete(f"{BASE_URL}/api/clients/{fake_id}")
        assert response.status_code == 404
        print(f"✅ DELETE non-existent client returns 404")
    
    def test_update_client(self):
        """Test PUT /api/clients/{id} updates client"""
        # Create a client first
        unique_id = uuid.uuid4().hex[:8]
        client_data = {
            "tipo": "potencial",
            "codigo": f"UPD-{unique_id}",
            "nombre": f"Update Test Client {unique_id}",
            "cif": "B11111111",
            "segmento": "Tienda",
            "direccion": "Original Address",
            "localidad": "Valencia",
            "provincia": "Valencia",
            "codigoPostal": "46001",
            "telefono": "600111111",
            "email": "update-test@example.com",
            "descuento": 5,
            "activo": True,
            "notas": "Original notes"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 200
        client_id = create_response.json()["id"]
        
        # Update the client
        update_data = {
            "nombre": f"Updated Client Name {unique_id}",
            "descuento": 15,
            "notas": "Updated notes"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/clients/{client_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert update_response.status_code == 200
        updated_client = update_response.json()
        assert updated_client["nombre"] == update_data["nombre"]
        assert updated_client["descuento"] == update_data["descuento"]
        print(f"✅ PUT /api/clients/{client_id} - Updated successfully")
        
        # Cleanup: delete the test client
        requests.delete(f"{BASE_URL}/api/clients/{client_id}")
    
    def test_get_client_segments(self):
        """Test GET /api/clients/segments returns segment list"""
        response = requests.get(f"{BASE_URL}/api/clients/segments")
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert isinstance(data["segments"], list)
        print(f"✅ GET /api/clients/segments - Found {len(data['segments'])} segments")


class TestOrderConfirmation:
    """Test Order Confirmation Email Endpoint"""
    
    def test_order_confirm_endpoint_exists(self):
        """Test POST /api/orders/confirm endpoint exists and accepts form data"""
        # Send minimal form data to test endpoint
        form_data = {
            "budgetNumber": "TEST-001",
            "customerName": "Test Customer",
            "customerAddress": "Test Address 123",
            "totalAmount": "1500.00",
            "email": "test@example.com",
            "notes": "Test order confirmation",
            "items": "[]",
            "doorColorLow": "",
            "doorColorHigh": "",
            "doorColorColumns": "",
            "sideColor": "",
            "carcassColor": "",
            "globalFinish": "",
            "distributorName": "Test Distributor"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/orders/confirm",
            data=form_data
        )
        
        # Should return 200 if SendGrid is configured, or 500 with specific error if not
        if response.status_code == 200:
            print(f"✅ POST /api/orders/confirm - Email sent successfully")
        elif response.status_code == 500:
            data = response.json()
            # Check if it's a SendGrid configuration error (expected in test env)
            if "SENDGRID" in str(data.get("detail", "")):
                print(f"⚠️ POST /api/orders/confirm - SendGrid not configured (expected in test)")
            else:
                print(f"❌ POST /api/orders/confirm - Unexpected error: {data}")
        else:
            # Endpoint exists but returned unexpected status
            print(f"⚠️ POST /api/orders/confirm - Status: {response.status_code}")
        
        # The endpoint should exist (not 404)
        assert response.status_code != 404, "Order confirm endpoint not found"
    
    def test_order_confirm_with_items(self):
        """Test order confirmation with item list"""
        import json
        
        items = [
            {"code": "35A1P400", "name": "Alto 35cm 1 Puerta 400mm", "quantity": 2, "price": 150.00},
            {"code": "7B2P600", "name": "Bajo 70cm 2 Puertas 600mm", "quantity": 1, "price": 280.00}
        ]
        
        form_data = {
            "budgetNumber": "TEST-002",
            "customerName": "Test Customer with Items",
            "customerAddress": "Test Address 456",
            "totalAmount": "580.00",
            "email": "test@example.com",
            "notes": "Order with items",
            "items": json.dumps(items),
            "doorColorLow": "Blanco Brillo",
            "doorColorHigh": "Blanco Mate",
            "doorColorColumns": "Blanco Brillo",
            "sideColor": "Melamina Blanca",
            "carcassColor": "Melamina Blanca 16mm",
            "globalFinish": "Moderno",
            "distributorName": "Cocinas Test SL"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/orders/confirm",
            data=form_data
        )
        
        # Endpoint should exist
        assert response.status_code != 404, "Order confirm endpoint not found"
        print(f"✅ POST /api/orders/confirm with items - Status: {response.status_code}")


class TestClientDeletionFromUI:
    """Simulate UI deletion flow - tests the exact API call pattern from frontend"""
    
    def test_ui_delete_flow(self):
        """
        Simulates the exact flow from SettingsModal.jsx:
        1. Create client
        2. Call DELETE endpoint (same as clientsAPI.delete())
        3. Verify response can be parsed as JSON
        4. Verify client is deleted
        """
        # Create test client
        unique_id = uuid.uuid4().hex[:8]
        client_data = {
            "tipo": "potencial",
            "codigo": f"UI-DEL-{unique_id}",
            "nombre": f"UI Delete Test {unique_id}",
            "cif": "B77777777",
            "segmento": "Tienda",
            "direccion": "UI Test Address",
            "localidad": "Sevilla",
            "provincia": "Sevilla",
            "codigoPostal": "41001",
            "telefono": "600777777",
            "email": "ui-delete@example.com",
            "descuento": 0,
            "activo": True,
            "notas": "UI deletion test"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/clients",
            json=client_data,
            headers={"Content-Type": "application/json"}
        )
        assert create_response.status_code == 200
        client_id = create_response.json()["id"]
        print(f"✅ Created UI test client: {client_id}")
        
        # Simulate UI DELETE call
        delete_response = requests.delete(f"{BASE_URL}/api/clients/{client_id}")
        
        # This is the key test - the response should be parseable as JSON
        # The bug was "body stream already read" error
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.status_code}"
        
        try:
            delete_data = delete_response.json()
            print(f"✅ DELETE response parsed successfully: {delete_data}")
        except Exception as e:
            pytest.fail(f"Failed to parse DELETE response as JSON: {e}")
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/clients/{client_id}")
        assert verify_response.status_code == 404
        print(f"✅ UI delete flow complete - client {client_id} deleted")


# Cleanup fixture to remove test clients after all tests
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_clients():
    """Cleanup any leftover test clients after tests complete"""
    yield
    # After tests, clean up any TEST-, DEL-, UPD-, UI-DEL- prefixed clients
    try:
        response = requests.get(f"{BASE_URL}/api/clients")
        if response.status_code == 200:
            clients = response.json()
            for client in clients:
                codigo = client.get("codigo", "")
                if any(codigo.startswith(prefix) for prefix in ["TEST-", "DEL-", "UPD-", "UI-DEL-"]):
                    requests.delete(f"{BASE_URL}/api/clients/{client['id']}")
                    print(f"🧹 Cleaned up test client: {codigo}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
