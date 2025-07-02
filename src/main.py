from collections.abc import Callable
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import os
import sys
import traceback
import asyncio
from src.strategies import calculate_orders
from src.services import PolymarketService, PolymarketMarketEventsService
from src.models import MarketEvent, SyntheticOrderBook, OrderBookStore, Order
from src.daos import write_marketEvents, write_orderBookStore, write_orders, write_metadata
from src.utils import datetime_to_epoch, CSVMessageProcessor

class OrdersStore:
    def __init__(self):
        self.orders = []

    def add_order(self, order: Order):
        self.orders.append(order)

    def add_orders(self, orders: List[Order]):
        self.orders.extend(orders)


# TODO: Could use the same pattern as OrderBuilder in polymarket_arb
def get_order_message_register(orderBook_store: OrderBookStore, order_store: OrdersStore, test_mode: bool = False) -> Callable:
    def handler(events: List[Dict[str, Any]]):
        try:
            now = datetime.now()
            #TODO: Refactor, this is ugly
            market_events = [MarketEvent.from_dict(
                {**market_eventdict,
                 "market_slug": orderBook_store.market_slug,
                 "market_id": orderBook_store.market_id,
                 "outcome_name": orderBook_store.lookup(market_eventdict["asset_id"]).outcome_name}
            ) for market_eventdict in events
            if market_eventdict["event_type"] == "book"
                or market_eventdict["event_type"] == "price_change" ]

            book_store = orderBook_store.update_book(market_events)
            book_a, book_b = book_store.books

            # TODO: Rename to make it clear this is strategy execution
            orders = calculate_orders(book_a, book_b)
            order_store.add_orders(orders)

            write_marketEvents(
                market_slug=book_store.market_slug,
                market_id=book_store.market_id,
                market_events=market_events,
                datetime=now,
                test_mode=test_mode
            )
            write_orderBookStore(
                market_slug=book_store.market_slug,
                orderBook_store=book_store,
                datetime=now,
                test_mode=test_mode
            )
            write_orders(
                market_slug=book_store.market_slug,
                orders=orders,
                datetime=now,
                test_mode=test_mode
            )
        except Exception:
            print("ERROR ERROR ERROR")
            print(traceback.format_exc())

    return handler


async def run_market_connection(market_slug: str, csv_file_path: Optional[str] = None):
    """
    Run a single market connection asynchronously.

    Args:
        market_slug: The market slug identifier
        csv_file_path: Optional path to CSV file for testing. If provided, runs from CSV data instead of websocket.
    """
    try:
        print(f"Starting market connection for {market_slug}")

        # Determine if we're running in test mode (from CSV)
        test_mode = csv_file_path is not None

        market_metadata = PolymarketService().get_market_by_slug(market_slug)

        if market_metadata:
            timestamp = datetime_to_epoch(datetime.now())
            books = [
                SyntheticOrderBook(market_slug, market_metadata['id'], outcome_name, asset_id, timestamp)
                for asset_id, outcome_name
                in zip(json.loads(market_metadata['clobTokenIds']), json.loads(market_metadata['outcomes']))
            ]

            book_store = OrderBookStore(market_slug, market_metadata['id'], books)
            order_store = OrdersStore()
            message_handler = get_order_message_register(book_store, order_store, test_mode=test_mode)

            # Write metadata at the start of the run (only for live system, not CSV mode)
            if not test_mode:
                executed_at = datetime.now()
                write_metadata(
                    market_slug=market_slug,
                    market_id=market_metadata['id'],
                    books=books,
                    executed_at=executed_at
                )

            if test_mode:
                # Run from CSV file
                print(f"Running from CSV file: {csv_file_path}")
                csv_processor = CSVMessageProcessor(csv_file_path, [message_handler])
                csv_processor.run()
                print(f"Completed CSV processing for {market_slug}")
            else:
                # Run from websocket (original behavior)
                market_connection = PolymarketMarketEventsService(market_slug, book_store.asset_ids, [message_handler])
                await market_connection.run()
        else:
            print(f"No metadata found for market {market_slug}")
    except Exception as e:
        print(f"Error in market connection {market_slug}: {e}")
        traceback.print_exc()


