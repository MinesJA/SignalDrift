import pytest
from datetime import datetime
from unittest.mock import patch
from src.models.synthetic_orderbook import SyntheticOrderBook, SyntheticOrder
from src.models.order import OrderSide


class TestSyntheticOrderBook:

    @pytest.fixture
    def orderbook(self):
        """Create a SyntheticOrderBook instance for testing."""
        return SyntheticOrderBook(
            market_slug="test-market",
            market_id=123,
            outcome_name="YES",
            asset_id="asset-456",
            timestamp=1000
        )

    def test_init(self):
        """Test the initialization of SyntheticOrderBook."""
        ob = SyntheticOrderBook(
            market_slug="test-market",
            market_id=123,
            outcome_name="YES",
            asset_id="asset-456",
            timestamp=1000
        )

        assert ob.market_slug == "test-market"
        assert ob.market_id == 123
        assert ob.outcome_name == "YES"
        assert ob.asset_id == "asset-456"
        assert ob.orders_lookup == {}
        assert ob.orders == []

    def test_orders_property(self, orderbook):
        """Test the orders property returns list of orders."""
        # Add some orders manually
        orderbook.orders_lookup = {
            0.5: SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100.0),
            0.6: SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200.0)
        }

        orders = orderbook.orders
        assert len(orders) == 2
        assert all(isinstance(order, SyntheticOrder) for order in orders)
        assert {order.price for order in orders} == {0.5, 0.6}

    def test_add_entries_new_orders(self, orderbook):
        """Test adding new orders to the orderbook."""

        orders = [
            SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100),
            SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200)
        ]

        orderbook.add_entries(orders)

        assert len(orderbook.orders_lookup) == 2
        assert 0.5 in orderbook.orders_lookup
        assert 0.6 in orderbook.orders_lookup

        order1 = orderbook.orders_lookup[0.5]
        assert order1.side == OrderSide.SELL
        assert order1.price == 0.5
        assert order1.size == 100.0

        order2 = orderbook.orders_lookup[0.6]
        assert order2.side == OrderSide.SELL
        assert order2.price == 0.6
        assert order2.size == 200.0

    def test_add_entries_update_existing(self, orderbook):
        """Test updating existing orders in the orderbook."""

        # Add initial order
        orderbook.add_entries([
            SyntheticOrder(side= OrderSide.SELL, price=0.5, size=100)
        ])

        # Update with new size - should replace (not accumulate)
        orderbook.add_entries([
            SyntheticOrder(side=OrderSide.SELL, price=0.5, size=50)
        ])

        assert len(orderbook.orders_lookup) == 1
        order = orderbook.orders_lookup[0.5]
        assert order.size == 50.0

    def test_add_entries_remove_zero_size(self, orderbook):
        """Test that orders with size 0 are removed from the orderbook."""

        # Add initial orders
        orderbook.add_entries([
            SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100),
            SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200)
        ])

        assert len(orderbook.orders_lookup) == 2

        # Remove order by setting size to 0
        orderbook.add_entries([SyntheticOrder(side=OrderSide.SELL, price=0.5, size=0)])

        assert len(orderbook.orders_lookup) == 1
        assert 0.5 not in orderbook.orders_lookup
        assert 0.6 in orderbook.orders_lookup

    def test_add_entries_non_sell_orders(self, orderbook):
        """Test that non-SELL orders are ignored."""

        orders = [
            SyntheticOrder(side=OrderSide.BUY, price=0.5, size=100),
            SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200)
        ]

        orderbook.add_entries(orders)

        # Only SELL order should be added
        assert len(orderbook.orders_lookup) == 1
        assert 0.6 in orderbook.orders_lookup
        assert 0.5 not in orderbook.orders_lookup

    def test_replace_entries(self, orderbook):
        """Test replacing all entries in the orderbook."""

        # Add initial orders
        orderbook.add_entries([
            SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100),
            SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200)
        ])

        # Replace with new orders
        new_orders = [
            SyntheticOrder(price=0.7, side=OrderSide.SELL, size=300),
            SyntheticOrder(price=0.8, side=OrderSide.SELL, size=400)
        ]

        orderbook.replace_entries(new_orders)

        assert len(orderbook.orders_lookup) == 2
        assert 0.5 not in orderbook.orders_lookup
        assert 0.6 not in orderbook.orders_lookup
        assert 0.7 in orderbook.orders_lookup
        assert 0.8 in orderbook.orders_lookup

        order1 = orderbook.orders_lookup[0.7]
        assert order1.side == OrderSide.SELL
        assert order1.price == 0.7
        assert order1.size == 300.0

    def test_replace_entries_filters_small_sizes(self, orderbook):
        """Test that replace_entries filters out orders with size <= 0."""

        orders = [
            SyntheticOrder(price=0.5, side=OrderSide.SELL, size=0),
            SyntheticOrder(price=0.6, side=OrderSide.SELL,size=0.0),
            SyntheticOrder(price=0.7, side=OrderSide.SELL, size=1.1),
            SyntheticOrder(price=0.8, side=OrderSide.SELL, size=100)
        ]

        orderbook.replace_entries(orders)

        # Only orders with size > 0 should be kept
        assert len(orderbook.orders_lookup) == 2
        assert 0.7 in orderbook.orders_lookup
        assert 0.8 in orderbook.orders_lookup
        assert 0.5 not in orderbook.orders_lookup
        assert 0.6 not in orderbook.orders_lookup

    def test_to_orders_dicts(self, orderbook):
        """Test converting orders to dictionary format."""

        # Add orders in non-sorted order
        orderbook.add_entries([
            SyntheticOrder(side=OrderSide.SELL, price=0.8, size=400.0),
            SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100.0),
            SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200.0)
        ])

        result = orderbook.asdict_rows()

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
            assert order_dict["market_slug"] == "test-market"
            assert order_dict["market_id"] == 123
            assert order_dict["outcome_name"] == "YES"
            assert order_dict["asset_id"] == "asset-456"

    def test_to_orders_dicts_empty_orderbook(self, orderbook):
        """Test to_orders_dicts with empty orderbook."""
        result = orderbook.asdict_rows()
        assert result == []

    def test_edge_cases(self, orderbook):
        """Test various edge cases."""

        # Test with string "0.0" size
        orderbook.add_entries([SyntheticOrder(side=OrderSide.SELL, price=0.5, size=0.0)])
        assert len(orderbook.orders_lookup) == 0

        # Test with empty orders list
        orderbook.add_entries([])
        assert len(orderbook.orders_lookup) == 0

        # Test replace_entries with empty list
        orderbook.replace_entries([])
        assert len(orderbook.orders_lookup) == 0
