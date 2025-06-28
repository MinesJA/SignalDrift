from unittest.mock import patch

import pytest

from src.models.synthetic_orderbook import SyntheticOrder, SyntheticOrderBook


class TestSyntheticOrderBook:

    @pytest.fixture
    def orderbook(self):
        """Create a SyntheticOrderBook instance for testing."""
        return SyntheticOrderBook(
            market_slug="test-market",
            market_id="test-id-123",
            outcome_name="YES",
            asset_id="asset-456"
        )

    def test_init(self):
        """Test the initialization of SyntheticOrderBook."""
        ob = SyntheticOrderBook(
            market_slug="test-market",
            market_id="test-id-123",
            outcome_name="YES",
            asset_id="asset-456"
        )

        assert ob.market_slug == "test-market"
        assert ob.market_id == "test-id-123"
        assert ob.outcome_name == "YES"
        assert ob.asset_id == "asset-456"
        assert ob.orders_lookup == {}
        assert ob.orders == []

    def test_orders_property(self, orderbook):
        """Test the orders property returns list of orders."""
        # Add some orders manually
        orderbook.orders_lookup = {
            "0.5": SyntheticOrder(side="ask", price=0.5, size=100.0, timestamp=1000),
            "0.6": SyntheticOrder(side="ask", price=0.6, size=200.0, timestamp=1000)
        }

        orders = orderbook.orders
        assert len(orders) == 2
        assert all(isinstance(order, SyntheticOrder) for order in orders)
        assert {order.price for order in orders} == {0.5, 0.6}

    @patch('src.models.synthetic_orderbook.datetime')
    def test_add_entries_new_orders(self, mock_datetime, orderbook):
        """Test adding new orders to the orderbook."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        orders = [
            {"side": "SELL", "price": "0.5", "size": "100"},
            {"side": "SELL", "price": "0.6", "size": "200"}
        ]

        orderbook.add_entries(orders, timestamp=1234567890)

        assert len(orderbook.orders_lookup) == 2
        assert "0.5" in orderbook.orders_lookup
        assert "0.6" in orderbook.orders_lookup

        order1 = orderbook.orders_lookup["0.5"]
        assert order1.side == "ask"
        assert order1.price == 0.5
        assert order1.size == 100.0
        assert order1.timestamp == 1234567890

        order2 = orderbook.orders_lookup["0.6"]
        assert order2.side == "ask"
        assert order2.price == 0.6
        assert order2.size == 200.0
        assert order2.timestamp == 1234567890

    @patch('src.models.synthetic_orderbook.datetime')
    def test_add_entries_update_existing(self, mock_datetime, orderbook):
        """Test updating existing orders in the orderbook."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        # Add initial order
        orderbook.add_entries([{"side": "SELL", "price": "0.5", "size": "100"}], timestamp=1234567890)

        # Update with new size
        mock_datetime.now().timestamp.return_value = 1234568.890
        orderbook.add_entries([{"side": "SELL", "price": "0.5", "size": "150"}], timestamp=1234568890)

        assert len(orderbook.orders_lookup) == 1
        order = orderbook.orders_lookup["0.5"]
        assert order.size == 150.0
        assert order.timestamp == 1234568890

    @patch('src.models.synthetic_orderbook.datetime')
    def test_add_entries_remove_zero_size(self, mock_datetime, orderbook):
        """Test that orders with size 0 are removed from the orderbook."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        # Add initial orders
        orderbook.add_entries([
            {"side": "SELL", "price": "0.5", "size": "100"},
            {"side": "SELL", "price": "0.6", "size": "200"}
        ], timestamp=1234567890)

        assert len(orderbook.orders_lookup) == 2

        # Remove order by setting size to 0
        orderbook.add_entries([{"side": "SELL", "price": "0.5", "size": "0"}], timestamp=1234567890)

        assert len(orderbook.orders_lookup) == 1
        assert "0.5" not in orderbook.orders_lookup
        assert "0.6" in orderbook.orders_lookup

    @patch('src.models.synthetic_orderbook.datetime')
    def test_add_entries_non_sell_orders(self, mock_datetime, orderbook):
        """Test that non-SELL orders are ignored."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        orders = [
            {"side": "BUY", "price": "0.5", "size": "100"},
            {"side": "SELL", "price": "0.6", "size": "200"}
        ]

        orderbook.add_entries(orders, timestamp=1234567890)

        # Only SELL order should be added
        assert len(orderbook.orders_lookup) == 1
        assert "0.6" in orderbook.orders_lookup
        assert "0.5" not in orderbook.orders_lookup

    @patch('src.models.synthetic_orderbook.datetime')
    def test_replace_entries(self, mock_datetime, orderbook):
        """Test replacing all entries in the orderbook."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        # Add initial orders
        orderbook.add_entries([
            {"side": "SELL", "price": "0.5", "size": "100"},
            {"side": "SELL", "price": "0.6", "size": "200"}
        ], timestamp=1234567890)

        # Replace with new orders
        new_orders = [
            {"price": "0.7", "size": "300"},
            {"price": "0.8", "size": "400"}
        ]

        orderbook.replace_entries(new_orders, timestamp=1234567890)

        assert len(orderbook.orders_lookup) == 2
        assert "0.5" not in orderbook.orders_lookup
        assert "0.6" not in orderbook.orders_lookup
        assert "0.7" in orderbook.orders_lookup
        assert "0.8" in orderbook.orders_lookup

        order1 = orderbook.orders_lookup["0.7"]
        assert order1.side == "ask"
        assert order1.price == 0.7
        assert order1.size == 300.0
        assert order1.timestamp == 1234567890

    @patch('src.models.synthetic_orderbook.datetime')
    def test_replace_entries_filters_small_sizes(self, mock_datetime, orderbook):
        """Test that replace_entries filters out orders with size <= 0."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        orders = [
            {"price": "0.5", "size": "0"},
            {"price": "0.6", "size": "0.0"},
            {"price": "0.7", "size": "1.1"},
            {"price": "0.8", "size": "100"}
        ]

        orderbook.replace_entries(orders, timestamp=1234567890)

        # Only orders with size > 0 should be kept
        assert len(orderbook.orders_lookup) == 2
        assert "0.7" in orderbook.orders_lookup
        assert "0.8" in orderbook.orders_lookup
        assert "0.5" not in orderbook.orders_lookup
        assert "0.6" not in orderbook.orders_lookup

    @patch('src.models.synthetic_orderbook.datetime')
    def test_to_orders_dicts(self, mock_datetime, orderbook):
        """Test converting orders to dictionary format."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        # Add orders in non-sorted order
        orderbook.add_entries([
            {"side": "SELL", "price": "0.8", "size": "400"},
            {"side": "SELL", "price": "0.5", "size": "100"},
            {"side": "SELL", "price": "0.6", "size": "200"}
        ], timestamp=1234567890)

        result = orderbook.to_orders_dicts()

        assert len(result) == 3

        # Check that orders are sorted by price
        assert result[0]["price"] == 0.5
        assert result[1]["price"] == 0.6
        assert result[2]["price"] == 0.8

        # Check all fields are present in each order
        for order_dict in result:
            assert "side" in order_dict
            assert "price" in order_dict
            assert "size" in order_dict
            assert "timestamp" in order_dict
            assert order_dict["market_slug"] == "test-market"
            assert order_dict["market_id"] == "test-id-123"
            assert order_dict["outcome_name"] == "YES"
            assert order_dict["asset_id"] == "asset-456"

    def test_to_orders_dicts_empty_orderbook(self, orderbook):
        """Test to_orders_dicts with empty orderbook."""
        result = orderbook.to_orders_dicts()
        assert result == []

    @patch('src.models.synthetic_orderbook.datetime')
    def test_edge_cases(self, mock_datetime, orderbook):
        """Test various edge cases."""
        mock_datetime.now().timestamp.return_value = 1234567.890

        # Test with string "0.0" size
        orderbook.add_entries([{"side": "SELL", "price": "0.5", "size": "0.0"}], timestamp=1234567890)
        assert len(orderbook.orders_lookup) == 0

        # Test with empty orders list
        orderbook.add_entries([], timestamp=1234567890)
        assert len(orderbook.orders_lookup) == 0

        # Test replace_entries with empty list
        orderbook.replace_entries([], timestamp=1234567890)
        assert len(orderbook.orders_lookup) == 0
