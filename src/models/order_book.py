import traceback
from datetime import datetime
from typing import Dict, Any, List
import os
import os.path
import csv
from strategies import build_orders

class SyntheticOrderBook:
    """
    Represents an odds event from various betting sources.

    Attributes:
        request_id: ID used to connect different fetched results
        timestamp: DateTime UTC when we fetched the market price
        impl_prob: Implied probability (vig removed if applicable)
        fair_odds: Fair odds value
        source: Name of source (polymarket, betfair, etc.)
        odds_type: Type of odds (decimal, american, fractional, exchange)
        question: The betting question/event
        updated_at: DateTime UTC that the endpoint provides (if available)
        meta: Additional metadata specific to source data
    """
    def __init__(self, slug):
        self.market = market
        self.book_a
        self.orders = {}
        self.market_slug = slug



    def handle_order_message(self, order_message: List[Dict[str, Any]]):
        try:
            self.csv_writer(order_message)

            for order in order_message:
                asset_id = order["asset_id"]

                if asset_id not in self.orders:
                    self.orders[asset_id] = {}

                if order["event_type"] == "price_change":
                    for change in order["changes"]:
                        if change["side"] == "SELL":
                            self.orders[asset_id][change["price"]] = {
                                "price": float(change["price"]),
                                "size": float(change["size"])
                            }

                    print(f"\n PRICE_CHANGE -- curr order number [asset_id-{asset_id[-5:]}]: {len(self.orders[asset_id])}")

                if order["event_type"] == "book":
                    for ask in order["asks"]:
                        self.orders[asset_id][ask["price"]] = {
                            "price": float(ask["price"]),
                            "size": float(ask["size"])
                        }

                    print(f"\n BOOK -- curr order number [asset_id-{asset_id[-5:]}]:  {len(self.orders[asset_id])}")



            self.csv_orderbook_writer()

            (assetId_a, orders_a), (assetId_b, orders_b) = self.orders.items()
            orders_a = list(orders_a.values())
            orders_b = list(orders_b.values())

            print("\n ===== \n")
            print(orders_a)
            print(orders_b)


            print("\n ===== \n")
            trades = build_orders({"asset_id": assetId_a, "orders": orders_a}, {"asset_id": assetId_b, "orders": orders_b})

            print(trades)

            self.csv_trade_writer(trades)


        except Exception:
            print("ERROR \n")
            print(traceback.format_exc())
