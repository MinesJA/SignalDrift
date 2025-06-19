from typing import Dict, Any, List
from models import SyntheticOrderBook, Order, OrderType, SyntheticOrder
from datetime import datetime

def calculate_orders(book_a: SyntheticOrderBook, book_b: SyntheticOrderBook) -> List[Order]:
    orders_a = sorted(book_a.orders, key=lambda order: order.price)
    orders_b = sorted(book_b.orders, key=lambda order: order.price)

    timestamp = round(datetime.now().timestamp() * 1000)
    return _recurs_build_orders(book_a.asset_id, orders_a, book_b.asset_id, orders_b, timestamp)

def _build_order(size, asset_id, price, timestamp):
    return Order(order_type=OrderType.LIMIT_BUY, size=size, asset_id=asset_id, price=price, timestamp=timestamp),

def _recurs_build_orders(a_assetId: str, a_orders: List[SyntheticOrder], b_assetId: str, b_orders: List[SyntheticOrder], timestamp) -> List[Order]:
    orders = []

    if a_orders and b_orders:
        a = a_orders[0]
        b = b_orders[0]

        total = a.price + b.price
        if total < 1:
            if a.size < b.size and a.size >= 1:
                size = a.size
                orders.extend([
                    _build_order(size, a_assetId, a.price, timestamp),
                    _build_order(size, b_assetId, b.price, timestamp)
                ])
                b_orders[0] = SyntheticOrder(side=b.side, price=b.price, size=b_orders[0].size - a.size, timestamp=b.timestamp)
                orders.extend(_recurs_build_orders(a_assetId, a_orders[1:], b_assetId, b_orders, timestamp))

            elif b.size < a.size and b.size >= 1:
                size = b.size
                orders.extend([
                    _build_order(size, a_assetId, a.price, timestamp),
                    _build_order(size, b_assetId, b.price, timestamp)
                ])
                a_orders[0] = SyntheticOrder(side=a.side, price=a.price, size=a_orders[0].size - b.size, timestamp=a.timestamp)
                orders.extend(_recurs_build_orders(a_assetId, a_orders, b_assetId, b_orders[1:], timestamp))

            elif a.size == b.size and a.size >= 1:
                size = a.size
                orders.extend([
                    _build_order(size, a_assetId, a.price, timestamp),
                    _build_order(size, b_assetId, b.price, timestamp)
                ])
                orders.extend(_recurs_build_orders(a_assetId, a_orders[1:], b_assetId, b_orders[1:], timestamp))

    return orders














