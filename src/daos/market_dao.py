import os
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

from src.utils import setup_logging

logger = setup_logging(__name__)

# TODO: Should this be defined in MarketEvent?
FIELD_NAMES = ['market_slug', 'asset_id', 'market_id', 'event_type', 'price', 'side', 'size', 'hash', 'timestamp']

def write_marketMessages(market_slug: str, datetime: datetime, market_messages: List[Dict[str, Any]]):
    csv_filename = os.path.join('data', f"{datetime.strftime("%Y%m%d")}-{market_slug}-polymarket_market_events.csv")

    rows = []
    for event in market_messages:
        event_rows = _create_rows(market_slug, event)
        if event_rows:
            rows.extend(event_rows)

    try:
        if len(rows) > 0:
            logger.info(f"Writing {len(rows)} market event records to CSV for market_slug: {market_slug}")
            _write_to_csv(csv_filename, rows)
            logger.info(f"Successfully wrote market events to {csv_filename}")
        else:
            logger.warning(f"No market event records to write for market_slug: {market_slug}")
    except Exception as e:
        logger.error(f"Failed to write {len(rows)} market event records for market_slug: {market_slug} - Error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

def _write_to_csv(csv_filename, rows: List[Dict[str, Any]]):
    if not os.path.isfile(csv_filename):
        logger.info(f"Setting up CSV file: {csv_filename}")
        _setup_csv(csv_filename)

    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,
                                    delimiter=',',
                                    quotechar='|',
                                    quoting=csv.QUOTE_MINIMAL,
                                    fieldnames=FIELD_NAMES
                                )
        writer.writerows(rows)


# TODO: Can abstract into util
def _setup_csv(csv_filename: str):
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(FIELD_NAMES)


def _create_price_change_rows(market_slug, event):
    rows = [{
                **event,
                **change,
                "market_slug": market_slug,
                "side": "bid" if change['side'] == 'BUY' else 'ask'
            } for change in event["changes"]]

    return [{key: row.get(key) for key in FIELD_NAMES} for row in rows]


def _create_book_rows(market_slug, event):
    asks = [{**event, **ask, "side": "ask", "market_slug": market_slug} for ask in event["asks"]]
    bids = [{**event, **bid, "side": "bid", "market_slug": market_slug} for bid in event["bids"]]
    rows = asks + bids

    return [{key: row.get(key) for key in FIELD_NAMES} for row in rows]


def _create_rows(market_slug, event) -> Optional[List[Dict[str, Any]]]:
    match event['event_type']:
        case 'price_change':
            return _create_price_change_rows(market_slug, event)
        case 'book':
            return _create_book_rows(market_slug, event)
