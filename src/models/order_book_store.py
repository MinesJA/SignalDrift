from typing import List, Dict, Any
from . import SyntheticOrderBook

class OrderBookStore:
    def __init__(self, market_slug: str, market_id: int, books: List[SyntheticOrderBook]):
        self.market_slug = market_slug
        self.market_id = market_id
        self.books_lookup = {book.asset_id: book for book in books}

    @property
    def books(self) -> List[SyntheticOrderBook]:
        return list(self.books_lookup.values())

    @property
    def asset_ids(self) -> List[str]:
        return list(self.books_lookup.keys())

    def lookup(self, asset_id) -> SyntheticOrderBook:
        return self.books_lookup[asset_id]

    def lookups(self, asset_ids: List[str]) -> List[SyntheticOrderBook]:
        return [self.books_lookup[asset_id] for asset_id in asset_ids]

    def update_book(self, market_orders: List[Dict[str, Any]]) -> 'OrderBookStore':
        for order in market_orders:
            synth_orderbook = self.lookup(order["asset_id"])
            # TODO: Was trying to match on ENUM but that doesnt work
            # will probably have to change those to constants
            match order["event_type"]:
                case "event_type":
                    synth_orderbook.add_entries(order["changes"], order["timestamp"])
                case "book":
                    synth_orderbook.replace_entries(order["asks"], order["timestamp"])

        return self


