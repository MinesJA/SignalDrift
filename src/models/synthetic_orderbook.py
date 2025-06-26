from typing import Dict, Any, List
from collections import namedtuple
from datetime import datetime

SyntheticOrder = namedtuple('synthetic_order', ['side', 'price', 'size', 'timestamp'])

class SyntheticOrderBook:
    def __init__(self, market_slug, market_id, outcome_name: str, asset_id: str):
        self.orders_lookup: Dict[str, SyntheticOrder] = {}
        self.market_slug = market_slug
        self.market_id = market_id
        self.outcome_name = outcome_name
        self.asset_id = asset_id

    @property
    def orders(self) -> List[SyntheticOrder]:
        return list(self.orders_lookup.values())

    def add_entries(self, orders: List[Dict[str, Any]], timestamp):
        for order in orders:
            if order["side"] == "SELL":
                size = float(order["size"])
                if size == 0.0:
                    self.orders_lookup.pop(order["price"], None)
                else:
                    self.orders_lookup[order["price"]] = SyntheticOrder(
                        side="ask",
                        price=float(order["price"]),
                        size=float(order["size"]),
                        timestamp=timestamp
                    )

    def replace_entries(self, orders: List[Dict[str, Any]], timestamp):
        self.orders_lookup = {
            order["price"]: SyntheticOrder(
                side="ask",
                price=float(order["price"]),
                size=float(order["size"]),
                timestamp=timestamp
            )
            for order in orders
            if float(order["size"]) > 0
        }

    def to_orders_dicts(self) -> List[Dict[str, Any]]:
        orders = sorted(self.orders, key=lambda order: order.price)
        return [{ **order._asdict(),
                  "market_slug": self.market_slug,
                  "market_id": self.market_id,
                  "outcome_name": self.outcome_name,
                  "asset_id": self.asset_id }
            for order in orders]




