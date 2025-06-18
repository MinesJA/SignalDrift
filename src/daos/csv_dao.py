

# TradeWriter
# OrderBookWriter
# OrderBookWriter


# create_trades(trades)
# create_orderbook(trades)


    def csv_trade_writer(self, trades):
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        csv_filename = os.path.join('data', f"polymarket_trades_{self.market_slug}.csv")
        timestamp = round(datetime.now().timestamp() * 1000)

        with open(csv_filename, 'a', newline='') as csvfile:
            fieldnames=['asset_id', 'price', 'size', 'side', 'timestamp']
            writer = csv.DictWriter(csvfile,
                                    delimiter=',',
                                    quotechar='|',
                                    quoting=csv.QUOTE_MINIMAL,
                                    fieldnames=fieldnames
                                )

            for trade in trades:
                x = {**trade, "timestamp": timestamp}
                writer.writerow({key: x.get(key) for key in fieldnames})

    def csv_orderbook_writer(self):
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        csv_filename = os.path.join('data', f"order_book_{self.market_slug}.csv")

        with open(csv_filename, 'a', newline='') as csvfile:
            fieldnames=['asset_id', 'price', 'size', 'side', 'timestamp']
            writer = csv.DictWriter(csvfile,
                                    delimiter=',',
                                    quotechar='|',
                                    quoting=csv.QUOTE_MINIMAL,
                                    fieldnames=fieldnames
                                )

            for asset_id, orders in self.orders.items():
                for _, order in orders.items():

                    x = {**order,
                         "asset_id": asset_id,
                         "side": "ask",
                         "timestamp": round(datetime.now().timestamp() * 1000)}

                    writer.writerow({key: x.get(key) for key in fieldnames})


