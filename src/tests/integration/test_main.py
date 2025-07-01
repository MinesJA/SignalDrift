import pytest
import tempfile
import json
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from src.main import (
    OrdersStore, 
    get_order_message_register, 
    run_market_connection
)
from src.models import SyntheticOrderBook, OrderBookStore, Order, OrderType


class TestOrderProcessingIntegration:
    """Integration tests for the complete order processing pipeline."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory for file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def real_orderbook_store(self):
        """Create a real OrderBookStore with real SyntheticOrderBook instances."""
        market_slug = "test-market-integration"
        books = [
            SyntheticOrderBook(
                market_slug=market_slug,
                market_id="market-123",
                outcome_name="YES",
                asset_id="asset-yes"
            ),
            SyntheticOrderBook(
                market_slug=market_slug,
                market_id="market-123", 
                outcome_name="NO",
                asset_id="asset-no"
            )
        ]
        return OrderBookStore(market_slug, 123456, books)
    
    @pytest.fixture
    def realistic_market_messages(self):
        """Create realistic market messages that simulate real trading activity."""
        return [
            {
                "asset_id": "asset-yes",
                "event_type": "book",
                "asks": [
                    {"price": "0.45", "size": "1000"},
                    {"price": "0.46", "size": "500"},
                    {"price": "0.47", "size": "250"}
                ],
                "timestamp": int(datetime.now().timestamp())
            },
            {
                "asset_id": "asset-no", 
                "event_type": "book",
                "asks": [
                    {"price": "0.54", "size": "800"},
                    {"price": "0.55", "size": "400"},
                    {"price": "0.56", "size": "200"}
                ],
                "timestamp": int(datetime.now().timestamp())
            }
        ]
    
    @patch('src.main.write_marketMessages')
    @patch('src.main.write_orderBookStore')
    @patch('src.main.write_orders')
    @patch('src.main.calculate_orders')
    def test_end_to_end_order_processing(
        self,
        mock_calculate_orders,
        mock_write_orders,
        mock_write_orderBookStore,
        mock_write_marketMessages,
        real_orderbook_store,
        realistic_market_messages
    ):
        """Test complete order processing flow with real objects."""
        # Setup
        order_store = OrdersStore()
        
        # Create mock orders that strategy would return
        mock_orders = [
            Mock(spec=Order, order_type=OrderType.LIMIT_BUY, price=0.44, size=100),
            Mock(spec=Order, order_type=OrderType.LIMIT_SELL, price=0.57, size=50)
        ]
        mock_calculate_orders.return_value = mock_orders
        
        # Get the message handler
        handler = get_order_message_register(real_orderbook_store, order_store)
        
        # Process market messages
        handler(realistic_market_messages)
        
        # Verify the order books were updated with real data
        yes_book = real_orderbook_store.lookup("asset-yes")
        no_book = real_orderbook_store.lookup("asset-no")
        
        # Check that orders were actually added to the books
        assert len(yes_book.orders) == 3  # 3 ask orders
        assert len(no_book.orders) == 3   # 3 ask orders
        
        # Verify order details
        yes_orders = yes_book.orders
        assert yes_orders[0].price == 0.45
        assert yes_orders[0].size == 1000.0
        assert yes_orders[0].side == "ask"
        
        # Verify strategy was called with real books
        mock_calculate_orders.assert_called_once_with(yes_book, no_book)
        
        # Verify orders were added to store
        assert len(order_store.orders) == 2
        assert order_store.orders == mock_orders
        
        # Verify file writes were called
        mock_write_marketMessages.assert_called_once()
        mock_write_orderBookStore.assert_called_once()
        mock_write_orders.assert_called_once()
        
        # Verify write calls had correct arguments
        write_market_call = mock_write_marketMessages.call_args
        assert write_market_call[0][0] == "test-market-integration"  # market_slug
        assert write_market_call[0][2] == realistic_market_messages  # messages
        
        write_orders_call = mock_write_orders.call_args
        assert write_orders_call[0][2] == mock_orders  # orders
    
    def test_multiple_message_processing_updates_order_books(
        self,
        real_orderbook_store
    ):
        """Test that multiple market messages correctly update order books."""
        order_store = OrdersStore()
        
        with patch('src.main.calculate_orders', return_value=[]), \
             patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            handler = get_order_message_register(real_orderbook_store, order_store)
            
            # First update
            first_messages = [{
                "asset_id": "asset-yes",
                "event_type": "book", 
                "asks": [{"price": "0.50", "size": "100"}],
                "timestamp": 1000
            }]
            handler(first_messages)
            
            # Second update - should replace first
            second_messages = [{
                "asset_id": "asset-yes",
                "event_type": "book",
                "asks": [
                    {"price": "0.49", "size": "200"},
                    {"price": "0.51", "size": "150"}
                ],
                "timestamp": 2000
            }]
            handler(second_messages)
            
            # Verify final state
            yes_book = real_orderbook_store.lookup("asset-yes")
            orders = yes_book.orders
            
            assert len(orders) == 2
            # Orders should be from second message (replace_entries)
            prices = [order.price for order in orders]
            assert 0.49 in prices
            assert 0.51 in prices
            assert 0.50 not in prices  # Should be replaced
    
    @patch('src.main.calculate_orders')
    def test_strategy_calculation_with_real_data(
        self,
        mock_calculate_orders,
        real_orderbook_store
    ):
        """Test that strategy gets called with real order book data."""
        order_store = OrdersStore()
        mock_calculate_orders.return_value = []
        
        with patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            handler = get_order_message_register(real_orderbook_store, order_store)
            
            # Add realistic data to both books
            messages = [
                {
                    "asset_id": "asset-yes",
                    "event_type": "book",
                    "asks": [{"price": "0.45", "size": "1000"}],
                    "timestamp": 1000
                },
                {
                    "asset_id": "asset-no", 
                    "event_type": "book",
                    "asks": [{"price": "0.55", "size": "800"}],
                    "timestamp": 1000
                }
            ]
            
            handler(messages)
            
            # Verify strategy was called with the actual books
            mock_calculate_orders.assert_called_once()
            call_args = mock_calculate_orders.call_args[0]
            book_a, book_b = call_args
            
            # Verify these are real SyntheticOrderBook instances with data
            assert isinstance(book_a, SyntheticOrderBook)
            assert isinstance(book_b, SyntheticOrderBook)
            assert len(book_a.orders) == 1
            assert len(book_b.orders) == 1
            assert book_a.orders[0].price == 0.45
            assert book_b.orders[0].price == 0.55
    
    def test_error_handling_preserves_order_book_state(
        self,
        real_orderbook_store
    ):
        """Test that exceptions don't corrupt order book state."""
        order_store = OrdersStore()
        
        # Add initial data
        initial_messages = [{
            "asset_id": "asset-yes",
            "event_type": "book",
            "asks": [{"price": "0.50", "size": "100"}],
            "timestamp": 1000
        }]
        
        with patch('src.main.calculate_orders', return_value=[]), \
             patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            handler = get_order_message_register(real_orderbook_store, order_store)
            handler(initial_messages)
            
            # Verify initial state
            yes_book = real_orderbook_store.lookup("asset-yes")
            assert len(yes_book.orders) == 1
            assert yes_book.orders[0].price == 0.50
        
        # Now cause an error in strategy calculation
        with patch('src.main.calculate_orders', side_effect=Exception("Strategy error")), \
             patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            # This should not raise, error should be caught
            error_messages = [{
                "asset_id": "asset-yes", 
                "event_type": "book",
                "asks": [{"price": "0.48", "size": "200"}],
                "timestamp": 2000
            }]
            
            handler(error_messages)
            
            # Verify order book was still updated despite strategy error
            yes_book = real_orderbook_store.lookup("asset-yes")
            assert len(yes_book.orders) == 1
            assert yes_book.orders[0].price == 0.48  # Should be updated


