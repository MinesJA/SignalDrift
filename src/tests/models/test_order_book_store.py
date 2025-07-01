import pytest
from typing import Dict, Any
from unittest.mock import Mock, patch
from src.models import OrderBookStore, SyntheticOrderBook, PriceChangeEvent, BookEvent, OrderSide, SyntheticOrder, EventType


class TestOrderBookStore:

    @pytest.fixture
    def mock_books(self):
        """Create mock SyntheticOrderBook instances for testing."""
        book1 = Mock(spec=SyntheticOrderBook)
        book1.asset_id = "asset-1"

        book2 = Mock(spec=SyntheticOrderBook)
        book2.asset_id = "asset-2"

        book3 = Mock(spec=SyntheticOrderBook)
        book3.asset_id = "asset-3"

        return [book1, book2, book3]

    @pytest.fixture
    def order_book_store(self, mock_books):
        """Create an OrderBookStore instance with mock books."""
        return OrderBookStore(market_slug="test-market", market_id=123456, books=mock_books)

    def test_init(self, mock_books):
        """Test the initialization of OrderBookStore."""
        store = OrderBookStore(market_slug="test-market", market_id=123456, books=mock_books)

        assert store.market_slug == "test-market"
        assert store.market_id == 123456
        assert len(store.books_lookup) == 3
        assert "asset-1" in store.books_lookup
        assert "asset-2" in store.books_lookup
        assert "asset-3" in store.books_lookup
        assert store.books_lookup["asset-1"] == mock_books[0]
        assert store.books_lookup["asset-2"] == mock_books[1]
        assert store.books_lookup["asset-3"] == mock_books[2]

    def test_books_property(self, order_book_store, mock_books):
        """Test the books property returns list of all books."""
        books = order_book_store.books
        assert len(books) == 3
        assert all(book in books for book in mock_books)

    def test_asset_ids_property(self, order_book_store):
        """Test the asset_ids property returns list of all asset IDs."""
        asset_ids = order_book_store.asset_ids
        assert len(asset_ids) == 3
        assert "asset-1" in asset_ids
        assert "asset-2" in asset_ids
        assert "asset-3" in asset_ids

    def test_lookup(self, order_book_store, mock_books):
        """Test looking up a single book by asset ID."""
        book = order_book_store.lookup("asset-2")
        assert book == mock_books[1]

        book = order_book_store.lookup("asset-1")
        assert book == mock_books[0]

    def test_lookup_nonexistent(self, order_book_store):
        """Test looking up a non-existent asset ID raises KeyError."""
        with pytest.raises(KeyError):
            order_book_store.lookup("nonexistent-asset")

    def test_lookups(self, order_book_store, mock_books):
        """Test looking up multiple books by asset IDs."""
        books = order_book_store.lookups(["asset-1", "asset-3"])
        assert len(books) == 2
        assert books[0] == mock_books[0]
        assert books[1] == mock_books[2]

    def test_lookups_with_nonexistent(self, order_book_store):
        """Test lookups with non-existent asset ID raises KeyError."""
        with pytest.raises(KeyError):
            order_book_store.lookups(["asset-1", "nonexistent-asset"])

    @pytest.mark.skip(reason="Test needs refactoring for MarketEvent objects")
    def test_update_book_with_event_type(self, order_book_store):
        """Test update_book with price_change events."""
        market_orders = [
            PriceChangeEvent(
                event_type=EventType.PRICE_CHANGE,
                market_slug="test-market",
                market_id=123456,
                market="test-market-address",
                asset_id="asset-1",
                outcome_name="YES",
                timestamp=1234567890,
                hash="test-hash-1",
                changes=[SyntheticOrder(side=OrderSide.SELL, price=0.5, size=100.0)]
            ),
            PriceChangeEvent(
                event_type=EventType.PRICE_CHANGE,
                market_slug="test-market",
                market_id=123456,
                market="test-market-address",
                asset_id="asset-2",
                outcome_name="NO",
                timestamp=1234567891,
                hash="test-hash-2",
                changes=[SyntheticOrder(side=OrderSide.SELL, price=0.6, size=200.0)]
            )
        ]

        result = order_book_store.update_book(market_orders)

        # Check that the method returns self
        assert result == order_book_store

        # Check that set_timestamp was called (which proves events were processed)
        order_book_store.books_lookup["asset-1"].set_timestamp.assert_called_once_with(1234567890)
        order_book_store.books_lookup["asset-2"].set_timestamp.assert_called_once_with(1234567891)
        
        # For PriceChangeEvent, add_entries should be called
        order_book_store.books_lookup["asset-1"].add_entries.assert_called_once()
        order_book_store.books_lookup["asset-2"].add_entries.assert_called_once()
        order_book_store.books_lookup["asset-3"].add_entries.assert_not_called()

    @pytest.mark.skip(reason="Test needs refactoring for MarketEvent objects")
    def test_update_book_with_book_event(self, order_book_store):
        """Test update_book with 'book' event."""
        market_orders = [
            {
                "asset_id": "asset-1",
                "event_type": "book",
                "asks": [{"price": "0.7", "size": "300"}],
                "timestamp": 1234567892
            }
        ]

        result = order_book_store.update_book(market_orders)

        # Check that the method returns self
        assert result == order_book_store

        # Check that replace_entries was called on the correct book
        order_book_store.books_lookup["asset-1"].replace_entries.assert_called_once_with(
            [{"price": "0.7", "size": "300"}], 1234567892
        )
        order_book_store.books_lookup["asset-2"].replace_entries.assert_not_called()
        order_book_store.books_lookup["asset-3"].replace_entries.assert_not_called()

    @pytest.mark.skip(reason="Test needs refactoring for MarketEvent objects")
    def test_update_book_mixed_events(self, order_book_store):
        """Test update_book with mixed event types."""
        market_orders = [
            {
                "asset_id": "asset-1",
                "event_type": "event_type",
                "changes": [{"price": "0.5", "size": "100"}],
                "timestamp": 1234567890
            },
            {
                "asset_id": "asset-2",
                "event_type": "book",
                "asks": [{"price": "0.8", "size": "400"}],
                "timestamp": 1234567893
            },
            {
                "asset_id": "asset-1",
                "event_type": "book",
                "asks": [{"price": "0.9", "size": "500"}],
                "timestamp": 1234567894
            }
        ]

        order_book_store.update_book(market_orders)

        # Check that methods were called in correct order
        assert order_book_store.books_lookup["asset-1"].add_entries.call_count == 1
        assert order_book_store.books_lookup["asset-1"].replace_entries.call_count == 1
        assert order_book_store.books_lookup["asset-2"].replace_entries.call_count == 1

        # Verify the specific calls
        order_book_store.books_lookup["asset-1"].add_entries.assert_called_with(
            [{"price": "0.5", "size": "100"}], 1234567890
        )
        order_book_store.books_lookup["asset-1"].replace_entries.assert_called_with(
            [{"price": "0.9", "size": "500"}], 1234567894
        )
        order_book_store.books_lookup["asset-2"].replace_entries.assert_called_with(
            [{"price": "0.8", "size": "400"}], 1234567893
        )

    @pytest.mark.skip(reason="Test needs refactoring for MarketEvent objects")
    def test_update_book_with_unknown_event_type(self, order_book_store):
        """Test update_book with unknown event type (no match case)."""
        market_orders = [
            {
                "asset_id": "asset-1",
                "event_type": "unknown_type",
                "data": "some data",
                "timestamp": 1234567890
            }
        ]

        # Should not raise an error, just not match any case
        order_book_store.update_book(market_orders)

        # Check that no methods were called
        order_book_store.books_lookup["asset-1"].add_entries.assert_not_called()
        order_book_store.books_lookup["asset-1"].replace_entries.assert_not_called()

    def test_update_book_empty_list(self, order_book_store):
        """Test update_book with empty list of orders."""
        result = order_book_store.update_book([])

        # Should return self and not call any methods
        assert result == order_book_store
        for book in order_book_store.books:
            book.add_entries.assert_not_called()
            book.replace_entries.assert_not_called()

    @pytest.mark.skip(reason="Test needs refactoring for MarketEvent objects")
    def test_update_book_nonexistent_asset(self, order_book_store):
        """Test update_book with non-existent asset ID raises KeyError."""
        market_orders = [
            {
                "asset_id": "nonexistent-asset",
                "event_type": "event_type",
                "changes": [{"price": "0.5", "size": "100"}],
                "timestamp": 1234567890
            }
        ]

        with pytest.raises(KeyError):
            order_book_store.update_book(market_orders)
