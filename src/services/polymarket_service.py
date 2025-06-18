import requests
import json
import asyncio
import websockets
from datetime import datetime
from typing import Dict, Optional, Any, List, Union, Callable, Set
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymarketService:
    def __init__(self):
        self.gamma_api_base = config.POLYMARKET_GAMMA_API
        self.websocket_url = config.POLYMARKET_WEBSOCKET_URL
        self.headers = {}

        # WebSocket connection state

        # Add authentication headers if tokens are configured
        if config.POLYMARKET_PRIVY_TOKEN:
            self.headers['privy-token'] = config.POLYMARKET_PRIVY_TOKEN
        if config.POLYMARKET_PRIVY_ID_TOKEN:
            self.headers['privy-id-token'] = config.POLYMARKET_PRIVY_ID_TOKEN

    def fetch_current_price(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current market price for two teams given a slug.

        Args:
            slug: Market slug, e.g., 'mlb-sd-mil-2025-06-08'

        Returns:
            Dictionary containing:
            - team_name_a: float (price)
            - team_name_b: float (price)
            - fetched_at: datetime (time request was made)
            - updated_at: datetime (from request)
        """
        fetched_at = datetime.now()

        try:
            # Get market information using Gamma API
            market = self.get_market_by_slug(slug)
            if not market:
                logger.error(f"No market found for slug: {slug}")
                return None

            # Extract market data
            outcomes = json.loads(market.get('outcomes', '[]'))
            outcome_prices = json.loads(market.get('outcomePrices', '[]'))

            if len(outcomes) != 2 or len(outcome_prices) != 2:
                logger.error(f"Invalid market data: expected 2 outcomes, got {len(outcomes)}")
                return None

            # Get current prices from market data
            team_a, team_b = outcomes[0], outcomes[1]
            price_a, price_b = float(outcome_prices[0]), float(outcome_prices[1])

            # Get updated_at time from market data
            updated_at_str = market.get('updatedAt', '')
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))

            result = {
                team_a: price_a,
                team_b: price_b,
                'fetched_at': fetched_at,
                'updated_at': updated_at
            }

            logger.info(f"Successfully fetched prices for {slug}: {team_a}={price_a}, {team_b}={price_b}")
            return result

        except Exception as e:
            logger.error(f"Error fetching prices for {slug}: {e}")
            return None

    def get_market_by_slug(self, market_slug: str) -> Optional[Dict[str, Any]]:
        """Get market information using the Gamma API."""
        try:
            url = f"{self.gamma_api_base}/markets"
            params = {
                'slug': market_slug,
                'active': True,
                'closed': False
            }

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            markets = response.json()

            if not markets:
                return None

            return markets[0]  # Return the first matching market

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching market data: {e}")
            return None




    def remove_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Remove an event handler for specific event types.

        Args:
            event_type: Type of event ('book', 'price_change', 'tick_size_change')
            handler: Callback function to remove
        """
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"Removed event handler for {event_type}")

    async def _handle_websocket_message(self, message: str):
        """
        Handle incoming WebSocket messages and trigger appropriate event handlers.

        Args:
            message: Raw message string from WebSocket
        """
        try:
            data = json.loads(message)
            event_type = data.get('event_type')

            if event_type in self.event_handlers:
                # Call all registered handlers for this event type
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(data)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {e}")
            else:
                logger.debug(f"Unhandled event type: {event_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def start_consuming_events(self):
        """
        Start consuming events from the WebSocket connection.
        This method will run indefinitely until the connection is closed.
        """
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected. Call connect_websocket() first.")
            return

        logger.info("Starting to consume WebSocket events...")

        try:
            async for message in self.websocket:
                await self._handle_websocket_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error consuming WebSocket events: {e}")
            self.is_connected = False

    async def subscribe_and_start_consuming(self, asset_ids: List[str]) -> bool:
        """
        Convenience method to connect, subscribe to market channel, and start consuming events.

        Args:
            asset_ids: List of asset/token IDs to subscribe to

        Returns:
            bool: True if setup successful, False otherwise
        """
        # Connect to WebSocket
        if not await self.connect_websocket():
            return False

        # Subscribe to market channel
        if not await self.subscribe_to_market_channel(asset_ids):
            await self.disconnect_websocket()
            return False

        # Start consuming events (this will run indefinitely)
        await self.start_consuming_events()
        return True


# Create a module-level instance for convenience
_service = PolymarketService()
fetch_current_price = _service.fetch_current_price
place_single_order = _service.place_single_order
place_multiple_orders = _service.place_multiple_orders
get_market_by_slug = _service.get_market_by_slug
# WebSocket functions
connect_websocket = _service.connect_websocket
disconnect_websocket = _service.disconnect_websocket
subscribe_to_market_channel = _service.subscribe_to_market_channel
add_event_handler = _service.add_event_handler
remove_event_handler = _service.remove_event_handler
start_consuming_events = _service.start_consuming_events
subscribe_and_start_consuming = _service.subscribe_and_start_consuming
