#!/usr/bin/env python3
"""Test script for Polymarket service."""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


from src.services.polymarket_service import PolymarketService


class TestPolymarketService(unittest.TestCase):
    """Unit tests for PolymarketService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = PolymarketService()

        # Sample order data for testing
        self.sample_order_data = {
            "order": {
                "salt": 12345,
                "maker": "0x123abc...",
                "signer": "0x456def...",
                "taker": "0x789ghi...",
                "tokenId": "token123",
                "makerAmount": "1000000",
                "takerAmount": "500000",
                "expiration": 1703980800,
                "nonce": 1,
                "feeRateBps": 100,
                "side": "BUY",
                "signatureType": 0,
                "signature": "0xabcd1234..."
            },
            "owner": "test-api-key"
        }

        self.sample_success_response = {
            "success": True,
            "orderId": "order-123",
            "orderHashes": ["0xhash1", "0xhash2"],
            "errorMsg": None
        }

        self.sample_error_response = {
            "success": False,
            "orderId": None,
            "orderHashes": None,
            "errorMsg": "Insufficient balance"
        }

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_success(self, mock_post):
        """Test successful single order placement."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_success_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.service.place_single_order(self.sample_order_data, "GTC")

        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertEqual(result["orderId"], "order-123")

        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("order", call_args.kwargs["json"])
        self.assertIn("owner", call_args.kwargs["json"])
        self.assertIn("orderType", call_args.kwargs["json"])
        self.assertEqual(call_args.kwargs["json"]["orderType"], "GTC")

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_failure(self, mock_post):
        """Test single order placement with API error."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_error_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.service.place_single_order(self.sample_order_data, "FOK")

        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertEqual(result["errorMsg"], "Insufficient balance")
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_single_order_network_error(self, mock_post):
        """Test single order placement with network error."""
        mock_post.side_effect = Exception("Network error")

        result = self.service.place_single_order(self.sample_order_data, "GTC")

        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Network error", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_multiple_orders_success(self, mock_post):
        """Test successful multiple orders placement."""
        mock_response = Mock()
        mock_response.json.return_value = self.sample_success_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        orders_data = [self.sample_order_data, self.sample_order_data]
        result = self.service.place_multiple_orders(orders_data, "GTC")

        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertEqual(result["orderId"], "order-123")

        # Verify the API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIsInstance(call_args.kwargs["json"], list)
        self.assertEqual(len(call_args.kwargs["json"]), 2)

    def test_place_multiple_orders_too_many(self):
        """Test multiple orders placement with too many orders."""
        orders_data = [self.sample_order_data] * 6  # 6 orders, max is 5

        result = self.service.place_multiple_orders(orders_data, "GTC")

        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Maximum of 5 orders", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    @patch('src.services.polymarket_service.requests.post')
    def test_place_multiple_orders_network_error(self, mock_post):
        """Test multiple orders placement with network error."""
        mock_post.side_effect = Exception("Network error")

        orders_data = [self.sample_order_data, self.sample_order_data]
        result = self.service.place_multiple_orders(orders_data, "FAK")

        self.assertIsNotNone(result)
        self.assertFalse(result["success"])
        self.assertIn("Network error", result["errorMsg"])
        self.assertIsNone(result["orderId"])

    def test_order_types_validation(self):
        """Test that different order types are handled correctly."""
        order_types = ["GTC", "FOK", "FAK", "GTD"]

        with patch('src.services.polymarket_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = self.sample_success_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            for order_type in order_types:
                result = self.service.place_single_order(self.sample_order_data, order_type)
                self.assertTrue(result["success"])

                # Check that the correct order type was sent
                call_args = mock_post.call_args
                self.assertEqual(call_args.kwargs["json"]["orderType"], order_type)

    def test_connect_websocket_success(self):
        """Test successful WebSocket connection."""
        async def run_test():
            mock_websocket = Mock()
            mock_websocket.closed = False

            async def mock_connect(*args, **kwargs):
                return mock_websocket

            with patch('src.services.polymarket_service.websockets.connect', side_effect=mock_connect):
                result = await self.service.connect_websocket()
                self.assertTrue(result)
                self.assertTrue(self.service.is_connected)
                self.assertEqual(self.service.websocket, mock_websocket)

        asyncio.run(run_test())

    @patch('src.services.polymarket_service.websockets.connect')
    def test_connect_websocket_failure(self, mock_connect):
        """Test WebSocket connection failure."""
        mock_connect.side_effect = Exception("Connection failed")

        async def run_test():
            result = await self.service.connect_websocket()
            self.assertFalse(result)
            self.assertFalse(self.service.is_connected)
            self.assertIsNone(self.service.websocket)

        asyncio.run(run_test())

    def test_disconnect_websocket(self):
        """Test WebSocket disconnection."""
        async def run_test():
            # Set up a mock websocket
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            self.service.websocket = mock_websocket
            self.service.is_connected = True
            self.service.subscribed_assets.add("test-asset")

            await self.service.disconnect_websocket()

            mock_websocket.close.assert_called_once()
            self.assertFalse(self.service.is_connected)
            self.assertEqual(len(self.service.subscribed_assets), 0)

        asyncio.run(run_test())

    def test_subscribe_to_market_channel_not_connected(self):
        """Test market channel subscription when not connected."""
        async def run_test():
            result = await self.service.subscribe_to_market_channel(["asset1", "asset2"])
            self.assertFalse(result)

        asyncio.run(run_test())

    def test_subscribe_to_market_channel_success(self):
        """Test successful market channel subscription."""
        async def run_test():
            # Set up mock websocket
            mock_websocket = AsyncMock()
            self.service.websocket = mock_websocket
            self.service.is_connected = True

            asset_ids = ["asset1", "asset2"]
            result = await self.service.subscribe_to_market_channel(asset_ids)

            self.assertTrue(result)
            self.assertEqual(self.service.subscribed_assets, set(asset_ids))

            # Verify subscription message was sent
            mock_websocket.send.assert_called_once()
            sent_message = json.loads(mock_websocket.send.call_args[0][0])
            self.assertEqual(sent_message["type"], "MARKET")
            self.assertEqual(sent_message["assets_ids"], asset_ids)

        asyncio.run(run_test())

    def test_subscribe_to_market_channel_with_auth(self):
        """Test market channel subscription with authentication."""
        async def run_test():
            # Set up mock websocket and config
            mock_websocket = AsyncMock()
            self.service.websocket = mock_websocket
            self.service.is_connected = True

            with patch('src.services.polymarket_service.config') as mock_config:
                mock_config.POLYMARKET_PRIVY_TOKEN = "test-privy-token"
                mock_config.POLYMARKET_PRIVY_ID_TOKEN = "test-privy-id-token"

                asset_ids = ["asset1"]
                result = await self.service.subscribe_to_market_channel(asset_ids)

                self.assertTrue(result)

                # Verify authentication was included
                sent_message = json.loads(mock_websocket.send.call_args[0][0])
                self.assertIn("auth", sent_message)
                self.assertEqual(sent_message["auth"]["privy_token"], "test-privy-token")
                self.assertEqual(sent_message["auth"]["privy_id_token"], "test-privy-id-token")

        asyncio.run(run_test())

    def test_add_event_handler(self):
        """Test adding event handlers."""
        def mock_handler(data):
            pass

        self.service.add_event_handler("book", mock_handler)
        self.assertIn(mock_handler, self.service.event_handlers["book"])

        # Test invalid event type
        self.service.add_event_handler("invalid_type", mock_handler)
        # Should not raise error but warn

    def test_remove_event_handler(self):
        """Test removing event handlers."""
        def mock_handler(data):
            pass

        # Add handler first
        self.service.add_event_handler("price_change", mock_handler)
        self.assertIn(mock_handler, self.service.event_handlers["price_change"])

        # Remove handler
        self.service.remove_event_handler("price_change", mock_handler)
        self.assertNotIn(mock_handler, self.service.event_handlers["price_change"])

    def test_handle_websocket_message_book_event(self):
        """Test handling book event messages."""
        async def run_test():
            # Set up event handler
            handled_data = None

            def book_handler(data):
                nonlocal handled_data
                handled_data = data

            self.service.add_event_handler("book", book_handler)

            # Create sample book message
            book_message = {
                "event_type": "book",
                "asset_id": "123456",
                "market": "0xabc123",
                "buys": [{"price": "0.48", "size": "30"}],
                "sells": [{"price": "0.52", "size": "25"}]
            }

            await self.service._handle_websocket_message(json.dumps(book_message))

            self.assertIsNotNone(handled_data)
            self.assertEqual(handled_data["event_type"], "book")
            self.assertEqual(handled_data["asset_id"], "123456")

        asyncio.run(run_test())

    def test_handle_websocket_message_invalid_json(self):
        """Test handling invalid JSON messages."""
        async def run_test():
            # Should not raise exception
            await self.service._handle_websocket_message("invalid json")

        asyncio.run(run_test())

    def test_start_consuming_events_not_connected(self):
        """Test starting event consumption when not connected."""
        async def run_test():
            # Should return early and not raise exception
            await self.service.start_consuming_events()

        asyncio.run(run_test())

    def test_subscribe_and_start_consuming_connection_failure(self):
        """Test subscribe_and_start_consuming with connection failure."""
        async def run_test():
            with patch.object(self.service, 'connect_websocket', return_value=False):
                result = await self.service.subscribe_and_start_consuming(["asset1"])
                self.assertFalse(result)

        asyncio.run(run_test())

    def test_subscribe_and_start_consuming_subscription_failure(self):
        """Test subscribe_and_start_consuming with subscription failure."""
        async def run_test():
            with patch.object(self.service, 'connect_websocket', return_value=True):
                with patch.object(self.service, 'subscribe_to_market_channel', return_value=False):
                    with patch.object(self.service, 'disconnect_websocket') as mock_disconnect:
                        result = await self.service.subscribe_and_start_consuming(["asset1"])
                        self.assertFalse(result)
                        mock_disconnect.assert_called_once()

        asyncio.run(run_test())


def run_integration_test():
    """Run integration test with actual API call (commented out for safety)."""
    print("\n" + "="*60)
    print("INTEGRATION TESTS (Manual)")
    print("="*60)
    print("The following integration test is commented out to prevent")
    print("accidental real API calls during automated testing.")
    print("Uncomment and configure with real credentials to test:")
    print()
    print("# Test with a sample slug")
    print('slug = "mlb-sd-mil-2025-06-08"')
    print('print(f"Testing fetch_current_price with slug: {slug}")')
    print('print("-" * 50)')
    print()
    print('result = fetch_current_price(slug)')
    print()
    print('if result:')
    print('    print("Success! Fetched data:")')
    print('    pprint(result)')
    print('else:')
    print('    print("Failed to fetch data.")')


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Run integration test info
    run_integration_test()
