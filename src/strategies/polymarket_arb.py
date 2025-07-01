from typing import Dict, Any, List, Callable
from models import SyntheticOrderBook, Order, OrderType, SyntheticOrder, OrderSide
from datetime import datetime
from utils.datetime_utils import datetime_to_epoch

class OrderBuilder:
    def __init__(self, market_slug: str, market_id: int, outcome_name: str, asset_id: int):
        self.market_slug = market_slug
        self.market_id = market_id
        self.outcome_name = outcome_name
        self.asset_id = asset_id
        self.order_type = OrderType.FOK
        self.side = OrderSide.BUY


    def __call__(self, price: float, size: float, timestamp: int) -> Order:
        return Order(
            market_slug = self.market_slug,
            market_id = self.market_id,
            asset_id = self.asset_id,
            outcome_name = self.outcome_name,
            order_type = self.order_type,
            side = self.side,
            price = price,
            size = size,
            timestamp = timestamp
        )

def calculate_orders(book_a: SyntheticOrderBook, book_b: SyntheticOrderBook) -> List[Order]:
    orders_a = sorted(book_a.orders, key=lambda order: order.price)
    orders_b = sorted(book_b.orders, key=lambda order: order.price)

    timestamp = datetime_to_epoch(datetime.now())

    orderBuilder_a = OrderBuilder(book_a.market_slug, book_a.market_id, book_a.outcome_name, book_a.asset_id)
    orderBuilder_b = OrderBuilder(book_b.market_slug, book_b.market_id, book_b.outcome_name, book_b.asset_id)

    return _recurs_build_orders(orders_a, orderBuilder_a, orders_b, orderBuilder_b, timestamp)

def _recurs_build_orders(orders_a: List[SyntheticOrder], orderBuilder_a: OrderBuilder, orders_b: List[SyntheticOrder], orderBuilder_b: OrderBuilder, timestamp) -> List[Order]:
    orders = []

    if orders_a and orders_b:
        a = orders_a[0]
        b = orders_b[0]

        total = a.price + b.price
        if total < 1:
            if a.size < b.size and round(a.size/2) >= 1:
                size = round(a.size/2)
                # TODO: Figure out how to remove all the duplicate extend _build_order calls for each conditional
                orders.extend([
                    orderBuilder_a(a.price, size, timestamp),
                    orderBuilder_b(b.price, size, timestamp)
                ])

                orders_a = orders_a[1:]
                orders_b[0] = SyntheticOrder(side=b.side, price=b.price, size=b.size - a.size)
            elif a.size > b.size and round(b.size/2) >= 1:
                size = round(b.size/2)
                orders.extend([
                    orderBuilder_a(a.price, size, timestamp),
                    orderBuilder_b(b.price, size, timestamp)
                ])

                orders_a[0] = SyntheticOrder(side=a.side, price=a.price, size=a.size - b.size)
                orders_b = orders_b[1:]
            elif a.size == b.size and round(a.size/2) >= 1:
                size = round(a.size/2)
                orders.extend([
                    orderBuilder_a(a.price, size, timestamp),
                    orderBuilder_b(b.price, size, timestamp)
                ])

                orders_a = orders_a[1:]
                orders_b = orders_b[1:]

            orders.extend(_recurs_build_orders(orders_a, orderBuilder_a, orders_b, orderBuilder_b, timestamp))

    return orders

