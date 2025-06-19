import os
import csv
from typing import List, Dict, Any
from datetime import datetime
from models import Order
from utils import setup_logging

logger = setup_logging(__name__)

FIELD_NAMES = ['market_slug', 'asset_id', 'price', 'size', 'timestamp']

def write_orders(market_slug: str, datetime: datetime, orders: List[Order]):
    csv_filename = os.path.join('data', f"{datetime.strftime("%Y%m%d-%H")}-{market_slug}_orders.csv")

    rows = [order.asdict() for order in orders]

    logger.info(f"Writing {len(rows)} order records to CSV for market_slug: {market_slug}")
    _write_to_csv(csv_filename, rows)
    logger.info(f"Successfully wrote orders to {csv_filename}")


# TODO: This can prob be abstracted into csv utils
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

