import csv
import os


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
