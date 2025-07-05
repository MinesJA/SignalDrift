from typing import Dict, Any, List
from src.models import OrderSide
from dataclasses import dataclass, asdict, replace

@dataclass
class SyntheticOrder:
    side: OrderSide
    price: float
    size: float

    def asdict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['side'] = self.side.value
        return data


class SyntheticOrderBook:
    def __init__(self, market_slug: str, market_id: int, outcome_name: str, asset_id: str, timestamp: int):
        self.orders_lookup: Dict[float, SyntheticOrder] = {}
        self.market_slug = market_slug
        self.market_id = market_id
        self.outcome_name = outcome_name
        self.asset_id = asset_id
        self.timestamp = timestamp

    # TODO: Does this need to be a setter or something?
    def set_timestamp(self, timestamp: int):
        self.timestamp = timestamp

    @property
    def orders(self) -> List[SyntheticOrder]:
        return list(self.orders_lookup.values())

    def sorted_orders(self) -> List[SyntheticOrder]:
        return sorted(self.orders, key=lambda order: order.price)

    def add_entries(self, orders: List[SyntheticOrder]):
        for order in orders:
            if order.side == OrderSide.SELL:
                if order.size == 0.0:
                    self.orders_lookup.pop(order.price, None)
                else:
                    self.orders_lookup[order.price] = order

    def replace_entries(self, orders: List[SyntheticOrder]):
        self.orders_lookup = {
            order.price: order
            for order in orders
            if order.size > 0
        }

    def update_entries(self, reduce_size: float, at_price: float, timestamp: int):
        """Reduces size of entires for a particular price"""
        synth_order = self.orders_lookup[at_price]
        new_size = synth_order.size - reduce_size
        self.timestamp = timestamp
        self.orders_lookup[at_price] = replace(synth_order, size=new_size)

    def asdict_rows(self) -> List[Dict[str, Any]]:
        """Creates dict for reach order"""
        return [{**order.asdict(),
            "market_slug": self.market_slug,
            "market_id": self.market_id,
            "asset_id": self.asset_id,
            "outcome_name": self.outcome_name,
            "timestamp": self.timestamp
        } for order in self.sorted_orders()]

