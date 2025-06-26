from collections.abc import Callable
from datetime import datetime
from typing import Dict, Any, List
import json
from concurrent.futures import ThreadPoolExecutor
from strategies import calculate_orders
from services import PolymarketService, PolymarketMarketEventsService
from models import EventType, SyntheticOrderBook, OrderBookStore, Order
from daos import write_marketMessages, write_orderBookStore, write_orders
import traceback

class OrdersStore:
    def __init__(self):
        self.orders = []

    def add_order(self, order: Order):
        self.orders.append(order)

    def add_orders(self, orders: List[Order]):
        self.orders.extend(orders)


def get_arb_strategy(orderbook_store: OrderBookStore, order_store: OrdersStore) -> Callable:
    def handler(_order_message: List[Dict[str, Any]]):
        book_a, book_b = orderbook_store.books
        orders = calculate_orders(book_a, book_b)
        order_store.add_orders(orders)

        return order_store

    return handler


def get_order_message_register(orderBook_store: OrderBookStore, order_store: OrdersStore) -> Callable:
    def handler(market_message: List[Dict[str, Any]]):
        try:
            now = datetime.now()

            book_store = orderBook_store.update_book(market_message)
            book_a, book_b = book_store.books

            # TODO: Rename to make it clear this is strategy execution
            orders = calculate_orders(book_a, book_b)
            order_store.add_orders(orders)

            # Get market_id from the first book (all books should have the same market_id)
            market_id = book_store.books[0].market_id if book_store.books else None
            
            write_marketMessages(book_store.market_slug, now, market_message, market_id)
            write_orderBookStore(book_store.market_slug, now, book_store)
            write_orders(book_store.market_slug, now, orders)
        except Exception:
            print("ERROR ERROR ERROR")
            print(traceback.format_exc())

    return handler


def run_market_connection(market_slug: str):
    """Run a single market connection in its own thread"""
    try:
        print(f"Starting market connection for {market_slug}")
        market_metadata = PolymarketService().get_market_by_slug(market_slug)

        if market_metadata:
            books = [
                SyntheticOrderBook(market_slug, market_metadata['id'], outcome, token_id)
                for token_id, outcome
                in zip(json.loads(market_metadata['clobTokenIds']), json.loads(market_metadata['outcomes']))
            ]

            book_store = OrderBookStore(market_slug, books)
            order_store = OrdersStore()
            message_handler = get_order_message_register(book_store, order_store)

            market_connection = PolymarketMarketEventsService(market_slug, book_store.asset_ids, [message_handler])
            market_connection.run()
        else:
            print(f"No metadata found for market {market_slug}")
    except Exception as e:
        print(f"Error in market connection {market_slug}: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    #slug = "mlb-phi-mia-2025-06-17"
    #slug = "mlb-mil-chc-2025-06-17"
    #slug="mlb-cle-sf-2025-06-17"
    #market_slug="mlb-sd-lad-2025-06-17"

    #market_slugs = [
    #   "mlb-min-cin-2025-06-19",
    #   "mlb-laa-nyy-2025-06-19",
    #   "mlb-col-wsh-2025-06-19",
    #   "mlb-mil-chc-2025-06-19",
    #   "mlb-kc-tex-2025-06-19",
    #   "mlb-ari-tor-2025-06-19",
    #   "mlb-cle-sf-2025-06-19",
    #   "mlb-pit-det-2025-06-19"
    #
    #]

    market_slugs=[
        "mlb-tex-bal-2025-06-25",
        "mlb-oak-det-2025-06-25",
        "mlb-tor-cle-2025-06-25",
        "mlb-atl-nym-2025-06-25",
        "mlb-nyy-cin-2025-06-25",
        "mlb-sea-min-2025-06-25",
        "mlb-tb-kc-2025-06-25",
        "mlb-chc-stl-2025-06-25"
    ]
    # Create thread pool with max workers equal to number of markets
    with ThreadPoolExecutor(max_workers=len(market_slugs)) as executor:
        # Submit all market connections to run concurrently
        futures = []
        for market_slug in market_slugs:
            future = executor.submit(run_market_connection, market_slug)
            futures.append(future)

        print(f"Started {len(futures)} market connections")

        # Keep main thread alive while workers are running
        try:
            # Wait for all threads to complete (they won't unless there's an error)
            for future in futures:
                future.result()
        except KeyboardInterrupt:
            print("\nShutting down market connections...")
            executor.shutdown(wait=False)