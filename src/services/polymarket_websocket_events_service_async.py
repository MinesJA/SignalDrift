import asyncio
import json
import logging
from typing import List, Dict, Callable
from abc import ABC, abstractmethod
import websockets
from websockets.exceptions import ConnectionClosed
from services import PolymarketClobClient
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncWebsocketConnection(ABC):
    def __init__(self, channel_type):
        self.url = config.POLYMARKET_WEBSOCKET_URL
        self.furl = f"{self.url}/ws/{channel_type}"
        self.channel_type = channel_type
        self.ws = None
        self._ping_task = None

    @abstractmethod
    async def on_open(self):
        """To be implemented by child class"""
        pass

    @abstractmethod
    async def on_message(self, message):
        """To be implemented by child class"""
        pass

    async def on_error(self, error):
        logger.error(f"WebSocket error: {error}")
        raise error

    async def on_close(self):
        logger.info("WebSocket connection closed")

    async def ping(self):
        """Send periodic ping messages to keep connection alive"""
        try:
            while True:
                if self.ws and not self.ws.closed:
                    await self.ws.send("PING")
                    logger.debug("Sent PING")
                await asyncio.sleep(10)
        except ConnectionClosed:
            logger.info("Ping task stopped due to closed connection")
        except Exception as e:
            logger.error(f"Error in ping task: {e}")

    async def run(self):
        """Main connection loop with automatic reconnection"""
        while True:
            try:
                async with websockets.connect(self.furl) as websocket:
                    self.ws = websocket
                    logger.info(f"Connected to {self.furl}")
                    
                    # Start ping task
                    self._ping_task = asyncio.create_task(self.ping())
                    
                    # Call on_open handler
                    await self.on_open()
                    
                    # Message handling loop
                    async for message in websocket:
                        await self.on_message(message)
                        
            except ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await self.on_error(e)
                await asyncio.sleep(5)  # Wait before reconnecting
            finally:
                if self._ping_task and not self._ping_task.done():
                    self._ping_task.cancel()
                    try:
                        await self._ping_task
                    except asyncio.CancelledError:
                        pass
                await self.on_close()


class AsyncPolymarketUserEventsService(AsyncWebsocketConnection):
    def __init__(self, asset_ids, message_callbacks):
        super().__init__("user")
        client = PolymarketClobClient.connect()
        if not client:
            raise Exception("Could not connect to client")

        self.auth = client.derive_auth()
        self.asset_ids = asset_ids
        self.message_callbacks = message_callbacks

    @property
    def payload(self):
        return {"markets": self.asset_ids, "type": "user", "auth": self.auth}

    async def on_open(self):
        await self.ws.send(json.dumps(self.payload))
        logger.info(f"Started user events service")

    async def on_message(self, message):
        # Handle PONG messages
        if message == "PONG":
            logger.debug("Received PONG from server")
            return

        try:
            data = json.loads(message)
            for callback in self.message_callbacks:
                try:
                    # Support both sync and async callbacks
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}. Message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            logger.error(message)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")


class AsyncPolymarketMarketEventsService(AsyncWebsocketConnection):
    """
    Provides ability to connect to Polymarket websocket for streaming orderbook events

    Attributes:
        channel_type: The type of WebSocket channel
        market_slug: The market identifier
        asset_ids: List of asset IDs to subscribe to
        event_handlers: List of callback functions to handle events
    """

    def __init__(self, market_slug, asset_ids, event_handlers):
        super().__init__("market")
        self.market_slug = market_slug
        self.asset_ids = asset_ids
        self.event_handlers = event_handlers

    @property
    def payload(self):
        return {"assets_ids": self.asset_ids, "type": self.channel_type}

    async def on_open(self):
        await self.ws.send(json.dumps(self.payload))
        logger.info(f"Started market events service for {self.market_slug}")

    async def on_message(self, message):
        # Handle PONG messages
        if message == "PONG":
            logger.debug("Received PONG from server")
            return

        try:
            data = json.loads(message)
            for handler in self.event_handlers:
                try:
                    # Support both sync and async handlers
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}. Message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            logger.error(message)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")