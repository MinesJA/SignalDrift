import os
import csv
from typing import List, Dict, Any
from datetime import datetime
from models import Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FIELD_NAMES = ['asset_id', 'market_slug', 'order_type', 'price', 'size', 'timestamp']

def write_orders(market_slug: str, datetime: datetime, orders: List[Order], test_mode: bool = False):

    logger.info("Writing orders")
    test_suffix = "_test" if test_mode else ""
    csv_filename = os.path.join('data', f"{datetime.strftime('%Y%m%d')}_{market_slug}_orders{test_suffix}.csv")

    rows = [order.asdict() for order in orders]
    
    # Validate that Order attributes match expected field names
    if rows:
        order_fields = set(rows[0].keys())
        expected_fields = set(FIELD_NAMES)
        if order_fields != expected_fields:
            missing_fields = expected_fields - order_fields
            extra_fields = order_fields - expected_fields
            error_msg = f"Order fields mismatch. Missing: {missing_fields}, Extra: {extra_fields}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    _write_to_csv(csv_filename, rows)


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

