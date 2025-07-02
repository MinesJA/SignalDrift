import pytest
from unittest.mock import Mock, patch
from src.main import get_order_message_register, OrdersStore, OrderBookStore
from src.models import SyntheticOrderBook, Order
from src.models.market_event import MarketEvent, BookEvent, PriceChangeEvent, EventType
from src.models.synthetic_orderbook import SyntheticOrder
from src.models.order import OrderSide


class TestGetOrderMessageRegister:

    @pytest.fixture
    def mock_orderbook_store(self):
        """Create a mock OrderBookStore."""
        store = Mock(spec=OrderBookStore)
        store.market_slug = "test-market"
        store.market_id = 123456

        # Create mock order books
        book_a = Mock(spec=SyntheticOrderBook)
        book_b = Mock(spec=SyntheticOrderBook)
        store.books = [book_a, book_b]

        return store

    @pytest.fixture
    def order_store(self):
        """Create an OrdersStore instance."""
        return OrdersStore()

    @pytest.fixture
    def sample_market_message(self):
        """Create a sample market message as dict (handler expects dicts)."""
        return [
            {
                "asset_id": "asset-123",
                "event_type": "book",
                "market_slug": "test-market",
                "market": "test-market-address",
                "asks": [
                    {"price": "0.5", "size": "100"},
                    {"price": "0.6", "size": "200"}
                ],
                "bids": [],
                "timestamp": 1234567890,
                "hash": "test-hash-main"
            }
        ]

    @patch('src.main.PolymarketOrderService')
    @patch('src.main.write_marketEvents')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    @patch('src.main.datetime')
    def test_handler_successful_execution(
        self,
        mock_datetime,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketEvents,
        mock_polymarket_service,
        mock_orderbook_store,
        order_store,
        sample_market_message
    ):
        """Test successful execution of the handler."""
        # Setup mocks
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now

        mock_orders = [Mock(spec=Order), Mock(spec=Order)]
        mock_calculate_orders.return_value = mock_orders
        mock_orderbook_store.update_book.return_value = mock_orderbook_store

        # Mock the lookup method to return a book with outcome_name
        mock_book = Mock()
        mock_book.outcome_name = "YES"
        mock_orderbook_store.lookup.return_value = mock_book
        
        # Mock PolymarketOrderService
        mock_service_instance = Mock()
        mock_service_instance.execute_orders_from_list.return_value = {"success": True}
        mock_polymarket_service.return_value = mock_service_instance

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(sample_market_message)

        # Verify calls - should be called with MarketEvent objects, not raw dicts
        mock_orderbook_store.update_book.assert_called_once()
        # Get the actual call arguments
        call_args = mock_orderbook_store.update_book.call_args[0][0]
        assert len(call_args) == 1  # Should have converted 1 message
        mock_calculate_orders.assert_called_once_with(
            mock_orderbook_store.books[0],
            mock_orderbook_store.books[1]
        )

        # Verify orders were added to store
        assert order_store.orders == mock_orders

        # Verify writes
        mock_write_marketEvents.assert_called_once()
        write_call = mock_write_marketEvents.call_args
        assert write_call.kwargs["market_slug"] == "test-market"
        assert write_call.kwargs["market_id"] == 123456
        assert write_call.kwargs["datetime"] == mock_now
        assert write_call.kwargs["test_mode"] == False
        # market_events should be MarketEvent objects, not raw dicts
        assert len(write_call.kwargs["market_events"]) == 1
        mock_write_orderBookStore.assert_called_once_with(
            market_slug="test-market",
            orderBook_store=mock_orderbook_store,
            datetime=mock_now,
            test_mode=False
        )
        mock_write_orders.assert_called_once_with(
            market_slug="test-market",
            orders=mock_orders,
            datetime=mock_now,
            test_mode=False
        )

    @patch('src.main.write_marketEvents')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    def test_handler_exception_handling(
        self,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketEvents,
        mock_orderbook_store,
        order_store,
        sample_market_message,
        capsys
    ):
        """Test that exceptions are caught and logged."""
        # Make update_book raise an exception
        mock_orderbook_store.update_book.side_effect = Exception("Test exception")

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler - should not raise
        handler(sample_market_message)

        # Verify error was printed
        captured = capsys.readouterr()
        assert "ERROR ERROR ERROR" in captured.out
        assert "Test exception" in captured.out

        # Verify no writes happened
        mock_write_marketEvents.assert_not_called()
        mock_write_orderBookStore.assert_not_called()
        mock_write_orders.assert_not_called()

    @patch('src.main.PolymarketOrderService')
    @patch('src.main.write_marketEvents')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    @patch('src.main.datetime')
    def test_handler_with_empty_orders(
        self,
        mock_datetime,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketEvents,
        mock_polymarket_service,
        mock_orderbook_store,
        order_store,
        sample_market_message
    ):
        """Test handler when no orders are calculated."""
        # Setup mocks
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now

        mock_calculate_orders.return_value = []
        mock_orderbook_store.update_book.return_value = mock_orderbook_store
        
        # Mock PolymarketOrderService
        mock_service_instance = Mock()
        mock_service_instance.execute_orders_from_list.return_value = {"success": True}
        mock_polymarket_service.return_value = mock_service_instance
        
        # Mock the lookup method
        mock_book = Mock()
        mock_book.outcome_name = "YES"
        mock_orderbook_store.lookup.return_value = mock_book

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(sample_market_message)

        # Verify empty orders were added
        assert order_store.orders == []

        # Verify writes still happened
        mock_write_marketEvents.assert_called_once()
        mock_write_orderBookStore.assert_called_once()
        mock_write_orders.assert_called_once_with(
            market_slug="test-market",
            orders=[],
            datetime=mock_now,
            test_mode=False
        )

    @patch('src.main.PolymarketOrderService')
    @patch('src.main.write_marketEvents')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    def test_handler_write_failure(
        self,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketEvents,
        mock_polymarket_service,
        mock_orderbook_store,
        order_store,
        sample_market_message,
        capsys
    ):
        """Test that write failures are handled gracefully."""
        # Setup mocks
        mock_calculate_orders.return_value = []
        mock_orderbook_store.update_book.return_value = mock_orderbook_store

        # Mock PolymarketOrderService
        mock_service_instance = Mock()
        mock_service_instance.execute_orders_from_list.return_value = {"success": True}
        mock_polymarket_service.return_value = mock_service_instance
        
        # Mock the lookup method
        mock_book = Mock()
        mock_book.outcome_name = "YES"
        mock_orderbook_store.lookup.return_value = mock_book

        # Make write fail
        mock_write_marketEvents.side_effect = Exception("Write failed")

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(sample_market_message)

        # Verify error was printed
        captured = capsys.readouterr()
        assert "ERROR ERROR ERROR" in captured.out
        assert "Write failed" in captured.out

    def test_handler_returns_callable(self, mock_orderbook_store, order_store):
        """Test that get_order_message_register returns a callable."""
        handler = get_order_message_register(mock_orderbook_store, order_store)
        assert callable(handler)

    @patch('src.main.PolymarketOrderService')
    @patch('src.main.write_marketEvents')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    @patch('src.main.datetime')
    def test_handler_multiple_messages(
        self,
        mock_datetime,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketEvents,
        mock_polymarket_service,
        mock_orderbook_store,
        order_store
    ):
        """Test handler with multiple market messages."""
        # Setup mocks
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now

        mock_orders = [Mock(spec=Order)]
        mock_calculate_orders.return_value = mock_orders
        mock_orderbook_store.update_book.return_value = mock_orderbook_store

        # Mock PolymarketOrderService
        mock_service_instance = Mock()
        mock_service_instance.execute_orders_from_list.return_value = {"success": True}
        mock_polymarket_service.return_value = mock_service_instance

        # Mock the lookup method to return a book with outcome_name
        mock_book = Mock()
        mock_book.outcome_name = "YES"
        mock_orderbook_store.lookup.return_value = mock_book

        # Create multiple market messages as dicts (handler expects dicts)
        market_messages = [
            {
                "asset_id": "asset-123",
                "event_type": "book",
                "market_slug": "test-market",
                "market": "test-market-address",
                "asks": [{"price": "0.5", "size": "100"}],
                "bids": [],
                "timestamp": 1234567890,
                "hash": "test-hash-multiple-1"
            },
            {
                "asset_id": "asset-456",
                "event_type": "price_change",
                "market_slug": "test-market",
                "market": "test-market-address",
                "changes": [{"side": "BUY", "price": "0.7", "size": "300"}],
                "timestamp": 1234567891,
                "hash": "test-hash-multiple-2"
            }
        ]

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(market_messages)

        # Verify update_book was called with MarketEvent objects (converted from dicts)
        mock_orderbook_store.update_book.assert_called_once()
        call_args = mock_orderbook_store.update_book.call_args[0][0]
        assert len(call_args) == 2
        # Check first event properties
        assert call_args[0].event_type.value == "book"
        assert call_args[0].asset_id == "asset-123"
        assert hasattr(call_args[0], 'asks')
        assert hasattr(call_args[0], 'bids')
        # Check second event properties
        assert call_args[1].event_type.value == "price_change"
        assert call_args[1].asset_id == "asset-456"
        assert hasattr(call_args[1], 'changes')

        # Verify orders were added
        assert len(order_store.orders) == 1
        assert order_store.orders == mock_orders
