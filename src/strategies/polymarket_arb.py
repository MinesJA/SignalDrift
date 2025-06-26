from typing import Dict, Any, List
from models import SyntheticOrderBook, Order, OrderType, SyntheticOrder
from datetime import datetime

def calculate_orders(a_book: SyntheticOrderBook, b_book: SyntheticOrderBook) -> List[Order]:
    a_orders = sorted(a_book.orders, key=lambda order: order.price)
    b_orders = sorted(b_book.orders, key=lambda order: order.price)

    timestamp = round(datetime.now().timestamp() * 1000)
    market_slug = a_book.market_slug  # Both books should have the same market_slug
    return _recurs_build_orders(market_slug, a_book.asset_id, a_orders, b_book.asset_id, b_orders, timestamp)

def _recurs_build_orders(market_slug: str, a_assetId: str, a_orders: List[SyntheticOrder], b_assetId: str, b_orders: List[SyntheticOrder], timestamp) -> List[Order]:
    orders = []

    if a_orders and b_orders:
        a = a_orders[0]
        b = b_orders[0]

        total = a.price + b.price
        if total < 1:
            if a.size < b.size and a.size >= 1:
                size = a.size
                # TODO: Figure out how to remove all the duplicate extend _build_order calls for each conditional
                orders.extend([
                    _build_order(market_slug, size, a_assetId, a.price, timestamp),
                    _build_order(market_slug, size, b_assetId, b.price, timestamp)
                ])
                a_orders = a_orders[1:]
                b_orders[0] = SyntheticOrder(side=b.side, price=b.price, size=b.size - a.size, timestamp=b.timestamp)

            elif a.size > b.size and b.size >= 1:
                size = b.size
                orders.extend([
                    _build_order(market_slug, size, a_assetId, a.price, timestamp),
                    _build_order(market_slug, size, b_assetId, b.price, timestamp)
                ])
                a_orders[0] = SyntheticOrder(side=a.side, price=a.price, size=a.size - b.size, timestamp=a.timestamp)
                b_orders = b_orders[1:]

            elif a.size == b.size and a.size >= 1:
                size = a.size
                orders.extend([
                    _build_order(market_slug, size, a_assetId, a.price, timestamp),
                    _build_order(market_slug, size, b_assetId, b.price, timestamp)
                ])
                a_orders = a_orders[1:]
                b_orders = b_orders[1:]

            orders.extend(_recurs_build_orders(market_slug, a_assetId, a_orders, b_assetId, b_orders, timestamp))

    return orders

def _build_order(market_slug, size, asset_id, price, timestamp):
    return Order(market_slug=market_slug, order_type=OrderType.LIMIT_BUY, size=size, asset_id=asset_id, price=price, timestamp=timestamp)