class TestMarketConnectionIntegration:
    """Integration tests for market connection setup and management."""
    
    @pytest.fixture
    def mock_market_metadata(self):
        """Realistic market metadata response."""
        return {
            'id': 12345,
            'clobTokenIds': '["token-yes", "token-no"]',
            'outcomes': '["YES", "NO"]'
        }
    
    @patch('src.main.PolymarketMarketEventsService')
    @patch('src.main.PolymarketService')
    def test_successful_market_connection_setup(
        self,
        mock_polymarket_service,
        mock_events_service,
        mock_market_metadata
    ):
        """Test complete market connection setup with real objects."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.get_market_by_slug.return_value = mock_market_metadata
        mock_polymarket_service.return_value = mock_service_instance
        
        mock_events_instance = Mock()
        mock_events_service.return_value = mock_events_instance
        
        # Run market connection
        market_slug = "test-market-slug"
        run_market_connection(market_slug)
        
        # Verify service calls
        mock_service_instance.get_market_by_slug.assert_called_once_with(market_slug)
        
        # Verify events service was created with correct parameters
        mock_events_service.assert_called_once()
        call_args = mock_events_service.call_args
        
        assert call_args[0][0] == market_slug  # market_slug
        assert call_args[0][1] == ["token-yes", "token-no"]  # asset_ids
        assert len(call_args[0][2]) == 1  # one message handler
        
        # Verify the handler is callable
        handler = call_args[0][2][0]
        assert callable(handler)
        
        # Verify run was called
        mock_events_instance.run.assert_called_once()
    
    @patch('src.main.PolymarketMarketEventsService')
    @patch('src.main.PolymarketService')
    def test_market_connection_with_invalid_slug(
        self,
        mock_polymarket_service,
        mock_events_service
    ):
        """Test error handling when market slug doesn't exist."""
        # Setup service to return None (market not found)
        mock_service_instance = Mock()
        mock_service_instance.get_market_by_slug.return_value = None
        mock_polymarket_service.return_value = mock_service_instance
        
        # Should not raise exception
        run_market_connection("invalid-slug")
        
        # Events service should not be called
        mock_events_service.assert_not_called()
    
    @patch('src.main.PolymarketMarketEventsService')
    @patch('src.main.PolymarketService')
    def test_market_connection_service_exception(
        self,
        mock_polymarket_service,
        mock_events_service
    ):
        """Test error handling when service raises exception."""
        # Setup service to raise exception
        mock_service_instance = Mock()
        mock_service_instance.get_market_by_slug.side_effect = Exception("Service error")
        mock_polymarket_service.return_value = mock_service_instance
        
        # Should not raise exception (error is caught and logged)
        run_market_connection("test-market")
        
        # Events service should not be called
        mock_events_service.assert_not_called()
    
    @patch('src.main.PolymarketMarketEventsService')
    @patch('src.main.PolymarketService')
    def test_real_orderbook_creation_from_metadata(
        self,
        mock_polymarket_service,
        mock_events_service,
        mock_market_metadata
    ):
        """Test that real OrderBookStore and SyntheticOrderBooks are created correctly."""
        # Setup mocks
        mock_service_instance = Mock()
        mock_service_instance.get_market_by_slug.return_value = mock_market_metadata
        mock_polymarket_service.return_value = mock_service_instance
        
        # Capture the handler to test it
        captured_handler = None
        def capture_handler(market_slug, asset_ids, handlers):
            nonlocal captured_handler
            captured_handler = handlers[0]
            return Mock()
        
        mock_events_service.side_effect = capture_handler
        
        # Run market connection
        run_market_connection("test-market")
        
        # Test the captured handler with real market message
        assert captured_handler is not None
        
        # The handler should work with real data
        test_message = [{
            "asset_id": "token-yes",
            "event_type": "book",
            "asks": [{"price": "0.45", "size": "100"}],
            "timestamp": 1000
        }]
        
        # This should not raise (tests that real objects were created correctly)
        with patch('src.main.calculate_orders', return_value=[]), \
             patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            captured_handler(test_message)


