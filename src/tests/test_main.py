import pytest
from unittest.mock import Mock, patch, call
from src.main import get_order_message_register, OrdersStore, OrderBookStore
from src.models import SyntheticOrderBook, Order


class TestGetOrderMessageRegister:

    @pytest.fixture
    def mock_orderbook_store(self):
        """Create a mock OrderBookStore."""
        store = Mock(spec=OrderBookStore)
        store.market_slug = "test-market"
        store.market_id = "123456"

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
        """Create a sample market message."""
        return [
            {
                "asset_id": "asset-123",
                "event_type": "book",
                "asks": [
                    {"price": "0.5", "size": "100"},
                    {"price": "0.6", "size": "200"}
                ],
                "timestamp": 1234567890
            }
        ]

    @patch('src.main.write_marketMessages')
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
        mock_write_marketMessages,
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

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(sample_market_message)

        # Verify calls
        mock_orderbook_store.update_book.assert_called_once_with(sample_market_message)
        mock_calculate_orders.assert_called_once_with(
            mock_orderbook_store.books[0],
            mock_orderbook_store.books[1]
        )

        # Verify orders were added to store
        assert order_store.orders == mock_orders

        # Verify writes
        mock_write_marketMessages.assert_called_once_with(
            "test-market", mock_now, sample_market_message, "123456"
        )
        mock_write_orderBookStore.assert_called_once_with(
            "test-market", mock_now, mock_orderbook_store
        )
        mock_write_orders.assert_called_once_with(
            "test-market", mock_now, mock_orders
        )

    @patch('src.main.write_marketMessages')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    def test_handler_exception_handling(
        self,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketMessages,
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
        mock_write_marketMessages.assert_not_called()
        mock_write_orderBookStore.assert_not_called()
        mock_write_orders.assert_not_called()

    @patch('src.main.write_marketMessages')
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
        mock_write_marketMessages,
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

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(sample_market_message)

        # Verify empty orders were added
        assert order_store.orders == []

        # Verify writes still happened
        mock_write_marketMessages.assert_called_once()
        mock_write_orderBookStore.assert_called_once()
        mock_write_orders.assert_called_once_with(
            "test-market", mock_now, []
        )

    @patch('src.main.write_marketMessages')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    def test_handler_write_failure(
        self,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketMessages,
        mock_orderbook_store,
        order_store,
        sample_market_message,
        capsys
    ):
        """Test that write failures are handled gracefully."""
        # Setup mocks
        mock_calculate_orders.return_value = []
        mock_orderbook_store.update_book.return_value = mock_orderbook_store

        # Make write fail
        mock_write_marketMessages.side_effect = Exception("Write failed")

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

    @patch('src.main.write_marketMessages')
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
        mock_write_marketMessages,
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

        # Create multiple market messages
        market_messages = [
            {
                "asset_id": "asset-123",
                "event_type": "book",
                "asks": [{"price": "0.5", "size": "100"}],
                "timestamp": 1234567890
            },
            {
                "asset_id": "asset-456",
                "event_type": "event_type",
                "changes": [{"price": "0.7", "size": "300"}],
                "timestamp": 1234567891
            }
        ]

        # Create handler
        handler = get_order_message_register(mock_orderbook_store, order_store)

        # Execute handler
        handler(market_messages)

        # Verify update_book was called with all messages
        mock_orderbook_store.update_book.assert_called_once_with(market_messages)

        # Verify orders were added
        assert len(order_store.orders) == 1
        assert order_store.orders == mock_orders
