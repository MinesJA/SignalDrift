import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.services.polymarket_service import PolymarketService


class TestPolymarketService:
    """Test cases for PolymarketService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PolymarketService()
        
    def test_init_without_private_key(self):
        """Test initialization without private key."""
        service = PolymarketService()
        assert service.clob_client is None
        assert service.gamma_api_base == "https://gamma-api.polymarket.com"
        assert service.clob_api_base == "https://clob.polymarket.com"
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_init_with_private_key(self, mock_clob_client):
        """Test initialization with private key."""
        mock_client = Mock()
        mock_clob_client.return_value = mock_client
        
        private_key = "0x1234567890abcdef"
        service = PolymarketService(private_key=private_key)
        
        mock_clob_client.assert_called_once()
        assert service.clob_client == mock_client
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_init_with_invalid_private_key(self, mock_clob_client):
        """Test initialization with invalid private key."""
        mock_clob_client.side_effect = Exception("Invalid key")
        
        service = PolymarketService(private_key="invalid_key")
        assert service.clob_client is None
        
    def test_place_order_without_clob_client(self):
        """Test place_order fails without CLOB client."""
        result = self.service.place_order(
            token_id="123",
            side="BUY",
            size=10.0,
            price=0.6
        )
        assert result is None
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_invalid_side(self, mock_clob_client):
        """Test place_order with invalid side parameter."""
        mock_client = Mock()
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="123",
            side="INVALID",
            size=10.0,
            price=0.6
        )
        assert result is None
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_invalid_price(self, mock_clob_client):
        """Test place_order with invalid price."""
        mock_client = Mock()
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        # Test price > 1.0
        result = service.place_order(
            token_id="123",
            side="BUY",
            size=10.0,
            price=1.5
        )
        assert result is None
        
        # Test negative price
        result = service.place_order(
            token_id="123",
            side="BUY",
            size=10.0,
            price=-0.1
        )
        assert result is None
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_invalid_size(self, mock_clob_client):
        """Test place_order with invalid size."""
        mock_client = Mock()
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        # Test zero size
        result = service.place_order(
            token_id="123",
            side="BUY",
            size=0.0,
            price=0.6
        )
        assert result is None
        
        # Test negative size
        result = service.place_order(
            token_id="123",
            side="BUY",
            size=-10.0,
            price=0.6
        )
        assert result is None
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_successful_buy(self, mock_clob_client):
        """Test successful BUY order placement."""
        mock_client = Mock()
        mock_order_response = Mock()
        mock_order_response.order_id = "order123"
        mock_client.create_order.return_value = mock_order_response
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="token123",
            side="BUY",
            size=10.0,
            price=0.6
        )
        
        assert result is not None
        assert result["order_id"] == "order123"
        assert result["token_id"] == "token123"
        assert result["side"] == "BUY"
        assert result["size"] == 10.0
        assert result["price"] == 0.6
        assert result["price_type"] == "price"
        assert result["status"] == "placed"
        assert isinstance(result["timestamp"], datetime)
        
        mock_client.create_order.assert_called_once_with(
            token_id="token123",
            side="BUY",
            size="10.0",
            price="0.6"
        )
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_successful_sell(self, mock_clob_client):
        """Test successful SELL order placement."""
        mock_client = Mock()
        mock_order_response = Mock()
        mock_order_response.order_id = "order456"
        mock_client.create_order.return_value = mock_order_response
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="token456",
            side="SELL",
            size=5.0,
            price=0.4
        )
        
        assert result is not None
        assert result["order_id"] == "order456"
        assert result["side"] == "SELL"
        assert result["size"] == 5.0
        assert result["price"] == 0.4
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_with_tick_price(self, mock_clob_client):
        """Test order placement with tick price type."""
        mock_client = Mock()
        mock_order_response = Mock()
        mock_order_response.order_id = "order789"
        mock_client.create_order.return_value = mock_order_response
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="token789",
            side="BUY",
            size=15.0,
            price=600,  # tick value
            price_type="tick"
        )
        
        assert result is not None
        assert result["price_type"] == "tick"
        
        mock_client.create_order.assert_called_once_with(
            token_id="token789",
            side="BUY",
            size="15.0",
            tick_size="600"
        )
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_clob_client_error(self, mock_clob_client):
        """Test place_order when CLOB client raises an error."""
        mock_client = Mock()
        mock_client.create_order.side_effect = Exception("Network error")
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="token123",
            side="BUY",
            size=10.0,
            price=0.6
        )
        
        assert result is None
        
    @patch('src.services.polymarket_service.ClobClient')
    def test_place_order_no_order_id_in_response(self, mock_clob_client):
        """Test place_order when response doesn't contain order_id."""
        mock_client = Mock()
        mock_order_response = Mock(spec=[])  # No order_id attribute
        mock_client.create_order.return_value = mock_order_response
        mock_clob_client.return_value = mock_client
        
        service = PolymarketService(private_key="0x123")
        
        result = service.place_order(
            token_id="token123",
            side="BUY",
            size=10.0,
            price=0.6
        )
        
        assert result is None