class TestConcurrencyIntegration:
    """Integration tests for concurrent operations and threading."""
    
    def test_multiple_market_connections_thread_safety(self):
        """Test that multiple market connections can run concurrently safely."""
        market_slugs = ["market-1", "market-2", "market-3"]
        
        with patch('src.main.PolymarketService') as mock_service, \
             patch('src.main.PolymarketMarketEventsService') as mock_events:
            
            # Setup service to return valid metadata
            mock_service_instance = Mock()
            mock_service_instance.get_market_by_slug.return_value = {
                'id': 123,
                'clobTokenIds': '["token-1", "token-2"]', 
                'outcomes': '["YES", "NO"]'
            }
            mock_service.return_value = mock_service_instance
            
            # Track which markets were processed
            processed_markets = []
            lock = threading.Lock()
            
            def mock_events_service(market_slug, asset_ids, handlers):
                with lock:
                    processed_markets.append(market_slug)
                # Simulate some processing time
                time.sleep(0.1)
                return Mock()
            
            mock_events.side_effect = mock_events_service
            
            # Run multiple market connections concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for market_slug in market_slugs:
                    future = executor.submit(run_market_connection, market_slug)
                    futures.append(future)
                
                # Wait for all to complete
                for future in futures:
                    future.result()
            
            # Verify all markets were processed
            assert len(processed_markets) == 3
            assert set(processed_markets) == set(market_slugs)
    
    def test_concurrent_order_processing(self):
        """Test that order processing is thread-safe across multiple handlers."""
        # Create shared order store
        order_store = OrdersStore()
        
        # Create multiple order book stores for different markets
        stores = []
        for i in range(3):
            books = [
                SyntheticOrderBook(f"market-{i}", f"id-{i}", "YES", f"asset-yes-{i}"),
                SyntheticOrderBook(f"market-{i}", f"id-{i}", "NO", f"asset-no-{i}")
            ]
            stores.append(OrderBookStore(f"market-{i}", 100000 + i, books))
        
        # Create handlers for each store
        handlers = []
        for store in stores:
            handler = get_order_message_register(store, order_store)
            handlers.append(handler)
        
        # Create market messages for each handler
        messages_list = []
        for i in range(3):
            messages = [{
                "asset_id": f"asset-yes-{i}",
                "event_type": "book",
                "asks": [{"price": f"0.{40+i}", "size": f"{100*(i+1)}"}],
                "timestamp": 1000 + i
            }]
            messages_list.append(messages)
        
        with patch('src.main.calculate_orders') as mock_calc, \
             patch('src.main.write_marketMessages'), \
             patch('src.main.write_orderBookStore'), \
             patch('src.main.write_orders'):
            
            # Each handler returns different number of orders
            def side_effect_calc(book_a, book_b):
                # Return different orders based on which market
                market_slug = book_a.market_slug
                market_num = int(market_slug.split('-')[1])
                return [Mock(spec=Order) for _ in range(market_num + 1)]
            
            mock_calc.side_effect = side_effect_calc
            
            # Process messages concurrently
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for handler, messages in zip(handlers, messages_list):
                    future = executor.submit(handler, messages)
                    futures.append(future)
                
                # Wait for all to complete
                for future in futures:
                    future.result()
            
            # Verify all orders were added correctly
            # Market 0: 1 order, Market 1: 2 orders, Market 2: 3 orders
            expected_total_orders = 1 + 2 + 3
            assert len(order_store.orders) == expected_total_orders
    
    def test_order_store_thread_safety(self):
        """Test that OrdersStore operations are thread-safe."""
        order_store = OrdersStore()
        
        def add_orders_worker(worker_id, num_orders):
            """Worker function that adds orders concurrently."""
            orders = [Mock(spec=Order, worker_id=worker_id, order_num=i) 
                     for i in range(num_orders)]
            order_store.add_orders(orders)
        
        # Run multiple workers concurrently
        num_workers = 5
        orders_per_worker = 10
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for worker_id in range(num_workers):
                future = executor.submit(add_orders_worker, worker_id, orders_per_worker)
                futures.append(future)
            
            # Wait for all workers to complete
            for future in futures:
                future.result()
        
        # Verify all orders were added
        expected_total = num_workers * orders_per_worker
        assert len(order_store.orders) == expected_total
        
        # Verify orders from all workers are present
        worker_ids = set(order.worker_id for order in order_store.orders)
        assert worker_ids == set(range(num_workers))


