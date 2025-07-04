from src.models import OrderBookStore
from datetime import datetime
from typing import List, Dict, Any
import os
import csv

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FIELD_NAMES = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'price', 'size', 'side',  'timestamp']

def write_orderBookStore(market_slug: str, orderBook_store: OrderBookStore, datetime: datetime, test_mode: bool = False):
    test_suffix = "_test" if test_mode else ""
    csv_filename = os.path.join('data', f"{datetime.strftime('%Y%m%d')}_{market_slug}_synthetic-order-book{test_suffix}.csv")

    rows = []

    for book in orderBook_store.books:
        rows.extend(book.asdict_rows())

    if len(rows) == 0:
        return

    logger.info(f"Writing {len(rows)} synthetic orders for market -- {market_slug}")

    _write_to_csv(csv_filename, rows)


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

