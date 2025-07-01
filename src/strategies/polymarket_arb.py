from typing import Dict, Any, List
from models import SyntheticOrderBook, Order, OrderType, SyntheticOrder, Side
from datetime import datetime

def calculate_orders(a_book: SyntheticOrderBook, b_book: SyntheticOrderBook) -> List[Order]:
    a_orders = sorted(a_book.orders, key=lambda order: order.price)
    b_orders = sorted(b_book.orders, key=lambda order: order.price)

    timestamp = round(datetime.now().timestamp() * 1000)
    market_slug = a_book.market_slug  # Both books should have the same market_slug
    return _recurs_build_orders(market_slug, a_book.asset_id, a_orders, b_book.asset_id, b_orders, timestamp)

def _recurs_build_orders(a_orders: List[SyntheticOrder], b_orders: List[SyntheticOrder], timestamp) -> List[Order]:
    orders = []

    if a_orders and b_orders:
        a = a_orders[0]
        b = b_orders[0]

        total = a.price + b.price
        if total < 1:
            if a.size < b.size and rount(a.size/2) >= 1:
                size = round(a.size/2)
                # TODO: Figure out how to remove all the duplicate extend _build_order calls for each conditional
                orders.extend([
                    _build_order(a, size, a.price, timestamp),
                    _build_order(b, size, b.price, timestamp)
                ])
                a_orders = a_orders[1:]
                b_orders[0] = SyntheticOrder(side=b.side, price=b.price, size=b.size - a.size, timestamp=b.timestamp)

            elif a.size > b.size and round(b.size/2) >= 1:
                size = round(b.size/2)
                orders.extend([
                    _build_order(market_slug, size, a_assetId, a.price, timestamp),
                    _build_order(market_slug, size, b_assetId, b.price, timestamp)
                ])
                a_orders[0] = SyntheticOrder(side=a.side, price=a.price, size=a.size - b.size, timestamp=a.timestamp)
                b_orders = b_orders[1:]

            elif a.size == b.size and round(a.size/2) >= 1:
                size = round(a.size/2)
                orders.extend([
                    _build_order(a, size, a_assetId, a.price, timestamp),
                    _build_order(b, size, b_assetId, b.price, timestamp)
                ])
                a_orders = a_orders[1:]
                b_orders = b_orders[1:]

            orders.extend(_recurs_build_orders(market_slug, a_assetId, a_orders, b_assetId, b_orders, timestamp))

    return orders

def _build_order(synth_order: SyntheticOrder, size: float, price: float, timestamp: int)
    return Order(
        market_slug=synth_order.market_slug,
        market_id=synth_order.market_id,
        asset_id=synth_order.asset_id,
        outcome_name=synth_order.outcome_name,
        order_type=OrderType.FOK,
        side=Side.BUY,
        price=price,
        size=size,
        timestamp=timestamp
    )

#def _build_order(market_slug, size, asset_id, price, timestamp)
#    return Order(
#        market_slug=synth_order.market_slug,
#        market_id=synth_order.market_id,
#        asset_id=asset_id,
#        outcome_name=outcome_name,
#        order_type=OrderType.FOK,
#        side=Side.BUY,
#        price=price,
#        size=size,
#        timestamp=timestamp
#    )












