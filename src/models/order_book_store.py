from typing import List, Self
from src.models import MarketEvent, PriceChangeEvent, BookEvent, SyntheticOrderBook

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

    def update_book(self, market_events: List[MarketEvent]) -> Self:
        for event in market_events:
            synth_orderbook = self.lookup(event.asset_id)
            synth_orderbook.set_timestamp(event.timestamp)

            if isinstance(event, PriceChangeEvent):
                synth_orderbook.add_entries(event.changes)
            elif isinstance(event, BookEvent):
                # We only care about the asks in the orderbook
                synth_orderbook.replace_entries(event.asks)

        return self


