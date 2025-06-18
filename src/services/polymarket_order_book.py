from websocket import WebSocketApp
import json
import time
import threading

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"


class PolymarketOrderBook:
    """
    Provdies ability to connect to Polymarket websocket for streaming orderbook events

    Attributes:
        channel_type: ...
    """
    def __init__(self, channel_type, url, data, auth, message_callback, verbose):
        self.channel_type = channel_type
        self.url = url
        self.data = data
        self.auth = auth
        self.message_callback = message_callback
        self.verbose = verbose
        furl = url + "/ws/" + channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self.orderbooks = {}
        self.event_handlers: Dict[str, List[Callable]] = {
            'book': [],
            'price_change': [],
            'tick_size_change': []
        }

    def on_message(self, ws, message):
        try:
            m = json.loads(message)
            #pprint.pp(m)
            if self.message_callback:
                self.message_callback.handle_order_message(m)

        except ValueError:
            print(message)
        finally:
            pass

    # TODO: use to replace above method
    def on_message():
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

    def on_error(self, ws, error):
        print("Error: ", error)
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        print("closing")
        exit(0)

    def on_open(self, ws):
        if self.channel_type == MARKET_CHANNEL:
            ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL}))
        elif self.channel_type == USER_CHANNEL and self.auth:
            ws.send(
                json.dumps(
                    {"markets": self.data, "type": USER_CHANNEL, "auth": self.auth}
                )
            )
        else:
            exit(1)

        thr = threading.Thread(target=self.ping, args=(ws,))
        thr.start()

    def ping(self, ws):
        while True:
            ws.send("PING")
            time.sleep(10)

    def run(self):
        self.ws.run_forever()