def extract_market_slug_from_filename(filename: str) -> str:
    """
    Extract market slug from filename.

    Args:
        filename: Filename like "20250619_mlb-tb-kc-2025-06-24"

    Returns:
        Market slug like "mlb-tb-kc-2025-06-24"
    """
    # Remove the date prefix (YYYYMMDD_)
    parts = filename.split('_', 1)
    if len(parts) >= 2:
        return parts[1]
    return filename


def get_csv_file_path(filename: str) -> str:
    """
    Get the CSV file path from filename.

    Args:
        filename: Base filename like "20250619_mlb-tb-kc-2025-06-24"

    Returns:
        Full path to the polymarket_market_events.csv file
    """
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    csv_filename = f"{filename}_polymarket-market-events.csv"
    return os.path.join(data_dir, csv_filename)


if __name__ == "__main__":
    # Check if CSV file is provided via environment variable or command line
    csv_filename = os.environ.get('CSV_FILE')

    if csv_filename:
        # Running from CSV file (test mode)
        try:
            csv_file_path = get_csv_file_path(csv_filename)
            market_slug = extract_market_slug_from_filename(csv_filename)

            print(f"Running in test mode from CSV file: {csv_file_path}")
            print(f"Market slug: {market_slug}")

            # Validate file exists
            if not os.path.exists(csv_file_path):
                print(f"Error: CSV file not found: {csv_file_path}")
                print(f"Make sure the file exists in the data directory.")
                sys.exit(1)

            # Basic validation of filename format
            if not csv_filename.endswith('_polymarket-market-events'):
                expected_filename = f"{csv_filename}_polymarket-market-events.csv"
                print(f"Warning: Expected filename format: {expected_filename}")

            # Run single market from CSV
            asyncio.run(run_market_connection(market_slug, csv_file_path))
            print("CSV processing completed successfully")

        except KeyboardInterrupt:
            print("\nShutting down CSV processing...")
        except Exception as e:
            print(f"Error during CSV processing: {e}")
            traceback.print_exc()
            sys.exit(1)

    else:
        # Running from websocket (live mode)
        print("Running in live mode from websocket connections")

        #market_slugs = [
        #    "mlb-tex-bal-2025-06-25",
        #    "mlb-oak-det-2025-06-25",
        #    "mlb-tor-cle-2025-06-25",
        #    "mlb-atl-nym-2025-06-25",
        #    "mlb-nyy-cin-2024-06-25",
        #    "mlb-sea-min-2025-06-25",
        #    "mlb-tb-kc-2025-06-25",
        #    "mlb-chc-stl-2025-06-25"
        #]

        #"mlb-kc-sea-2025-06-30",
        #"mlb-sf-ari-2025-06-30",

        market_slugs = [
            "mlb-min-mia-2025-07-01",
            "mlb-stl-pit-2025-07-01",
            "mlb-det-wsh-2025-07-01",
            "mlb-det-tb-2025-07-01",
            "mlb-cin-bos-2025-07-01"
        ]

        # Create async tasks for all market connections
        async def run_all_connections():
            # Create all market connection tasks
            tasks = []
            for market_slug in market_slugs:
                task = asyncio.create_task(run_market_connection(market_slug))
                tasks.append(task)

            print(f"Started {len(tasks)} market connections")

            try:
                # Run all connections concurrently
                await asyncio.gather(*tasks)
            except KeyboardInterrupt:
                print("\nShutting down market connections...")
                # Cancel all remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()
                # Wait for all tasks to finish cancellation
                await asyncio.gather(*tasks, return_exceptions=True)

        # Run the async function
        asyncio.run(run_all_connections())

