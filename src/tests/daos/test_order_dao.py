import os
import csv
import tempfile
import shutil
from datetime import datetime
import pytest
from models import Order, OrderType
from daos.order_dao import FIELD_NAMES, write_orders


class TestOrderDao:
    def test_field_names_match_order_attributes(self):
        """Test that FIELD_NAMES matches the attributes from Order.asdict()"""
        order = Order(
            asset_id=12345,
            market_slug="test-market",
            order_type=OrderType.LIMIT_BUY,
            price=0.45,
            size=100.0,
            timestamp=1234567890
        )
        
        order_fields = set(order.asdict().keys())
        expected_fields = set(FIELD_NAMES)
        
        assert order_fields == expected_fields, f"Order fields {order_fields} don't match FIELD_NAMES {expected_fields}"
    
    def test_write_orders_validates_field_mismatch(self, monkeypatch):
        # This test verifies that the exception handling works
        # by creating a mock order with wrong fields
        
        class BadOrder:
            def asdict(self):
                return {
                    'asset_id': 12345,
                    'market_slug': 'test',
                    'wrong_field': 'value',  # This field is not in FIELD_NAMES
                    'price': 0.5,
                    'size': 100,
                    'timestamp': 123456
                }
        
        bad_orders = [BadOrder()]
        
        with pytest.raises(ValueError) as exc_info:
            write_orders("test-market", datetime.now(), bad_orders, test_mode=True)
        
        assert "Order fields mismatch" in str(exc_info.value)
        assert "Missing: {'order_type'}" in str(exc_info.value)
        assert "Extra: {'wrong_field'}" in str(exc_info.value)