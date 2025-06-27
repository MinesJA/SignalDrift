import csv
import json
import os
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
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
    
    def load_and_group_messages(self) -> List[List[Dict[str, Any]]]:
        """
        Load CSV file and group rows by timestamp and event_type.
        
        Returns:
            List of message groups, where each group is a list of rows with the same timestamp/event_type
        """
        messages = []
        
        try:
            with open(self.csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convert string values to appropriate types
                    processed_row = self._process_csv_row(row)
                    messages.append(processed_row)
                    
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
        
        # Group messages by timestamp and event_type
        grouped_messages = self._group_messages_by_timestamp_and_event_type(messages)
        
        return grouped_messages
    
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
    
    def _group_messages_by_timestamp_and_event_type(self, messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group messages by timestamp and event_type."""
        # Create a dictionary to group messages
        groups = {}
        
        for message in messages:
            timestamp = message.get('timestamp')
            event_type = message.get('event_type')
            
            if timestamp is None or event_type is None:
                logger.warning(f"Skipping message with missing timestamp or event_type: {message}")
                continue
                
            key = (timestamp, event_type)
            if key not in groups:
                groups[key] = []
            groups[key].append(message)
        
        # Sort by timestamp and return as list of groups
        sorted_groups = sorted(groups.items(), key=lambda x: x[0][0])  # Sort by timestamp
        return [group for _, group in sorted_groups]
    
    def reconstruct_websocket_messages(self, csv_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reconstruct websocket messages from CSV rows.
        
        Args:
            csv_rows: List of CSV rows that represent multiple websocket messages (one per asset_id)
            
        Returns:
            List of dictionaries in websocket message format (one per asset_id)
        """
        if not csv_rows:
            return []
            
        # Group rows by asset_id to create one message per asset
        asset_groups = {}
        for row in csv_rows:
            asset_id = row.get('asset_id')
            if asset_id not in asset_groups:
                asset_groups[asset_id] = []
            asset_groups[asset_id].append(row)
        
        # Create one message per asset_id
        messages = []
        for asset_id, asset_rows in asset_groups.items():
            if not asset_rows:
                continue
                
            # Get common fields from first row
            first_row = asset_rows[0]
            message = {
                'asset_id': asset_id,
                'event_type': first_row.get('event_type'),
                'hash': first_row.get('hash'),
                'timestamp': first_row.get('timestamp')
            }
            
            # Reconstruct based on event type
            if message['event_type'] == 'book':
                asks = []
                bids = []
                
                for row in asset_rows:
                    if row.get('side') == 'ask':
                        asks.append({
                            'price': str(row.get('price', '')),
                            'size': str(row.get('size', ''))
                        })
                    elif row.get('side') == 'bid':
                        bids.append({
                            'price': str(row.get('price', '')),
                            'size': str(row.get('size', ''))
                        })
                
                message['asks'] = asks
                message['bids'] = bids
                
            elif message['event_type'] == 'price_change':
                changes = []
                
                for row in asset_rows:
                    side_map = {'bid': 'BUY', 'ask': 'SELL'}
                    changes.append({
                        'price': str(row.get('price', '')),
                        'size': str(row.get('size', '')),
                        'side': side_map.get(row.get('side'), row.get('side', ''))
                    })
                
                message['changes'] = changes
            
            messages.append(message)
        
        return messages
    
    def run(self) -> None:
        """
        Process the CSV file and send messages to event handlers.
        Mimics the behavior of PolymarketMarketEventsService.
        """
        logger.info(f"Starting CSV message processing from {self.csv_file_path}")
        
        try:
            grouped_messages = self.load_and_group_messages()
            logger.info(f"Loaded {len(grouped_messages)} message groups from CSV")
            
            # Process each group sequentially
            for i, message_group in enumerate(grouped_messages):
                try:
                    # Reconstruct websocket messages format (List[Dict])
                    websocket_messages = self.reconstruct_websocket_messages(message_group)
                    
                    # Send to all event handlers (same as websocket service)
                    for handler in self.event_handlers:
                        handler(websocket_messages)
                        
                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1} message groups")
                        
                except Exception as e:
                    logger.error(f"Error processing message group {i}: {e}")
                    # Continue processing other messages
                    continue
                    
        except Exception as e:
            logger.error(f"Error during CSV processing: {e}")
            raise
        
        logger.info("CSV message processing completed")