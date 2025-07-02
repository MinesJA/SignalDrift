import asyncio
import json
import time
import websockets
from src.services import PolymarketClobClient
from src.config import config

from abc import ABC, abstractmethod
from typing import List, Callable, Any

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncWebsocketConnection(ABC):
    def __init__(self, channel_type):
        self.url = config.POLYMARKET_WEBSOCKET_URL
        self.channel_type = channel_type
        self.websocket_url = self.url + "/ws/" + channel_type
        self.websocket = None
        self.ping_task = None
        self.running = False

    @abstractmethod
    async def on_open(self):
        """To be implemented by child class"""
        pass

    @abstractmethod
    async def on_message(self, message: str):
        """To be implemented by child class"""
        pass

    async def on_error(self, error):
        logger.error(f"WebSocket error: {error}")
        raise error

    async def on_close(self):
        logger.info("WebSocket connection closed")
        self.running = False

    async def ping_handler(self):
        """Send ping messages every 10 seconds to keep connection alive"""
        try:
            while self.running and self.websocket:
                await self.websocket.send("PING")
                logger.debug("Sent PING to server")
                await asyncio.sleep(10)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Ping handler stopped - connection closed")
        except Exception as e:
            logger.error(f"Error in ping handler: {e}")

    async def run(self):
        """Run the WebSocket connection with automatic reconnection"""
        retry_delay = 1
        max_retry_delay = 60
        
        while True:
            try:
                logger.info(f"Connecting to WebSocket: {self.websocket_url}")
                async with websockets.connect(self.websocket_url) as websocket:
                    self.websocket = websocket
                    self.running = True
                    retry_delay = 1  # Reset retry delay on successful connection
                    
                    # Start ping task
                    self.ping_task = asyncio.create_task(self.ping_handler())
                    
                    # Call on_open handler
                    await self.on_open()
                    
                    # Listen for messages
                    try:
                        async for message in websocket:
                            if message == "PONG":
                                logger.debug("Received PONG from server")
                                continue
                            await self.on_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket connection closed by server")
                        await self.on_close()
                        break
                        
            except Exception as e:
                await self.on_error(e)
                logger.error(f"WebSocket connection failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
            finally:
                if self.ping_task:
                    self.ping_task.cancel()
                    try:
                        await self.ping_task
                    except asyncio.CancelledError:
                        pass
                self.running = False

class PolymarketUserEventsService(AsyncWebsocketConnection):

    def __init__(self, asset_ids, event_handlers):
        super().__init__("user")
        client = PolymarketClobClient.connect()
        if not client:
            raise Exception("Could not connect to client")

        self.auth = client.derive_auth()
        self.asset_ids = asset_ids
        self.event_handlers = event_handlers

    def channel_type(self):
        return "user"

    def payload(self):
        return {"markets": self.asset_ids, "type": self.channel_type(), "auth": self.auth}

    async def on_open(self):
        await self.websocket.send(json.dumps(self.payload()))
        logger.info(f"Starting user events service")

    async def on_message(self, message: str):
        # Handle PONG messages
        if message == "PONG":
            logger.debug("Received PONG from server")
            return

        try:
            data = json.loads(message)

            for handler in self.event_handlers:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}. Message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            logger.error(message)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")


class PolymarketMarketEventsService(AsyncWebsocketConnection):

    """
    Provides ability to connect to Polymarket websocket for streaming orderbook events

    Attributes:
        market_slug:
        asset_ids:
        event_handlers:
    """
    def __init__(self, market_slug, asset_ids, event_handlers):
        super().__init__("market")
        self.market_slug = market_slug
        self.asset_ids = asset_ids
        self.event_handlers = event_handlers

    @property
    def payload(self):
        return {"assets_ids": self.asset_ids, "type": self.channel_type}

    def channel_type(self):
        return "market"

    async def on_message(self, message: str):
        # Handle PONG messages
        if message == "PONG":
            logger.debug("Received PONG from server")
            return

        try:
            data = json.loads(message)

            # Convert single dict to list for consistency with handlers
            # If data is already a list, keep it as is; if single dict, wrap in list
            if isinstance(data, dict):
                message_list = [data]
            elif isinstance(data, list):
                message_list = data
            else:
                logger.error(f"Unexpected data format: {type(data)}")
                return

            for handler in self.event_handlers:
                try:
                    handler(message_list)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}. Message: {message_list}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            logger.error(message)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def on_open(self):
        await self.websocket.send(json.dumps(self.payload))
        print(f"\n STARTING {self.market_slug} \n")

