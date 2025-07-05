from argparse import ArgumentError
import csv
import os
from typing import List, Dict, Any, Callable
from itertools import groupby
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

class CSVMessageProcessor:
    """
    Processes CSV files containing historical market events and replays them
    to simulate real-time websocket message flow.
    """

    def __init__(self, csv_file_path: str, event_handlers: List[Callable[[List[Dict[str, Any]]], None]]):
        """
        Initialize CSV processor.

        Args:
            csv_file_path: Path to the CSV file containing market events
            event_handlers: List of callback functions to process messages
        """
        self.csv_file_path = csv_file_path
        self.event_handlers = event_handlers
        self.validate_csv_file()

    def run(self):
        try:
            messages = []

            #TODO: Maybe look into an async csv reader so we can process
            # groups as they're being read
            with open(self.csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert string values to appropriate types
                    processed_row = self._process_csv_row(row)
                    messages.append(processed_row)

            grouped_messages = groupby(messages, key=lambda r: (r['timestamp'], r['event_type']))
            for _, v in grouped_messages:

                poly_messages = []
                for _, rows in groupby(v, key=itemgetter('asset_id')):
                    poly_message = self.reconstruct_websocket_message(list(rows))
                    if poly_message:
                        poly_messages.append(poly_message)

                for handler in self.event_handlers:
                    handler(poly_messages)


        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    def validate_csv_file(self) -> None:
        """Validate that CSV file exists and has required columns."""
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

        required_columns = {'timestamp', 'event_type'}

        try:
            with open(self.csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty or has no headers")

                missing_columns = required_columns - set(reader.fieldnames)
                if missing_columns:
                    raise ValueError(f"CSV file missing required columns: {missing_columns}")

        except Exception as e:
            raise ValueError(f"Invalid CSV file format: {e}")

    def _process_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Process a single CSV row and convert types."""
        processed_row = {}

        for key, value in row.items():
            if key == 'timestamp':
                processed_row[key] = int(value) if value else None
            elif key in ['price', 'size']:
                processed_row[key] = float(value) if value else None
            elif key == 'market_id':
                processed_row[key] = value if value else None
            else:
                processed_row[key] = value

        return processed_row


    def reconstruct_websocket_message(self, grouped_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reconstruct websocket messages from CSV rows.

        Args:
            csv_rows: List of CSV rows that represent multiple websocket messages (one per asset_id)

        Returns:
            List of dictionaries in websocket message format (one per asset_id)
        """

        if len(grouped_rows) == 0:
            raise ArgumentError(argument=None, message="No rows to process")

        first_row = grouped_rows[0]
        message = {
            'asset_id': first_row['asset_id'],
            'event_type': first_row['event_type'],
            'hash': first_row['hash'],
            'timestamp': first_row['timestamp']
        }

        if message['event_type'] == 'book':
            message['asks'] = []
            message['bids'] = []
            for row in grouped_rows:
                if row.get('side') == 'SELL':
                    message['asks'].append({
                            'price': str(row.get('price', '')),
                            'size': str(row.get('size', ''))
                        })
                elif row.get('side') == 'BUY':
                    message['bids'].append({
                        'price': str(row.get('price', '')),
                        'size': str(row.get('size', ''))
                    })

        elif message['event_type'] == 'price_change':
            message['changes'] = []
            for row in grouped_rows:
                message['changes'].append({
                    'price': str(row['price']),
                    'size': str(row['size']),
                    'side': row['side']
                })
        else:
            raise RuntimeError(f"event_type not valid: {message['event_type']}")

        return message

