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
        self.clob_api_base = config.POLYMARKET_CLOB_API
        self.websocket_url = config.POLYMARKET_WEBSOCKET_URL
        self.headers = {}

        # WebSocket connection state
        self.websocket = None
        self.is_connected = False
        self.subscribed_assets: Set[str] = set()
        self.event_handlers: Dict[str, List[Callable]] = {
            'book': [],
            'price_change': [],
            'tick_size_change': []
        }

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

    def place_single_order(self, order_data: Dict[str, Any], order_type: str = "GTC") -> Optional[Dict[str, Any]]:
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

    def place_multiple_orders(self, orders_data: List[Dict[str, Any]], order_type: str = "GTC") -> Optional[Dict[str, Any]]:
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
        """
        Connect to the Polymarket WebSocket for real-time data.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Add authentication headers to the connection if available
            extra_headers = {}
            if config.POLYMARKET_PRIVY_TOKEN:
                extra_headers['privy-token'] = config.POLYMARKET_PRIVY_TOKEN
            if config.POLYMARKET_PRIVY_ID_TOKEN:
                extra_headers['privy-id-token'] = config.POLYMARKET_PRIVY_ID_TOKEN

            self.websocket = await websockets.connect(
                self.websocket_url,
                extra_headers=extra_headers if extra_headers else None
            )
            self.is_connected = True
            logger.info(f"Successfully connected to Polymarket WebSocket: {self.websocket_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.is_connected = False
            return False

    async def disconnect_websocket(self):
        """Disconnect from the WebSocket."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            self.is_connected = False
            self.subscribed_assets.clear()
            logger.info("Disconnected from Polymarket WebSocket")

    async def subscribe_to_market_channel(self, asset_ids: List[str]) -> bool:
        """
        Subscribe to the Polymarket Market Channel for specific assets.

        Args:
            asset_ids: List of asset/token IDs to subscribe to

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected. Call connect_websocket() first.")
            return False

        try:
            # Prepare subscription message based on Polymarket documentation
            subscription_message = {
                "auth": {
                    # Add authentication if needed
                },
                "markets": [],  # For user channel
                "assets_ids": asset_ids,  # For market channel
                "type": "MARKET"
            }

            # Remove empty auth if no authentication tokens
            if not config.POLYMARKET_PRIVY_TOKEN and not config.POLYMARKET_PRIVY_ID_TOKEN:
                del subscription_message["auth"]
            else:
                # Add authentication details if available
                if config.POLYMARKET_PRIVY_TOKEN:
                    subscription_message["auth"]["privy_token"] = config.POLYMARKET_PRIVY_TOKEN
                if config.POLYMARKET_PRIVY_ID_TOKEN:
                    subscription_message["auth"]["privy_id_token"] = config.POLYMARKET_PRIVY_ID_TOKEN

            await self.websocket.send(json.dumps(subscription_message))

            # Update subscribed assets
            self.subscribed_assets.update(asset_ids)

            logger.info(f"Subscribed to market channel for assets: {asset_ids}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to market channel: {e}")
            return False

    def add_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """
        Add an event handler for specific event types.

        Args:
            event_type: Type of event ('book', 'price_change', 'tick_size_change')
            handler: Callback function that takes event data as parameter
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
            logger.info(f"Added event handler for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")

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
