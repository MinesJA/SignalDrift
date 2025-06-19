
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
