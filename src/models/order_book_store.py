from typing import List
from . import SyntheticOrderBook

class OrderBookStore:
    def __init__(self, market_slug: str, books: List[SyntheticOrderBook]):
        self.market_slug = market_slug
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


