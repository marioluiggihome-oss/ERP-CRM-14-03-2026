"""
Tests for Portal de Fábrica and Despiece PUERTAS calculation
Features tested:
1. Despiece calculation includes PUERTAS components (detecting 2P, 1P, D/I in product names)
2. Portal de Fábrica CRUD operations (create, list, update, delete orders)
3. Portal de Fábrica status changes
4. Portal de Fábrica delivery date setting
5. Dashboard statistics API
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def api_session():
    """Create a requests session with headers"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_session):
    """Get authentication token by logging in"""
    response = api_session.post(f"{BASE_URL}/api/auth/login", json={
        "username": "MARIO",
        "password": "MARIO"
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("tokens", {}).get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def authenticated_session(api_session, auth_token):
    """Session with auth header"""
    if auth_token:
        api_session.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_session


@pytest.fixture
def cleanup_test_orders(api_session):
    """Cleanup test orders after tests"""
    created_order_ids = []
    yield created_order_ids
    # Cleanup: delete all test-created orders
    for order_id in created_order_ids:
        try:
            api_session.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        except:
            pass


# ==========================================
# TEST: DESPIECE PUERTAS CALCULATION
# ==========================================

class TestDespiecePuertas:
    """Test that despiece calculation includes PUERTAS components"""

    def test_despiece_2p_mueble_includes_2_puertas(self, api_session):
        """Test: A furniture item with 2P in name should have 2 doors calculated"""
        # Create a despiece request with a 2P furniture item
        payload = {
            "items": [
                {
                    "productId": "test-2p-001",
                    "productCode": "7B2P600",
                    "productName": "BAJO 2P 600 - Bajo 2 puertas 60cm",
                    "width": 60,  # cm
                    "height": 70,  # cm
                    "depth": 58,  # cm
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "Melamina Blanca",
            "backPanelMaterial": "Tablero 8mm",
            "grosor": 18
        }
        
        response = api_session.post(f"{BASE_URL}/api/despiece/calculate", json=payload)
        assert response.status_code == 200, f"Despiece calculation failed: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        
        # Find the door component
        furniture_item = data["items"][0]
        components = furniture_item.get("components", [])
        
        # Look for PUERTA component
        puerta_components = [c for c in components if "PUERTA" in c.get("material", "").upper() or "PUERTA" in c.get("name", "").upper()]
        
        assert len(puerta_components) > 0, f"No PUERTA component found in despiece. Components: {[c.get('name') for c in components]}"
        
        # Verify door quantity is 2
        puerta = puerta_components[0]
        assert puerta.get("quantity") == 2, f"Expected 2 doors for 2P furniture, got {puerta.get('quantity')}"
        
        print(f"✅ 2P furniture has {puerta.get('quantity')} doors calculated")
        print(f"   Door dimensions: {puerta.get('length')}cm x {puerta.get('width')}cm")

    def test_despiece_1p_mueble_includes_1_puerta(self, api_session):
        """Test: A furniture item with 1P in name should have 1 door calculated"""
        payload = {
            "items": [
                {
                    "productId": "test-1p-001",
                    "productCode": "7B1P300",
                    "productName": "BAJO 1P 300 - Bajo 1 puerta 30cm",
                    "width": 30,
                    "height": 70,
                    "depth": 58,
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "Melamina Blanca",
            "backPanelMaterial": "Tablero 8mm",
            "grosor": 18
        }
        
        response = api_session.post(f"{BASE_URL}/api/despiece/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        furniture_item = data["items"][0]
        components = furniture_item.get("components", [])
        
        puerta_components = [c for c in components if "PUERTA" in c.get("material", "").upper() or "PUERTA" in c.get("name", "").upper()]
        
        assert len(puerta_components) > 0, "No PUERTA component found for 1P furniture"
        
        puerta = puerta_components[0]
        assert puerta.get("quantity") == 1, f"Expected 1 door for 1P furniture, got {puerta.get('quantity')}"
        
        print(f"✅ 1P furniture has {puerta.get('quantity')} door calculated")

    def test_despiece_di_mueble_includes_puerta(self, api_session):
        """Test: A furniture item with D/I (derecha/izquierda) should have 1 door"""
        payload = {
            "items": [
                {
                    "productId": "test-di-001",
                    "productCode": "7BDIR450",
                    "productName": "BAJO D/I 450 - Bajo puerta derecha/izquierda 45cm",
                    "width": 45,
                    "height": 70,
                    "depth": 58,
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "Melamina Blanca",
            "backPanelMaterial": "Tablero 8mm",
            "grosor": 18
        }
        
        response = api_session.post(f"{BASE_URL}/api/despiece/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        furniture_item = data["items"][0]
        components = furniture_item.get("components", [])
        
        puerta_components = [c for c in components if "PUERTA" in c.get("material", "").upper() or "PUERTA" in c.get("name", "").upper()]
        
        assert len(puerta_components) > 0, "No PUERTA component found for D/I furniture"
        
        puerta = puerta_components[0]
        assert puerta.get("quantity") == 1, f"Expected 1 door for D/I furniture, got {puerta.get('quantity')}"
        
        print(f"✅ D/I furniture has {puerta.get('quantity')} door calculated")

    def test_despiece_includes_standard_components(self, api_session):
        """Test: Despiece should include laterales, tapa, base, trasera, baldas"""
        payload = {
            "items": [
                {
                    "productId": "test-std-001",
                    "productCode": "7B2P600",
                    "productName": "BAJO 2P 600",
                    "width": 60,
                    "height": 70,
                    "depth": 58,
                    "quantity": 1,
                    "category": "BAJOS"
                }
            ],
            "carcassMaterial": "Melamina Blanca",
            "backPanelMaterial": "Tablero 8mm",
            "grosor": 18
        }
        
        response = api_session.post(f"{BASE_URL}/api/despiece/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        furniture_item = data["items"][0]
        components = furniture_item.get("components", [])
        
        component_names = [c.get("name", "").lower() for c in components]
        
        # Check for essential components
        has_lateral = any("lateral" in name for name in component_names)
        has_tapa = any("tapa" in name or "superior" in name for name in component_names)
        has_base = any("base" in name or "inferior" in name or "suelo" in name for name in component_names)
        has_trasera = any("trasera" in name or "tras" in name for name in component_names)
        
        assert has_lateral, f"Missing LATERAL component. Components: {component_names}"
        assert has_tapa, f"Missing TAPA/SUPERIOR component. Components: {component_names}"
        assert has_base, f"Missing BASE/INFERIOR component. Components: {component_names}"
        assert has_trasera, f"Missing TRASERA component. Components: {component_names}"
        
        print(f"✅ Despiece includes all standard components: {component_names}")


# ==========================================
# TEST: PORTAL FABRICA CRUD OPERATIONS
# ==========================================

class TestPortalFabricaCRUD:
    """Test Portal de Fábrica CRUD operations"""

    def test_create_manufacturing_order(self, api_session, cleanup_test_orders):
        """Test: Create a new manufacturing order"""
        payload = {
            "customerName": "TEST_Cliente Prueba",
            "customerCode": "TEST-CLI-001",
            "contactPhone": "600123456",
            "deliveryAddress": "Calle Test 123, Madrid",
            "priority": "normal",
            "items": [
                {
                    "productCode": "7B2P600",
                    "productName": "Bajo 2 puertas 60cm",
                    "quantity": 2,
                    "width": 60,
                    "height": 70,
                    "depth": 58,
                    "material": "Blanco",
                    "notes": "Test item"
                }
            ],
            "internalNotes": "Orden de prueba - TEST"
        }
        
        response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=payload)
        assert response.status_code == 200, f"Create order failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "order" in data
        
        order = data["order"]
        assert order.get("orderNumber", "").startswith("OF-")
        assert order.get("status") == "draft"
        assert order.get("customerName") == "TEST_Cliente Prueba"
        assert len(order.get("items", [])) == 1
        
        # Store for cleanup
        cleanup_test_orders.append(order.get("id"))
        
        print(f"✅ Created order: {order.get('orderNumber')}")
        return order

    def test_list_manufacturing_orders(self, api_session):
        """Test: List manufacturing orders"""
        response = api_session.get(f"{BASE_URL}/api/fabrica/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert "total" in data
        
        print(f"✅ Listed {data['total']} orders")

    def test_list_orders_with_status_filter(self, api_session):
        """Test: List orders with status filter"""
        response = api_session.get(f"{BASE_URL}/api/fabrica/orders?status=draft")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        
        # All orders should have status draft
        for order in data.get("orders", []):
            assert order.get("status") == "draft"
        
        print(f"✅ Filtered orders by status=draft: {len(data['orders'])} orders")

    def test_get_single_order(self, api_session, cleanup_test_orders):
        """Test: Get a single order by ID"""
        # First create an order
        create_payload = {
            "customerName": "TEST_Get Single Order",
            "items": [
                {"productCode": "TEST-001", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        assert create_response.status_code == 200
        
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Get the order
        response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("id") == order_id
        assert data.get("customerName") == "TEST_Get Single Order"
        
        print(f"✅ Retrieved order: {data.get('orderNumber')}")

    def test_update_manufacturing_order(self, api_session, cleanup_test_orders):
        """Test: Update a manufacturing order"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Update Order",
            "items": [
                {"productCode": "TEST-002", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Update the order
        update_payload = {
            "customerName": "TEST_Updated Customer Name",
            "priority": "high"
        }
        
        response = api_session.put(f"{BASE_URL}/api/fabrica/orders/{order_id}", json=update_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        assert data["order"]["customerName"] == "TEST_Updated Customer Name"
        assert data["order"]["priority"] == "high"
        
        print(f"✅ Updated order: {order_id}")

    def test_delete_manufacturing_order(self, api_session):
        """Test: Delete a manufacturing order"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Delete Order",
            "items": [
                {"productCode": "TEST-003", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        
        # Delete the order
        response = api_session.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        # Verify it's deleted
        get_response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.status_code == 404
        
        print(f"✅ Deleted order: {order_id}")


# ==========================================
# TEST: PORTAL FABRICA STATUS CHANGES
# ==========================================

class TestPortalFabricaStatus:
    """Test Portal de Fábrica status changes"""

    def test_change_order_status_to_confirmed(self, api_session, cleanup_test_orders):
        """Test: Change order status from draft to confirmed"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Status Change",
            "items": [
                {"productCode": "TEST-STATUS", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        assert order["status"] == "draft"
        
        # Change status to confirmed
        response = api_session.patch(f"{BASE_URL}/api/fabrica/orders/{order_id}/status?status=confirmed")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        # Verify status changed
        get_response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.json()["status"] == "confirmed"
        
        print(f"✅ Changed order status to confirmed")

    def test_change_order_status_to_in_production(self, api_session, cleanup_test_orders):
        """Test: Change order status to in_production"""
        # Create an order
        create_payload = {
            "customerName": "TEST_In Production",
            "items": [
                {"productCode": "TEST-PROD", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Change status to in_production
        response = api_session.patch(f"{BASE_URL}/api/fabrica/orders/{order_id}/status?status=in_production")
        assert response.status_code == 200
        
        get_response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.json()["status"] == "in_production"
        
        print(f"✅ Changed order status to in_production")

    def test_change_order_status_to_delivered(self, api_session, cleanup_test_orders):
        """Test: Change order status to delivered (should set actualDeliveryDate)"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Delivered",
            "items": [
                {"productCode": "TEST-DELIV", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Change status to delivered
        response = api_session.patch(f"{BASE_URL}/api/fabrica/orders/{order_id}/status?status=delivered")
        assert response.status_code == 200
        
        # Verify actualDeliveryDate is set
        get_response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        order_data = get_response.json()
        
        assert order_data["status"] == "delivered"
        assert order_data.get("actualDeliveryDate") is not None
        
        print(f"✅ Changed order status to delivered (actualDeliveryDate: {order_data.get('actualDeliveryDate')})")

    def test_invalid_status_returns_error(self, api_session, cleanup_test_orders):
        """Test: Invalid status should return 400 error"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Invalid Status",
            "items": [
                {"productCode": "TEST-INV", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Try invalid status
        response = api_session.patch(f"{BASE_URL}/api/fabrica/orders/{order_id}/status?status=invalid_status")
        assert response.status_code == 400
        
        print(f"✅ Invalid status correctly returns 400 error")


# ==========================================
# TEST: PORTAL FABRICA DELIVERY DATE
# ==========================================

class TestPortalFabricaDeliveryDate:
    """Test Portal de Fábrica delivery date setting"""

    def test_set_estimated_delivery_date(self, api_session, cleanup_test_orders):
        """Test: Set estimated delivery date for an order"""
        # Create an order
        create_payload = {
            "customerName": "TEST_Delivery Date",
            "items": [
                {"productCode": "TEST-DATE", "productName": "Test Product", "quantity": 1, "width": 60, "height": 70, "depth": 58}
            ]
        }
        
        create_response = api_session.post(f"{BASE_URL}/api/fabrica/orders", json=create_payload)
        order = create_response.json()["order"]
        order_id = order["id"]
        cleanup_test_orders.append(order_id)
        
        # Set delivery date
        delivery_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = api_session.patch(
            f"{BASE_URL}/api/fabrica/orders/{order_id}/delivery-date?estimated_date={delivery_date}&notes=Entrega%20programada"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        # Verify date is set
        get_response = api_session.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        order_data = get_response.json()
        
        assert order_data.get("estimatedDeliveryDate") == delivery_date
        
        print(f"✅ Set estimated delivery date: {delivery_date}")


# ==========================================
# TEST: PORTAL FABRICA DASHBOARD STATS
# ==========================================

class TestPortalFabricaDashboard:
    """Test Portal de Fábrica dashboard statistics"""

    def test_get_dashboard_stats(self, api_session):
        """Test: Get dashboard statistics"""
        response = api_session.get(f"{BASE_URL}/api/fabrica/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "byStatus" in data
        assert "byPriority" in data
        assert "pendingThisWeek" in data
        assert "piecesInProduction" in data
        assert "totalActive" in data
        
        print(f"✅ Dashboard stats retrieved successfully")
        print(f"   - By Status: {data['byStatus']}")
        print(f"   - Total Active: {data['totalActive']}")
        print(f"   - Pieces in Production: {data['piecesInProduction']}")


# ==========================================
# TEST: PDF IMPORT (MOCKED)
# ==========================================

class TestPortalFabricaPDFImport:
    """Test Portal de Fábrica PDF import (MOCKED)"""

    def test_import_pdf_returns_mocked_response(self, api_session):
        """Test: PDF import returns informative message (MOCKED)"""
        import base64
        
        # Create a simple test PDF-like content
        fake_pdf_content = b"%PDF-1.4 fake content"
        pdf_base64 = base64.b64encode(fake_pdf_content).decode('utf-8')
        
        payload = {
            "pdfBase64": pdf_base64,
            "fileName": "test_presupuesto.pdf"
        }
        
        response = api_session.post(f"{BASE_URL}/api/fabrica/import-pdf", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        assert "próximamente" in data.get("message", "").lower() or "recibido" in data.get("message", "").lower()
        
        print(f"✅ PDF import returns MOCKED response: {data.get('message')}")


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
