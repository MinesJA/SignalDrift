import traceback
from datetime import datetime
from typing import Dict, Any, List
import os
import os.path
import json
import csv
from strategies import build_orders
from services import WebSocketOrderBook, PolymarketService
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, PostOrdersArgs, PartialCreateOrderOptions
from py_clob_client.order_builder.constants import BUY
from config import config


def setup_csvs(slug):
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    trades_file = os.path.join('data', f"polymarket_trades_{slug}.csv")
    price_change_file = os.path.join('data', f"poly_market_price_change_event_{slug}.csv")
    orderbook_file = os.path.join('data', f"order_book_{slug}.csv")

    if not os.path.isfile(trades_file):
        print("Setting up trades csv")
        with open(trades_file, 'w', newline='') as csvfile:
            fieldnames=['asset_id', 'price', 'size', 'side', 'timestamp']
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(fieldnames)

    if not os.path.isfile(price_change_file):
        print("Setting up price change csv")
        with open(price_change_file, 'w', newline='') as csvfile:
            fieldnames=['asset_id', 'event_type', 'hash', 'market', 'price', 'side', 'size', 'timestamp']
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(fieldnames)

    if not os.path.isfile(orderbook_file):
        print("Setting up orderbook csv")
        with open(orderbook_file, 'w', newline='') as csvfile:
            fieldnames=['asset_id', 'price', 'size', 'side', 'timestamp']
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(fieldnames)




#if __name__ == "__main__":
#
#
#    client = connect()
#    ## Create and sign a limit order buying 100 YES tokens for 0.50c each
#    #Refer to the Markets API documentation to locate a tokenID: https://docs.polymarket.com/developers/gamma-markets-api/get-markets
#
#    if client:
#        client.set_api_creds(client.create_or_derive_api_creds())
#
#        slug="mlb-cle-sf-2025-06-17"
#        setup_csvs(slug)
#        market = PolymarketService().get_market_by_slug(slug)
#
#        if market:
#            y = [
#                    {'asset_id': token_id, 'outcome': outcome}
#                    for token_id, outcome in zip(
#                        json.loads(market['clobTokenIds']),
#                        json.loads(market['outcomes'])
#                    )
#                ]
#
#            asset_ids = [i['asset_id'] for i in y]
#            print(asset_ids)
#            #ord = client.create_order(OrderArgs(
#            #    price=args.price,
#            #    size=args.size,
#            #    side=args.side,
#            #    token_id=args.token_id,
#            #    expiration=args.expiration
#            #), PartialCreateOrderOptions(
#            #    neg_risk=args.neg_risk
#            #))
#
#            #resp = client.post_order(ord, order_type)
#
#            resp = client.post_orders([
#                PostOrdersArgs(
#                    # Create and sign a limit order buying 100 YES tokens for 0.50 each
#                    order=client.create_order(
#                        OrderArgs(
#                            price=0.01,
#                            size=5,
#                            side=BUY,
#                            token_id="10703298184509502202740464237528733764769030979577941510093170241051283757018",
#                        ),
#                        PartialCreateOrderOptions(neg_risk=False)
#                    ),
#                    #orderType=OrderType.GTC,
#                ),
#                #PostOrdersArgs(
#                #    # Create and sign a limit order selling 200 NO tokens for 0.25 each
#                #    order=client.create_order(
#                #        OrderArgs(
#                #            price=0.03,
#                #            size=5,
#                #            side=BUY,
#                #            token_id=asset_ids[1],
#                #        ),
#                #        PartialCreateOrderOptions(neg_risk=False)
#                #    ),
#                #   orderType=OrderType.GTC,
#                #)
#            ])
#            print(resp)




if __name__ == "__main__":
    #slug = "mlb-phi-mia-2025-06-17"
    #slug = "mlb-mil-chc-2025-06-17"
    #slug="mlb-cle-sf-2025-06-17"
    slug="mlb-sd-lad-2025-06-17"
    setup_csvs(slug)

    event = PolymarketService().get_market_by_slug(slug)

    if event:
        y = [
                {'asset_id': token_id, 'outcome': outcome}
                for token_id, outcome in
                zip(
                    json.loads(event['clobTokenIds']),
                    json.loads(event['outcomes'])
                )
        ]

        asset_ids = [i['asset_id'] for i in y]

        url = config.POLYMARKET_WEBSOCKET_URL

        def execute_write_market_event(message):
            write_market_event(slug, message):

        order_book = PolymarketOrderBook()

        def update_order_book(message):
            order_book.update(slug, message)

k

        #Complete these by exporting them from your initialized client.
        client = connect()
        if client:
            key = client.derive_api_key()

            auth = {"apiKey": key.api_key, "secret": key.api_secret, "passphrase": key.api_passphrase}

            order_book = OrderBook(slug)

            market_connection = WebSocketOrderBook(
                "market", url, asset_ids, auth, order_book, True
            )


            market_connection = PolymarketOrderBookService.connect("market", asset_ids, callback)
            market_connection.run()
            # user_connection.run()
