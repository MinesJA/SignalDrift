import json
import logging
from datetime import datetime
from typing import Any, Callable, Optional

import requests
import websockets

from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymarketService:
    def __init__(self):
        self.gamma_api_base = config.POLYMARKET_GAMMA_API
        self.clob_api_base = config.POLYMARKET_CLOB_API if hasattr(config, 'POLYMARKET_CLOB_API') else "https://clob.polymarket.com"
        self.headers = {}

        # WebSocket connection state
        self.websocket = None
        self.is_connected = False
        self.subscribed_assets = set()
        self.event_handlers = {
            "book": [],
            "price_change": [],
            "order_update": []
        }

        # Add authentication headers if tokens are configured
        if config.POLYMARKET_PRIVY_TOKEN:
            self.headers['privy-token'] = config.POLYMARKET_PRIVY_TOKEN
        if config.POLYMARKET_PRIVY_ID_TOKEN:
            self.headers['privy-id-token'] = config.POLYMARKET_PRIVY_ID_TOKEN

    def fetch_current_price(self, slug: str) -> Optional[dict[str, Any]]:
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

    def get_market_by_slug(self, market_slug: str) -> Optional[dict[str, Any]]:
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

    def place_single_order(self, order_data: dict[str, Any], order_type: str = "GTC") -> Optional[dict[str, Any]]:
        """
        Place a single order on Polymarket.

        Args:
            order_data: Dictionary containing order details:
                - order: Signed order object with all required fields
                - owner: API key of order owner
            order_type: Order type ("FOK", "GTC", "GTD", "FAK")

        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - orderId: Unique order identifier
            - orderHashes: Settlement transaction hashes
            - errorMsg: Error message if applicable
        """
        try:
            url = f"{self.clob_api_base}/order"

            payload = {
                "order": order_data["order"],
                "owner": order_data["owner"],
                "orderType": order_type
            }

            headers = {**self.headers, "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info(f"Successfully placed order: {result.get('orderId')}")
            else:
                logger.error(f"Order placement failed: {result.get('errorMsg')}")

            return result

        except Exception as e:
            logger.error(f"Error placing single order: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orderId": None,
                "orderHashes": None
            }

    def place_multiple_orders(self, orders_data: list[dict[str, Any]], order_type: str = "GTC") -> Optional[dict[str, Any]]:
        """
        Place multiple orders in a batch on Polymarket.

        Args:
            orders_data: List of order dictionaries, each containing:
                - order: Signed order object with all required fields
                - owner: API key of order owner
            order_type: Order type for all orders ("FOK", "GTC", "GTD", "FAK")

        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - orderId: ID of the batch order
            - orderHashes: Settlement transaction hashes
            - errorMsg: Error message if applicable

        Note:
            Maximum of 5 orders per batch request
        """
        try:
            if len(orders_data) > 5:
                error_msg = "Maximum of 5 orders per batch request"
                logger.error(error_msg)
                return {
                    "success": False,
                    "errorMsg": error_msg,
                    "orderId": None,
                    "orderHashes": None
                }

            url = f"{self.clob_api_base}/orders"

            # Format orders for batch request
            formatted_orders = []
            for order_data in orders_data:
                formatted_orders.append({
                    "order": order_data["order"],
                    "owner": order_data["owner"],
                    "orderType": order_type
                })

            headers = {**self.headers, "Content-Type": "application/json"}

            response = requests.post(url, json=formatted_orders, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                logger.info(f"Successfully placed batch order: {result.get('orderId')}")
            else:
                logger.error(f"Batch order placement failed: {result.get('errorMsg')}")

            return result

        except Exception as e:
            logger.error(f"Error placing multiple orders: {e}")
            return {
                "success": False,
                "errorMsg": str(e),
                "orderId": None,
                "orderHashes": None
            }

    async def connect_websocket(self) -> bool:
        """Connect to Polymarket WebSocket API."""
        try:
            websocket_url = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
            self.websocket = await websockets.connect(websocket_url)
            self.is_connected = True
            logger.info("Successfully connected to Polymarket WebSocket")
            return True
        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {e}")
            self.is_connected = False
            self.websocket = None
            return False

    async def disconnect_websocket(self):
        """Disconnect from Polymarket WebSocket API."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        self.is_connected = False
        self.websocket = None
        self.subscribed_assets.clear()
        logger.info("Disconnected from Polymarket WebSocket")

    async def subscribe_to_market_channel(self, asset_ids: list[str]) -> bool:
        """Subscribe to market data updates for given asset IDs."""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return False

        try:
            subscription_message = {
                "type": "MARKET",
                "assets_ids": asset_ids
            }

            # Add authentication if available
            if config.POLYMARKET_PRIVY_TOKEN and config.POLYMARKET_PRIVY_ID_TOKEN:
                subscription_message["auth"] = {
                    "privy_token": config.POLYMARKET_PRIVY_TOKEN,
                    "privy_id_token": config.POLYMARKET_PRIVY_ID_TOKEN
                }

            await self.websocket.send(json.dumps(subscription_message))
            self.subscribed_assets.update(asset_ids)
            logger.info(f"Subscribed to market data for assets: {asset_ids}")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to market channel: {e}")
            return False

    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler for specific event types."""
        if event_type not in self.event_handlers:
            logger.warning(f"Unknown event type: {event_type}")
            return

        self.event_handlers[event_type].append(handler)
        logger.info(f"Added event handler for {event_type}")

    def remove_event_handler(self, event_type: str, handler: Callable):
        """Remove an event handler for specific event types."""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"Removed event handler for {event_type}")

    async def _handle_websocket_message(self, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            event_type = data.get("event_type")

            if event_type and event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(data)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
        except json.JSONDecodeError:
            logger.error("Received invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def start_consuming_events(self):
        """Start consuming WebSocket events."""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return

        try:
            async for message in self.websocket:
                await self._handle_websocket_message(message)
        except Exception as e:
            logger.error(f"Error consuming WebSocket events: {e}")
            self.is_connected = False

    async def subscribe_and_start_consuming(self, asset_ids: list[str]) -> bool:
        """Connect, subscribe to assets, and start consuming events."""
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


