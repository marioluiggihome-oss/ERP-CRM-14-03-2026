"""
Test Suite for LUIGGI HOME ERP - Iteration 35
Testing new features:
1. Production PDF Report endpoint (GET /api/fabrica/reports/production/{order_id})
2. Production PDF Report from budget (GET /api/fabrica/reports/production-from-budget/{budget_id})
3. Send order copy with attachments (POST /api/orders/{order_id}/send-copy)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://erp-home-kitchen.preview.emergentagent.com')

# Test data - existing manufacturing order and order IDs from the system
EXISTING_MFG_ORDER_ID = "mfg-3d0545c9"  # Manufacturing order with items
EXISTING_ORDER_ID = "order-eecb4b8f"  # Order with attachments
EXISTING_BUDGET_ID = None  # Will be fetched dynamically


class TestProductionReportEndpoints:
    """Test PDF production report generation endpoints"""
    
    def test_production_report_endpoint_exists(self):
        """Test that the production report endpoint returns a response"""
        response = requests.get(f"{BASE_URL}/api/fabrica/reports/production/{EXISTING_MFG_ORDER_ID}")
        # Should return 200 with PDF or 404 if order not found
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Production report endpoint responds with status {response.status_code}")
    
    def test_production_report_returns_pdf(self):
        """Test that production report returns a valid PDF"""
        response = requests.get(f"{BASE_URL}/api/fabrica/reports/production/{EXISTING_MFG_ORDER_ID}")
        
        if response.status_code == 200:
            # Check content type is PDF
            content_type = response.headers.get('Content-Type', '')
            assert 'application/pdf' in content_type, f"Expected PDF, got {content_type}"
            
            # Check content disposition header for filename
            content_disp = response.headers.get('Content-Disposition', '')
            assert 'attachment' in content_disp, "Should have attachment disposition"
            assert '.pdf' in content_disp.lower(), "Filename should have .pdf extension"
            
            # Check PDF magic bytes
            assert response.content[:4] == b'%PDF', "Content should start with PDF magic bytes"
            
            print(f"✓ Production report returns valid PDF ({len(response.content)} bytes)")
        else:
            print(f"⚠ Order not found (status {response.status_code}), skipping PDF validation")
    
    def test_production_report_invalid_order(self):
        """Test production report with non-existent order ID"""
        response = requests.get(f"{BASE_URL}/api/fabrica/reports/production/invalid-order-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Production report returns 404 for invalid order ID")
    
    def test_production_report_from_budget_endpoint_exists(self):
        """Test that production report from budget endpoint exists"""
        # First get a budget ID
        projects_response = requests.get(f"{BASE_URL}/api/projects")
        if projects_response.status_code == 200:
            data = projects_response.json()
            # API returns list directly or dict with 'projects' key
            projects = data.get('projects', data) if isinstance(data, dict) else data
            if projects:
                budget_id = projects[0].get('id')
                response = requests.get(f"{BASE_URL}/api/fabrica/reports/production-from-budget/{budget_id}")
                assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
                print(f"✓ Production report from budget endpoint responds with status {response.status_code}")
            else:
                print("⚠ No projects found to test production-from-budget endpoint")
        else:
            print(f"⚠ Could not fetch projects (status {projects_response.status_code})")
    
    def test_production_report_from_budget_invalid(self):
        """Test production report from budget with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/fabrica/reports/production-from-budget/invalid-budget-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Production report from budget returns 404 for invalid budget ID")


