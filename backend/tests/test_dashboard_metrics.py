# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Test Dashboard Metrics API - LUIGGI HOME
Tests for GET /api/dashboard/metrics endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://erp-home-kitchen.preview.emergentagent.com')

class TestDashboardMetrics:
    """Dashboard metrics endpoint tests"""
    
    def test_dashboard_metrics_default_period(self):
        """Test GET /api/dashboard/metrics with default period (month)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "period" in data, "Response should contain 'period'"
        assert "generatedAt" in data, "Response should contain 'generatedAt'"
        assert "kpis" in data, "Response should contain 'kpis'"
        assert "production" in data, "Response should contain 'production'"
        assert "sales" in data, "Response should contain 'sales'"
        assert "budgets" in data, "Response should contain 'budgets'"
        assert "clients" in data, "Response should contain 'clients'"
        assert "products" in data, "Response should contain 'products'"
        assert "monthlyTrend" in data, "Response should contain 'monthlyTrend'"
        
        print(f"✅ Dashboard metrics default period test passed")
    
    def test_dashboard_metrics_week_period(self):
        """Test GET /api/dashboard/metrics?period=week"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=week")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week", f"Expected period 'week', got '{data['period']}'"
        print(f"✅ Dashboard metrics week period test passed")
    
    def test_dashboard_metrics_month_period(self):
        """Test GET /api/dashboard/metrics?period=month"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "month", f"Expected period 'month', got '{data['period']}'"
        print(f"✅ Dashboard metrics month period test passed")
    
    def test_dashboard_metrics_quarter_period(self):
        """Test GET /api/dashboard/metrics?period=quarter"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=quarter")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "quarter", f"Expected period 'quarter', got '{data['period']}'"
        print(f"✅ Dashboard metrics quarter period test passed")
    
    def test_dashboard_metrics_year_period(self):
        """Test GET /api/dashboard/metrics?period=year"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=year")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "year", f"Expected period 'year', got '{data['period']}'"
        print(f"✅ Dashboard metrics year period test passed")
    
    def test_dashboard_metrics_all_period(self):
        """Test GET /api/dashboard/metrics?period=all"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "all", f"Expected period 'all', got '{data['period']}'"
        print(f"✅ Dashboard metrics all period test passed")
    
    def test_dashboard_kpis_structure(self):
        """Test KPIs structure in dashboard metrics"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        kpis = data.get("kpis", {})
        
        # Verify KPIs fields
        expected_kpi_fields = [
            "totalFabOrders",
            "totalConfirmedOrders",
            "totalBudgets",
            "totalSalesValue",
            "totalBudgetValue",
            "totalPiecesInProduction",
            "conversionRate"
        ]
        
        for field in expected_kpi_fields:
            assert field in kpis, f"KPIs should contain '{field}'"
        
        # Verify types
        assert isinstance(kpis["totalFabOrders"], int), "totalFabOrders should be int"
        assert isinstance(kpis["totalConfirmedOrders"], int), "totalConfirmedOrders should be int"
        assert isinstance(kpis["totalBudgets"], int), "totalBudgets should be int"
        assert isinstance(kpis["totalSalesValue"], (int, float)), "totalSalesValue should be numeric"
        assert isinstance(kpis["totalBudgetValue"], (int, float)), "totalBudgetValue should be numeric"
        assert isinstance(kpis["totalPiecesInProduction"], int), "totalPiecesInProduction should be int"
        assert isinstance(kpis["conversionRate"], (int, float)), "conversionRate should be numeric"
        
        print(f"✅ Dashboard KPIs structure test passed")
        print(f"   - totalFabOrders: {kpis['totalFabOrders']}")
        print(f"   - totalConfirmedOrders: {kpis['totalConfirmedOrders']}")
        print(f"   - totalBudgets: {kpis['totalBudgets']}")
        print(f"   - totalSalesValue: {kpis['totalSalesValue']}€")
        print(f"   - conversionRate: {kpis['conversionRate']}%")
    
    def test_dashboard_production_structure(self):
        """Test production metrics structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        production = data.get("production", {})
        
        # Verify production fields
        assert "byStatus" in production, "Production should contain 'byStatus'"
        assert "byPriority" in production, "Production should contain 'byPriority'"
        assert "byFactory" in production, "Production should contain 'byFactory'"
        assert "pendingOrders" in production, "Production should contain 'pendingOrders'"
        
        # Verify byStatus structure
        by_status = production.get("byStatus", {})
        expected_statuses = ["draft", "confirmed", "in_production", "ready", "delivered", "cancelled"]
        for status in expected_statuses:
            assert status in by_status, f"byStatus should contain '{status}'"
        
        # Verify byPriority structure
        by_priority = production.get("byPriority", {})
        expected_priorities = ["low", "normal", "high", "urgent"]
        for priority in expected_priorities:
            assert priority in by_priority, f"byPriority should contain '{priority}'"
        
        print(f"✅ Dashboard production structure test passed")
    
    def test_dashboard_sales_structure(self):
        """Test sales metrics structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        sales = data.get("sales", {})
        
        # Verify sales fields
        assert "ordersByStatus" in sales, "Sales should contain 'ordersByStatus'"
        assert "recentOrders" in sales, "Sales should contain 'recentOrders'"
        
        # Verify ordersByStatus structure
        orders_by_status = sales.get("ordersByStatus", {})
        expected_statuses = ["confirmed", "in_production", "delivered"]
        for status in expected_statuses:
            assert status in orders_by_status, f"ordersByStatus should contain '{status}'"
        
        # Verify recentOrders is a list
        assert isinstance(sales["recentOrders"], list), "recentOrders should be a list"
        
        print(f"✅ Dashboard sales structure test passed")
        print(f"   - recentOrders count: {len(sales['recentOrders'])}")
    
    def test_dashboard_clients_structure(self):
        """Test clients metrics structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        clients = data.get("clients", {})
        
        # Verify clients fields
        assert "total" in clients, "Clients should contain 'total'"
        assert "active" in clients, "Clients should contain 'active'"
        assert "potential" in clients, "Clients should contain 'potential'"
        
        # Verify types
        assert isinstance(clients["total"], int), "total should be int"
        assert isinstance(clients["active"], int), "active should be int"
        assert isinstance(clients["potential"], int), "potential should be int"
        
        print(f"✅ Dashboard clients structure test passed")
        print(f"   - total: {clients['total']}")
        print(f"   - active: {clients['active']}")
        print(f"   - potential: {clients['potential']}")
    
    def test_dashboard_products_structure(self):
        """Test products metrics structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", {})
        
        # Verify products fields
        assert "total" in products, "Products should contain 'total'"
        assert "zc" in products, "Products should contain 'zc'"
        assert "mv" in products, "Products should contain 'mv'"
        
        # Verify types
        assert isinstance(products["total"], int), "total should be int"
        assert isinstance(products["zc"], int), "zc should be int"
        assert isinstance(products["mv"], int), "mv should be int"
        
        print(f"✅ Dashboard products structure test passed")
        print(f"   - total: {products['total']}")
        print(f"   - ZC: {products['zc']}")
        print(f"   - MV: {products['mv']}")
    
    def test_dashboard_monthly_trend_structure(self):
        """Test monthly trend structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        monthly_trend = data.get("monthlyTrend", [])
        
        # Verify monthlyTrend is a list
        assert isinstance(monthly_trend, list), "monthlyTrend should be a list"
        
        # Should have 6 months of data
        assert len(monthly_trend) == 6, f"monthlyTrend should have 6 entries, got {len(monthly_trend)}"
        
        # Verify each entry structure
        for entry in monthly_trend:
            assert "month" in entry, "Each trend entry should have 'month'"
            assert "name" in entry, "Each trend entry should have 'name'"
            assert "pedidos" in entry, "Each trend entry should have 'pedidos'"
            assert "presupuestos" in entry, "Each trend entry should have 'presupuestos'"
        
        print(f"✅ Dashboard monthly trend structure test passed")
        print(f"   - Months: {[e['name'] for e in monthly_trend]}")
    
    def test_dashboard_budgets_structure(self):
        """Test budgets metrics structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/metrics?period=month")
        
        assert response.status_code == 200
        data = response.json()
        budgets = data.get("budgets", {})
        
        # Verify budgets fields
        assert "byStatus" in budgets, "Budgets should contain 'byStatus'"
        assert "avgValue" in budgets, "Budgets should contain 'avgValue'"
        
        # Verify byStatus structure
        by_status = budgets.get("byStatus", {})
        expected_statuses = ["draft", "sent", "accepted", "rejected", "completed"]
        for status in expected_statuses:
            assert status in by_status, f"byStatus should contain '{status}'"
        
        print(f"✅ Dashboard budgets structure test passed")


class TestProductionSummary:
    """Production summary endpoint tests"""
    
    def test_production_summary(self):
        """Test GET /api/dashboard/production-summary"""
        response = requests.get(f"{BASE_URL}/api/dashboard/production-summary")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "pendingProduction" in data, "Response should contain 'pendingProduction'"
        assert "completedThisWeek" in data, "Response should contain 'completedThisWeek'"
        assert "urgentOrders" in data, "Response should contain 'urgentOrders'"
        
        # Verify types
        assert isinstance(data["pendingProduction"], int), "pendingProduction should be int"
        assert isinstance(data["completedThisWeek"], int), "completedThisWeek should be int"
        assert isinstance(data["urgentOrders"], int), "urgentOrders should be int"
        
        print(f"✅ Production summary test passed")
        print(f"   - pendingProduction: {data['pendingProduction']}")
        print(f"   - completedThisWeek: {data['completedThisWeek']}")
        print(f"   - urgentOrders: {data['urgentOrders']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
