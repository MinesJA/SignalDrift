import unittest
import pytest
import asyncio
from unittest.mock import Mock, patch
import json
import logging
from services.polymarket_websocket_events_service import (
    PolymarketMarketEventsService,
    PolymarketUserEventsService
)

class TestPolymarketWebsocketEventsService(unittest.TestCase):

    def setUp(self):
        self.market_slug = "test-market"
        self.asset_ids = ["asset1", "asset2"]
        self.event_handlers = [Mock(), Mock()]
        self.message_callbacks = [Mock(), Mock()]

    @pytest.mark.asyncio
    async def test_market_events_service_handles_pong_message(self):
        """Test that PONG messages are handled without JSON parsing errors"""
        service = PolymarketMarketEventsService(
            self.market_slug,
            self.asset_ids,
            self.event_handlers
        )

        # Test PONG message handling
        with patch('services.polymarket_websocket_events_service.logger') as mock_logger:
            await service.on_message("PONG")

            # Ensure debug log was called
            mock_logger.debug.assert_called_once_with("Received PONG from server")

            # Ensure no event handlers were called
            for handler in self.event_handlers:
                handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_market_events_service_handles_json_messages(self):
        """Test that regular JSON messages are parsed and handled correctly"""
        service = PolymarketMarketEventsService(
            self.market_slug,
            self.asset_ids,
            self.event_handlers
        )

        test_data = {"type": "update", "data": {"price": 100}}

        await service.on_message(json.dumps(test_data))

        # Ensure all event handlers were called with the parsed data wrapped in a list
        for handler in self.event_handlers:
            handler.assert_called_once_with([test_data])

    @pytest.mark.asyncio
    async def test_market_events_service_handles_invalid_json(self):
        """Test that invalid JSON messages are logged as errors"""
        service = PolymarketMarketEventsService(
            self.market_slug,
            self.asset_ids,
            self.event_handlers
        )

        invalid_json = "not a json {invalid"

        with patch('services.polymarket_websocket_events_service.logger') as mock_logger:
            await service.on_message(invalid_json)

            # Ensure error was logged
            self.assertEqual(mock_logger.error.call_count, 2)

            # Ensure no event handlers were called
            for handler in self.event_handlers:
                handler.assert_not_called()

    @pytest.mark.asyncio
    @patch('services.polymarket_websocket_events_service.PolymarketClobClient')
    async def test_user_events_service_handles_pong_message(self, mock_clob_client):
        """Test that UserEventsService handles PONG messages correctly"""
        # Mock the client
        mock_client = Mock()
        mock_client.derive_auth.return_value = {"token": "test"}
        mock_clob_client.connect.return_value = mock_client

        service = PolymarketUserEventsService(
            self.asset_ids,
            self.message_callbacks
        )

        with patch('services.polymarket_websocket_events_service.logger') as mock_logger:
            await service.on_message("PONG")

            # Ensure debug log was called
            mock_logger.debug.assert_called_once_with("Received PONG from server")

            # Ensure no callbacks were called
            for callback in self.message_callbacks:
                callback.assert_not_called()

    @pytest.mark.asyncio
    @patch('services.polymarket_websocket_events_service.PolymarketClobClient')
    async def test_user_events_service_handles_json_messages(self, mock_clob_client):
        """Test that UserEventsService handles JSON messages correctly"""
        # Mock the client
        mock_client = Mock()
        mock_client.derive_auth.return_value = {"token": "test"}
        mock_clob_client.connect.return_value = mock_client

        service = PolymarketUserEventsService(
            self.asset_ids,
            self.message_callbacks
        )

        test_data = {"type": "user_update", "data": {"balance": 1000}}

        await service.on_message(json.dumps(test_data))

        # Ensure all callbacks were called with the parsed data
        for callback in self.message_callbacks:
            callback.assert_called_once_with(test_data)

if __name__ == '__main__':
    unittest.main()
