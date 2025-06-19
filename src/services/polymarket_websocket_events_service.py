from websocket import WebSocketApp
import json
import time
import threading
from typing import Self, Callable, List, Dict
from services import PolymarketClobClient
from config import config


from abc import ABC, abstractmethod

from src.utils import setup_logging

logger = setup_logging(__name__)

class WebsocketConnection(ABC):
    def __init__(self, channel_type):
        self.url = config.POLYMARKET_WEBSOCKET_URL
        furl = self.url + "/ws/" + channel_type

        self.channel_type = channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

    @abstractmethod
    def on_open(self, ws):
        """To be implemented by child class"""
        pass

    @abstractmethod
    def on_message(self, ws, message):
        """To be implemented by child class"""
        pass

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket closing - Status: {close_status_code}, Message: {close_msg}")
        exit(0)

    def ping(self, ws):
        while True:
            ws.send("PING")
            time.sleep(10)

    def run(self):
        self.ws.run_forever()

class PolymarketUserEventsService(WebsocketConnection):

    def __init__(self, asset_ids, message_callbacks):
        super().__init__("user")
        client = PolymarketClobClient.connect()
        if not client:
            raise Exception("Could not connect to client")

        self.auth = client.derive_auth()
        self.asset_ids = asset_ids
        self.message_callbacks = message_callbacks

    def payload(self):
        return {"markets": self.asset_ids, "type": self.channel_type(), "auth": self.auth}


class PolymarketMarketEventsService(WebsocketConnection):

    """
    Provdies ability to connect to Polymarket websocket for streaming orderbook events

    Attributes:
        channel_type: ...
    """
    def __init__(self,market_slug, asset_ids, event_handlers):
        super().__init__("market")
        self.market_slug = market_slug
        self.asset_ids = asset_ids
        self.event_handlers = event_handlers

    @property
    def payload(self):
        return {"assets_ids": self.asset_ids, "type": self.channel_type}

    def channel_type(self):
        return "market"

    def on_message(self, ws, message):
        if message == "PONG":
            return
            
        try:
            data = json.loads(message)
            for handler in self.event_handlers:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}. Message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            logger.error(message)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
        finally:
            pass

    def on_open(self, ws):
        ws.send(json.dumps(self.payload))

        thr = threading.Thread(target=self.ping, args=(ws,))
        print(f"\n STARTING {self.market_slug} \n")
        thr.start()