class TestArbStrategyIntegration:
    """Integration tests for arbitrage strategy components."""
    
    # TODO: Update this test - get_arb_strategy was removed in refactoring
    @pytest.mark.skip(reason="get_arb_strategy function was removed in refactoring")
    def test_arb_strategy_with_real_order_books(self):
        """Test arbitrage strategy with real order book data."""
        # Create order books with realistic arbitrage opportunity
        books = [
            SyntheticOrderBook("arb-market", "market-123", "YES", "asset-yes"),
            SyntheticOrderBook("arb-market", "market-123", "NO", "asset-no")
        ]
        
        orderbook_store = OrderBookStore("arb-market", 123456, books)
        order_store = OrdersStore()
        
        # Add orders that create arbitrage opportunity
        # YES book: ask at 0.45 (underpriced)
        # NO book: ask at 0.50 (overpriced)
        # Total probability < 1.0, arbitrage opportunity exists
        
        yes_messages = [{
            "asset_id": "asset-yes",
            "event_type": "book", 
            "asks": [{"price": "0.45", "size": "1000"}],
            "timestamp": 1000
        }]
        
        no_messages = [{
            "asset_id": "asset-no",
            "event_type": "book",
            "asks": [{"price": "0.50", "size": "1000"}], 
            "timestamp": 1000
        }]
        
        # Update order books
        orderbook_store.update_book(yes_messages)
        orderbook_store.update_book(no_messages)
        
        # Test arbitrage strategy
        with patch('src.main.calculate_orders') as mock_calc:
            # Mock strategy to return profitable orders
            mock_orders = [
                Mock(spec=Order, order_type=OrderType.LIMIT_BUY, asset_id="asset-yes", price=0.45, size=500),
                Mock(spec=Order, order_type=OrderType.LIMIT_BUY, asset_id="asset-no", price=0.50, size=500)
            ]
            mock_calc.return_value = mock_orders
            
            # Get and execute arbitrage strategy
            arb_handler = get_arb_strategy(orderbook_store, order_store)
            arb_handler([])  # Empty message, strategy uses current book state
            
            # Verify strategy was called with real books
            mock_calc.assert_called_once()
            call_args = mock_calc.call_args[0]
            book_a, book_b = call_args
            
            assert book_a.orders[0].price == 0.45
            assert book_b.orders[0].price == 0.50
            
            # Verify orders were added to store
            assert len(order_store.orders) == 2
            assert order_store.orders == mock_orders
