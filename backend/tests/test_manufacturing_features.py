# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test Manufacturing Features for LUIGGI HOME
Tests:
1. Manufacturing number generation in factory orders
2. Factory orders CRUD operations
3. Despiece calculation endpoint
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestManufacturingNumber:
    """Test manufacturing number generation in factory orders"""
    
    def test_create_order_generates_manufacturing_number(self):
        """Test that creating a factory order generates a sequential manufacturing number"""
        # Create a new manufacturing order
        order_data = {
            "customerName": "TEST_MFG_Customer",
            "customerCode": "TEST-MFG-001",
            "contactPhone": "600123456",
            "deliveryAddress": "Test Address",
            "priority": "normal",
            "items": [
                {
                    "productCode": "B60",
                    "productName": "BAJO 60 2P",
                    "quantity": 1,
                    "width": 60,
                    "height": 70,
                    "depth": 58
                }
            ],
            "internalNotes": "Test order for manufacturing number"
        }
        
        response = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Order creation should succeed"
        assert "order" in data, "Response should contain order"
        
        order = data["order"]
        
        # Verify manufacturing number is present
        assert "manufacturingNumber" in order, "Order should have manufacturingNumber field"
        assert order["manufacturingNumber"] is not None, "manufacturingNumber should not be None"
        assert isinstance(order["manufacturingNumber"], int), "manufacturingNumber should be an integer"
        assert order["manufacturingNumber"] > 0, "manufacturingNumber should be positive"
        
        # Verify order number is also present
        assert "orderNumber" in order, "Order should have orderNumber field"
        assert order["orderNumber"].startswith("OF-"), "orderNumber should start with OF-"
        
        print(f"✓ Order created with manufacturingNumber: {order['manufacturingNumber']}, orderNumber: {order['orderNumber']}")
        
        # Store order ID for cleanup
        self.created_order_id = order["id"]
        return order
    
    def test_manufacturing_number_is_sequential(self):
        """Test that manufacturing numbers are sequential across orders"""
        # Create first order
        order_data = {
            "customerName": "TEST_SEQ_Customer1",
            "customerCode": "TEST-SEQ-001",
            "priority": "normal",
            "items": [{"productCode": "A60", "productName": "ALTO 60", "quantity": 1, "width": 60, "height": 90, "depth": 33}]
        }
        
        response1 = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert response1.status_code == 200
        order1 = response1.json()["order"]
        mfg_num1 = order1["manufacturingNumber"]
        
        # Create second order
        order_data["customerName"] = "TEST_SEQ_Customer2"
        order_data["customerCode"] = "TEST-SEQ-002"
        
        response2 = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert response2.status_code == 200
        order2 = response2.json()["order"]
        mfg_num2 = order2["manufacturingNumber"]
        
        # Verify sequential
        assert mfg_num2 == mfg_num1 + 1, f"Manufacturing numbers should be sequential: {mfg_num1} -> {mfg_num2}"
        
        print(f"✓ Manufacturing numbers are sequential: {mfg_num1} -> {mfg_num2}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/fabrica/orders/{order1['id']}")
        requests.delete(f"{BASE_URL}/api/fabrica/orders/{order2['id']}")
    
    def test_get_order_includes_manufacturing_number(self):
        """Test that GET order endpoint returns manufacturing number"""
        # Create order first
        order_data = {
            "customerName": "TEST_GET_Customer",
            "customerCode": "TEST-GET-001",
            "priority": "normal",
            "items": [{"productCode": "B45", "productName": "BAJO 45", "quantity": 1, "width": 45, "height": 70, "depth": 58}]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert create_response.status_code == 200
        created_order = create_response.json()["order"]
        order_id = created_order["id"]
        
        # GET the order
        get_response = requests.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.status_code == 200
        
        fetched_order = get_response.json()
        assert "manufacturingNumber" in fetched_order, "Fetched order should have manufacturingNumber"
        assert fetched_order["manufacturingNumber"] == created_order["manufacturingNumber"], "Manufacturing number should match"
        
        print(f"✓ GET order returns manufacturingNumber: {fetched_order['manufacturingNumber']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")
    
    def test_list_orders_includes_manufacturing_number(self):
        """Test that list orders endpoint returns manufacturing numbers"""
        response = requests.get(f"{BASE_URL}/api/fabrica/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data, "Response should contain orders array"
        
        # Check if any orders exist and have manufacturing numbers
        if data["orders"]:
            for order in data["orders"][:3]:  # Check first 3 orders
                if "manufacturingNumber" in order:
                    print(f"✓ Order {order.get('orderNumber')} has manufacturingNumber: {order['manufacturingNumber']}")
        
        print(f"✓ List orders endpoint working, total: {data.get('total', len(data['orders']))}")


class TestDespieceCalculation:
    """Test despiece calculation endpoint"""
    
    def test_despiece_endpoint_exists(self):
        """Test that despiece calculation endpoint exists"""
        # Create a test order first
        order_data = {
            "customerName": "TEST_DESPIECE_Customer",
            "customerCode": "TEST-DSP-001",
            "priority": "normal",
            "items": [
                {"productCode": "B60", "productName": "BAJO 60 2P", "quantity": 2, "width": 60, "height": 70, "depth": 58},
                {"productCode": "A60", "productName": "ALTO 60 2P", "quantity": 1, "width": 60, "height": 90, "depth": 33}
            ]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert create_response.status_code == 200
        order_id = create_response.json()["order"]["id"]
        
        # Get despiece for the order
        despiece_response = requests.get(f"{BASE_URL}/api/fabrica/orders/{order_id}/despiece")

        assert despiece_response.status_code == 200, (
            f"Despiece endpoint failed with status {despiece_response.status_code}: "
            f"{despiece_response.text}"
        )
        data = despiece_response.json()
        assert "orderId" in data, "Despiece should have orderId"
        assert "items" in data, "Despiece should have items"
        print(f"✓ Despiece calculation working for order {order_id}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")


class TestFactoryOrdersCRUD:
    """Test factory orders CRUD operations"""
    
    def test_create_order(self):
        """Test creating a factory order"""
        order_data = {
            "customerName": "TEST_CRUD_Customer",
            "customerCode": "TEST-CRUD-001",
            "contactPhone": "600111222",
            "deliveryAddress": "Calle Test 123",
            "priority": "high",
            "items": [
                {"productCode": "CH180", "productName": "COLUMNA HORNO 180", "quantity": 1, "width": 60, "height": 180, "depth": 58}
            ],
            "internalNotes": "CRUD test order"
        }
        
        response = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "order" in data
        
        order = data["order"]
        assert order["customerName"] == "TEST_CRUD_Customer"
        assert order["priority"] == "high"
        assert len(order["items"]) == 1
        assert order["status"] == "draft"
        
        print(f"✓ Order created: {order['orderNumber']}")
        
        # Store for cleanup
        self.test_order_id = order["id"]
        return order
    
    def test_update_order_status(self):
        """Test updating order status"""
        # Create order first
        order = self.test_create_order()
        order_id = order["id"]
        
        # Update status to confirmed
        response = requests.patch(
            f"{BASE_URL}/api/fabrica/orders/{order_id}/status",
            params={"status": "confirmed"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        
        # Verify status changed
        get_response = requests.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "confirmed"
        
        print(f"✓ Order status updated to confirmed")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")
    
    def test_delete_order(self):
        """Test deleting a factory order"""
        # Create order first
        order_data = {
            "customerName": "TEST_DELETE_Customer",
            "priority": "normal",
            "items": [{"productCode": "B30", "productName": "BAJO 30", "quantity": 1, "width": 30, "height": 70, "depth": 58}]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/fabrica/orders", json=order_data)
        assert create_response.status_code == 200
        order_id = create_response.json()["order"]["id"]
        
        # Delete the order
        delete_response = requests.delete(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = requests.get(f"{BASE_URL}/api/fabrica/orders/{order_id}")
        assert get_response.status_code == 404
        
        print(f"✓ Order deleted successfully")


class TestDashboardStats:
    """Test factory dashboard statistics"""
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/fabrica/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify expected fields
        assert "byStatus" in data, "Should have byStatus"
        assert "byPriority" in data, "Should have byPriority"
        assert "totalActive" in data, "Should have totalActive"
        
        print(f"✓ Dashboard stats: totalActive={data.get('totalActive')}, byStatus={data.get('byStatus')}")


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_orders():
    """Cleanup test orders after tests"""
    yield
    # Cleanup any remaining test orders
    try:
        response = requests.get(f"{BASE_URL}/api/fabrica/orders?search=TEST_")
        if response.status_code == 200:
            orders = response.json().get("orders", [])
            for order in orders:
                if order.get("customerName", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/fabrica/orders/{order['id']}")
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
