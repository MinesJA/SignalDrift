import os
import csv
from typing import Dict, Any, List, Optional


# TODO: Should this be defined in MarketEvent?
FIELD_NAMES = ['market_slug', 'asset_id', 'market', 'event_type', 'price', 'side', 'size', 'hash', 'timestamp']

def create_market_event(data):
    raise Exception("Not implemented")

def create_price_change_rows(market_slug, event):
    rows = [{
                **event,
                **change,
                "market_slug": market_slug,
                "side": "bid" if change['side'] == 'BUY' else 'ask'
            } for change in event["changes"]]

    return [{key: row.get(key) for key in FIELD_NAMES} for row in rows]

def create_book_rows(market_slug, event):
    asks = [{**event, **ask, "side": "ask", "market_slug": market_slug} for ask in event["asks"]]
    bids = [{**event, **bid, "side": "bid", "market_slug": market_slug} for bid in event["bids"]]
    rows = asks + bids

    return [{key: row.get(key) for key in FIELD_NAMES} for row in rows]

def create_rows(market_slug, event) -> Optional[List[Dict[str, Any]]]:
    match event['event_type']:
        case 'price_change':
            return create_price_change_rows(market_slug, event)
        case 'book':
            return create_book_rows(market_slug, event)
        case _:
            # Do nothin, we only care about book and price_change for now


def create_market_events(market_slug, events):
    for event in events:

        if event['event_type'] == 'price_change':

        if event['event_type'] == 'book':

    csv_market_event_writer(market_slug, data)


def csv_market_event_writer(market_slug, dict_rows):
    csv_filename = os.path.join('data', f"poly_market_price_change_event_{market_slug}.csv")

    if not os.path.isfile(csv_filename):
        raise Exception(f"CSV {csv_filename} does not exist. Cannot write market_event")

    with open(csv_filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,
                                delimiter=',',
                                quotechar='|',
                                quoting=csv.QUOTE_MINIMAL,
                                fieldnames=FIELD_NAMES
                            )


    def csv_writer(self, data):
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        csv_filename = os.path.join('data', f"poly_market_price_change_event_{self.market_slug}.csv")

        with open(csv_filename, 'a', newline='') as csvfile:
            fieldnames=['asset_id', 'event_type', 'hash', 'market', 'price', 'side', 'size', 'timestamp']
            writer = csv.DictWriter(csvfile,
                                    delimiter=',',
                                    quotechar='|',
                                    quoting=csv.QUOTE_MINIMAL,
                                    fieldnames=fieldnames
                                )