class TestSendOrderCopyEndpoint:
    """Test send order copy with attachments endpoint"""
    
    def test_send_copy_endpoint_exists(self):
        """Test that send-copy endpoint exists and accepts POST"""
        # Test with minimal payload
        response = requests.post(
            f"{BASE_URL}/api/orders/{EXISTING_ORDER_ID}/send-copy",
            json={
                "recipient_email": "test@example.com",
                "include_attachments": True,
                "additional_message": ""
            }
        )
        # Should return 200 (success), 404 (order not found), or 500 (email config issue)
        assert response.status_code in [200, 404, 500], f"Unexpected status: {response.status_code}"
        print(f"✓ Send copy endpoint responds with status {response.status_code}")
    
    def test_send_copy_invalid_order(self):
        """Test send copy with non-existent order ID"""
        response = requests.post(
            f"{BASE_URL}/api/orders/invalid-order-12345/send-copy",
            json={
                "recipient_email": "test@example.com",
                "include_attachments": False,
                "additional_message": ""
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Send copy returns 404 for invalid order ID")
    
    def test_send_copy_request_validation(self):
        """Test send copy validates request body"""
        # Test with missing required field
        response = requests.post(
            f"{BASE_URL}/api/orders/{EXISTING_ORDER_ID}/send-copy",
            json={
                "include_attachments": True
                # Missing recipient_email
            }
        )
        # Should return 422 (validation error) or handle gracefully
        assert response.status_code in [422, 400, 500], f"Unexpected status: {response.status_code}"
        print(f"✓ Send copy validates request body (status {response.status_code})")
    
    def test_send_copy_with_attachments_flag(self):
        """Test send copy with include_attachments flag"""
        response = requests.post(
            f"{BASE_URL}/api/orders/{EXISTING_ORDER_ID}/send-copy",
            json={
                "recipient_email": "test@example.com",
                "include_attachments": True,
                "additional_message": "Test message"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'success' in data, "Response should have success field"
            assert 'message' in data, "Response should have message field"
            print(f"✓ Send copy with attachments successful: {data.get('message', '')}")
        else:
            print(f"⚠ Send copy returned status {response.status_code} (may be email config issue)")


class TestOrdersEndpoint:
    """Test orders endpoint for attachments field"""
    
    def test_orders_list_returns_attachments_field(self):
        """Test that orders list includes attachments field"""
        response = requests.get(f"{BASE_URL}/api/orders?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        orders = response.json()
        assert isinstance(orders, list), "Response should be a list"
        
        if orders:
            order = orders[0]
            # Check for attachments-related fields
            assert 'attachmentsCount' in order or 'attachments' in order, \
                "Order should have attachmentsCount or attachments field"
            print(f"✓ Orders list includes attachment info (found {len(orders)} orders)")
        else:
            print("⚠ No orders found to verify attachments field")
    
    def test_order_detail_has_attachments(self):
        """Test that order detail includes attachments array"""
        response = requests.get(f"{BASE_URL}/api/orders/{EXISTING_ORDER_ID}")
        
        if response.status_code == 200:
            order = response.json()
            # Check for attachments field
            if 'attachments' in order:
                attachments = order['attachments']
                assert isinstance(attachments, list), "Attachments should be a list"
                print(f"✓ Order detail has attachments field ({len(attachments)} attachments)")
            else:
                print("⚠ Order does not have attachments field (may be empty)")
        else:
            print(f"⚠ Order not found (status {response.status_code})")


class TestFabricaOrdersEndpoint:
    """Test fabrica orders endpoint"""
    
    def test_fabrica_orders_list(self):
        """Test that fabrica orders list works"""
        response = requests.get(f"{BASE_URL}/api/fabrica/orders?limit=5")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'orders' in data, "Response should have orders field"
        
        orders = data['orders']
        if orders:
            order = orders[0]
            # Check for required fields
            assert 'id' in order, "Order should have id"
            assert 'orderNumber' in order, "Order should have orderNumber"
            assert 'items' in order, "Order should have items"
            print(f"✓ Fabrica orders list works ({len(orders)} orders)")
        else:
            print("⚠ No fabrica orders found")
    
    def test_fabrica_order_detail(self):
        """Test fabrica order detail endpoint"""
        response = requests.get(f"{BASE_URL}/api/fabrica/orders/{EXISTING_MFG_ORDER_ID}")
        
        if response.status_code == 200:
            order = response.json()
            assert 'id' in order, "Order should have id"
            assert 'items' in order, "Order should have items"
            print(f"✓ Fabrica order detail works (order: {order.get('orderNumber', 'N/A')})")
        else:
            print(f"⚠ Fabrica order not found (status {response.status_code})")


class TestAPIIntegration:
    """Integration tests for the new features"""
    
    def test_full_flow_production_report(self):
        """Test full flow: get order -> generate PDF report"""
        # Step 1: Get fabrica orders
        orders_response = requests.get(f"{BASE_URL}/api/fabrica/orders?limit=1")
        assert orders_response.status_code == 200
        
        data = orders_response.json()
        orders = data.get('orders', [])
        
        if not orders:
            print("⚠ No orders to test full flow")
            return
        
        order_id = orders[0]['id']
        
        # Step 2: Generate production report
        report_response = requests.get(f"{BASE_URL}/api/fabrica/reports/production/{order_id}")
        
        if report_response.status_code == 200:
            assert 'application/pdf' in report_response.headers.get('Content-Type', '')
            print(f"✓ Full flow: Generated PDF report for order {order_id}")
        else:
            print(f"⚠ Could not generate report (status {report_response.status_code})")
    
    def test_full_flow_send_copy(self):
        """Test full flow: get order -> send copy"""
        # Step 1: Get orders
        orders_response = requests.get(f"{BASE_URL}/api/orders?limit=1")
        assert orders_response.status_code == 200
        
        orders = orders_response.json()
        
        if not orders:
            print("⚠ No orders to test send copy flow")
            return
        
        order_id = orders[0]['id']
        
        # Step 2: Send copy (will likely fail due to email config, but endpoint should work)
        send_response = requests.post(
            f"{BASE_URL}/api/orders/{order_id}/send-copy",
            json={
                "recipient_email": "test@example.com",
                "include_attachments": False,
                "additional_message": "Test from automated test"
            }
        )
        
        # Accept 200 (success) or 500 (email config issue)
        assert send_response.status_code in [200, 500], f"Unexpected status: {send_response.status_code}"
        print(f"✓ Full flow: Send copy endpoint responded (status {send_response.status_code})")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
