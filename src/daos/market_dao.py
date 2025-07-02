import os
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.models import MarketEvent

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Should this be defined in MarketEvent?
FIELD_NAMES = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'event_type', 'price', 'side', 'size', 'hash', 'timestamp']

def write_marketEvents(market_slug: str, market_id: int, market_events: List[MarketEvent], datetime: datetime,  test_mode: bool = False):
    test_suffix = "_test" if test_mode else ""
    csv_filename = os.path.join('data', f"{datetime.strftime('%Y%m%d')}_{market_slug}_polymarket-market-events{test_suffix}.csv")

    if len(market_events) == 0:
        return

    logger.info(f"Writing {len(market_events)} market events for market -- {market_slug}")

    rows = []
    for event in market_events:
        event_rows = _create_rows(event, market_id)
        if event_rows:
            rows.extend(event_rows)

    try:
        if len(rows) > 0:
            _write_to_csv(csv_filename, rows)
    except Exception:
        logger.error(f"Failed to write rows in market_writer")

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

def _create_rows(event: MarketEvent, market_id: int) -> Optional[List[Dict[str, Any]]]:
    rows = event.asdict_rows()
    #TODO: Prob a faster way to do this
    rows = [{**row, 'market_id': market_id} for row in rows]
    return [{key: row.get(key) for key in FIELD_NAMES} for row in rows]

