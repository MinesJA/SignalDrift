from models import OrderBookStore
from datetime import datetime
from typing import List, Dict, Any
import os
import csv

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FIELD_NAMES = ['market_slug', 'asset_id', 'market_id', 'outcome_name', 'price', 'size', 'side',  'timestamp']

def write_orderBookStore(market_slug: str, datetime: datetime, orderBook_store: OrderBookStore):
    logger.info("Writing order book")
    csv_filename = os.path.join('data', f"{datetime.strftime("%Y%m%d")}-{market_slug}-synthetic_orders.csv")

    rows = []


    for book in orderBook_store.books:
        rows.extend(book.to_orders_dicts())

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

