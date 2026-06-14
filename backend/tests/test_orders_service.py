"""
Ejemplo de pruebas unitarias para el servicio de pedidos.
Demuestra cómo testear la lógica de negocio de forma aislada.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from models import OrderConfirmRequest, OrderItemRequest
from orders_service import OrderService
from error_handler import ValidationError, DatabaseError


class TestOrderService:
    \"\"\"Suite de pruebas para OrderService\"\"\"

    @pytest.fixture
    def mock_db(self):
        \"\"\"Mock de la base de datos\"\"\"
        db = MagicMock()
        db.orders = AsyncMock()
        db.manufacturing_orders = AsyncMock()
        db.counters = AsyncMock()
        return db

    @pytest.fixture
    def order_service(self, mock_db):
        \"\"\"Instancia del servicio con BD mockeada\"\"\"
        return OrderService(mock_db)

    @pytest.fixture
    def sample_order_data(self):
        \"\"\"Datos de ejemplo para un pedido\"\"\"
        return OrderConfirmRequest(
            budgetNumber=\"PRESUP-001\",
            customerName=\"Cliente Test\",
            customerAddress=\"Calle Test 123\",
            totalAmount=1500.00,
            email=\"cliente@test.com\",
            notes=\"Pedido de prueba\",
            items=[\n                OrderItemRequest(\n                    name=\"Puerta Cocina\",\n                    code=\"PUERTA-001\",\n                    quantity=2,\n                    price=500.00,\n                    width=60,\n                    height=70\n                )\n            ]\n        )

    @pytest.mark.asyncio
    async def test_confirm_order_success(self, order_service, mock_db, sample_order_data):\n        \"\"\"Prueba exitosa de confirmación de pedido\"\"\"\n        # Arrange\n        mock_db.orders.find_one.return_value = None  # No existe pedido duplicado\n        mock_db.orders.insert_one.return_value = MagicMock(inserted_id=\"order-123\")\n        mock_db.counters.find_one_and_update.return_value = {\"seq\": 1}\n        mock_db.manufacturing_orders.insert_one.return_value = MagicMock(inserted_id=\"mfg-456\")\n        mock_db.client.start_session.return_value.__aenter__.return_value = MagicMock()\n        mock_db.client.start_session.return_value.__aexit__.return_value = None\n\n        # Act\n        result = await order_service.confirm_order_atomic(sample_order_data)\n\n        # Assert\n        assert result[\"success\"] is True\n        assert result[\"order_id\"] == \"order-123\"\n        assert result[\"budgetNumber\"] == \"PRESUP-001\"\n        assert result[\"manufacturing_order_id\"] == \"mfg-456\"\n        mock_db.orders.insert_one.assert_called_once()\n        mock_db.manufacturing_orders.insert_one.assert_called_once()\n\n    @pytest.mark.asyncio\n    async def test_confirm_order_duplicate_budget(self, order_service, mock_db, sample_order_data):\n        \"\"\"Prueba de rechazo de presupuesto duplicado\"\"\"\n        # Arrange\n        mock_db.orders.find_one.return_value = {\"_id\": \"existing-order\"}  # Existe\n\n        # Act & Assert\n        with pytest.raises(ValidationError) as exc_info:\n            await order_service.confirm_order_atomic(sample_order_data)\n        \n        assert \"Ya existe un pedido\" in str(exc_info.value)\n\n    @pytest.mark.asyncio\n    async def test_prepare_order_record(self, order_service, sample_order_data):\n        \"\"\"Prueba de preparación del registro de pedido\"\"\"\n        # Act\n        record = order_service._prepare_order_record(sample_order_data)\n\n        # Assert\n        assert record[\"budgetNumber\"] == \"PRESUP-001\"\n        assert record[\"customerName\"] == \"Cliente Test\"\n        assert record[\"totalAmount\"] == 1500.00\n        assert record[\"itemsCount\"] == 1\n        assert record[\"status\"] == \"confirmed\"\n        assert \"confirmedAt\" in record\n        assert \"id\" in record\n\n    @pytest.mark.asyncio\n    async def test_prepare_order_record_with_attachments(self, order_service, sample_order_data):\n        \"\"\"Prueba de preparación con archivos adjuntos\"\"\"\n        # Arrange\n        attachments = [\n            {\n                \"filename\": \"plano.pdf\",\n                \"content_type\": \"application/pdf\",\n                \"encoded\": \"base64encodedcontent\"\n            }\n        ]\n\n        # Act\n        record = order_service._prepare_order_record(sample_order_data, attachments)\n\n        # Assert\n        assert record[\"attachmentsCount\"] == 1\n        assert len(record[\"attachments\"]) == 1\n        assert record[\"attachments\"][0][\"filename\"] == \"plano.pdf\"\n\n    @pytest.mark.asyncio\n    async def test_prepare_manufacturing_order(self, order_service, sample_order_data):\n        \"\"\"Prueba de preparación de orden de fabricación\"\"\"\n        # Arrange\n        mock_db = MagicMock()\n        mock_db.counters = AsyncMock()\n        mock_db.counters.find_one_and_update.side_effect = [\n            {\"seq\": 1},  # manufacturing_order_{year}\n            {\"seq\": 100}  # manufacturing_number_global\n        ]\n        order_service.db = mock_db\n\n        # Act\n        mfg_order = await order_service._prepare_manufacturing_order(sample_order_data)\n\n        # Assert\n        assert mfg_order[\"budgetNumber\"] == \"PRESUP-001\"\n        assert mfg_order[\"customerName\"] == \"Cliente Test\"\n        assert \"manufacturingNumber\" in mfg_order\n        assert mfg_order[\"totalPieces\"] == 2  # quantity del item\n        assert mfg_order[\"status\"] == \"pending\"\n\n    @pytest.mark.asyncio\n    async def test_update_order_email_status(self, order_service, mock_db):\n        \"\"\"Prueba de actualización de estado de email\"\"\"\n        # Arrange\n        mock_db.orders.update_one.return_value = MagicMock(matched_count=1)\n\n        # Act\n        result = await order_service.update_order_email_status(\n            \"order-123\",\n            email_sent=True,\n            email_provider=\"SendGrid\"\n        )\n\n        # Assert\n        assert result is True\n        mock_db.orders.update_one.assert_called_once()\n\n    @pytest.mark.asyncio\n    async def test_update_order_email_status_not_found(self, order_service, mock_db):\n        \"\"\"Prueba de actualización cuando el pedido no existe\"\"\"\n        # Arrange\n        mock_db.orders.update_one.return_value = MagicMock(matched_count=0)\n\n        # Act\n        result = await order_service.update_order_email_status(\n            \"nonexistent-order\",\n            email_sent=True\n        )\n\n        # Assert\n        assert result is False\n\n\nclass TestOrderModels:\n    \"\"\"Pruebas de validación de modelos Pydantic\"\"\"\n\n    def test_order_confirm_request_valid(self):\n        \"\"\"Prueba de validación exitosa\"\"\"\n        data = {\n            \"budgetNumber\": \"PRESUP-001\",\n            \"customerName\": \"Cliente Test\",\n            \"totalAmount\": 1500.00,\n            \"email\": \"cliente@test.com\",\n            \"items\": []\n        }\n        order = OrderConfirmRequest(**data)\n        assert order.budgetNumber == \"PRESUP-001\"\n\n    def test_order_confirm_request_invalid_email(self):\n        \"\"\"Prueba de rechazo de email inválido\"\"\"\n        data = {\n            \"budgetNumber\": \"PRESUP-001\",\n            \"customerName\": \"Cliente Test\",\n            \"totalAmount\": 1500.00,\n            \"email\": \"invalid-email\",\n            \"items\": []\n        }\n        with pytest.raises(ValueError):\n            OrderConfirmRequest(**data)\n\n    def test_order_confirm_request_negative_amount(self):\n        \"\"\"Prueba de rechazo de monto negativo\"\"\"\n        data = {\n            \"budgetNumber\": \"PRESUP-001\",\n            \"customerName\": \"Cliente Test\",\n            \"totalAmount\": -100.00,\n            \"email\": \"cliente@test.com\",\n            \"items\": []\n        }\n        with pytest.raises(ValueError):\n            OrderConfirmRequest(**data)\n\n    def test_order_item_quantity_validation(self):\n        \"\"\"Prueba de validación de cantidad\"\"\"\n        # Válido\n        item = OrderItemRequest(name=\"Test\", quantity=5)\n        assert item.quantity == 5\n\n        # Inválido (cantidad negativa)\n        with pytest.raises(ValueError):\n            OrderItemRequest(name=\"Test\", quantity=-1)\n\n        # Inválido (cantidad excesiva)\n        with pytest.raises(ValueError):\n            OrderItemRequest(name=\"Test\", quantity=50000)\n\n\nif __name__ == \"__main__\":\n    pytest.main([__file__, \"-v\", \"--tb=short\"])\n
