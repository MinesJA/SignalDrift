import pytest
import os
import tempfile
import csv
from unittest.mock import Mock, patch
from src.utils.csv_message_processor import CSVMessageProcessor


class TestCSVMessageProcessor:
    """Test suite for CSVMessageProcessor class."""

    def create_test_csv(self, rows):
        """Helper method to create a temporary CSV file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        try:
            if rows:
                writer = csv.DictWriter(temp_file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            temp_file.flush()
            return temp_file.name
        finally:
            temp_file.close()

    def test_validate_csv_file_not_found(self):
        """Test validation fails when CSV file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            CSVMessageProcessor("/nonexistent/file.csv", [])

    def test_validate_csv_file_missing_columns(self):
        """Test validation fails when required columns are missing."""
        rows = [{'price': '0.5', 'size': '100'}]  # Missing timestamp and event_type
        csv_file = self.create_test_csv(rows)
        
        try:
            with pytest.raises(ValueError, match="missing required columns"):
                CSVMessageProcessor(csv_file, [])
        finally:
            os.unlink(csv_file)

    def test_validate_csv_file_empty(self):
        """Test validation fails when CSV file is empty."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()
        
        try:
            with pytest.raises(ValueError, match="empty or has no headers"):
                CSVMessageProcessor(temp_file.name, [])
        finally:
            os.unlink(temp_file.name)

    def test_validate_csv_file_valid(self):
        """Test validation passes with valid CSV file."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'book', 'price': '0.5', 'size': '100', 'side': 'ask'}
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            # Should not raise exception
            processor = CSVMessageProcessor(csv_file, [])
            assert processor.csv_file_path == csv_file
        finally:
            os.unlink(csv_file)

    def test_process_csv_row_type_conversion(self):
        """Test CSV row processing converts types correctly."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'book', 'price': '0.5', 'size': '100.5', 'side': 'ask'}
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            processor = CSVMessageProcessor(csv_file, [])
            row = {'timestamp': '1750803262050', 'price': '0.5', 'size': '100.5', 'event_type': 'book'}
            processed = processor._process_csv_row(row)
            
            assert processed['timestamp'] == 1750803262050
            assert processed['price'] == 0.5
            assert processed['size'] == 100.5
            assert processed['event_type'] == 'book'
        finally:
            os.unlink(csv_file)

    def test_group_messages_by_timestamp_and_event_type(self):
        """Test message grouping by timestamp and event_type."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'book', 'price': '0.5', 'size': '100', 'side': 'ask'}
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            processor = CSVMessageProcessor(csv_file, [])
            messages = [
                {'timestamp': 1750803262050, 'event_type': 'book', 'price': 0.5, 'side': 'ask'},
                {'timestamp': 1750803262050, 'event_type': 'book', 'price': 0.4, 'side': 'bid'},
                {'timestamp': 1750803262060, 'event_type': 'price_change', 'price': 0.6, 'side': 'ask'},
            ]
            
            grouped = processor._group_messages_by_timestamp_and_event_type(messages)
            
            assert len(grouped) == 2
            # First group: timestamp 1750803262050, event_type 'book'
            assert len(grouped[0]) == 2
            assert all(msg['timestamp'] == 1750803262050 and msg['event_type'] == 'book' for msg in grouped[0])
            # Second group: timestamp 1750803262060, event_type 'price_change'
            assert len(grouped[1]) == 1
            assert grouped[1][0]['timestamp'] == 1750803262060
            assert grouped[1][0]['event_type'] == 'price_change'
        finally:
            os.unlink(csv_file)

    def test_reconstruct_websocket_message_book_event(self):
        """Test reconstructing websocket message for book event."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'book', 'price': '0.5', 'size': '100', 'side': 'ask'}
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            processor = CSVMessageProcessor(csv_file, [])
            csv_rows = [
                {'asset_id': '123', 'event_type': 'book', 'hash': 'abc', 'timestamp': 1750803262050, 'price': 0.5, 'size': 100, 'side': 'ask'},
                {'asset_id': '123', 'event_type': 'book', 'hash': 'abc', 'timestamp': 1750803262050, 'price': 0.4, 'size': 200, 'side': 'bid'},
            ]
            
            messages = processor.reconstruct_websocket_messages(csv_rows)
            assert len(messages) == 1  # Should be one message per asset_id
            message = messages[0]
            
            assert message['asset_id'] == '123'
            assert message['event_type'] == 'book'
            assert message['hash'] == 'abc'
            assert message['timestamp'] == 1750803262050
            assert len(message['asks']) == 1
            assert len(message['bids']) == 1
            assert message['asks'][0] == {'price': '0.5', 'size': '100'}
            assert message['bids'][0] == {'price': '0.4', 'size': '200'}
        finally:
            os.unlink(csv_file)

    def test_reconstruct_websocket_message_price_change_event(self):
        """Test reconstructing websocket message for price_change event."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'price_change', 'price': '0.5', 'size': '100', 'side': 'ask'}
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            processor = CSVMessageProcessor(csv_file, [])
            csv_rows = [
                {'asset_id': '123', 'event_type': 'price_change', 'hash': 'abc', 'timestamp': 1750803262050, 'price': 0.5, 'size': 100, 'side': 'ask'},
                {'asset_id': '123', 'event_type': 'price_change', 'hash': 'abc', 'timestamp': 1750803262050, 'price': 0.4, 'size': 200, 'side': 'bid'},
            ]
            
            messages = processor.reconstruct_websocket_messages(csv_rows)
            assert len(messages) == 1  # Should be one message per asset_id
            message = messages[0]
            
            assert message['asset_id'] == '123'
            assert message['event_type'] == 'price_change'
            assert message['hash'] == 'abc'
            assert message['timestamp'] == 1750803262050
            assert len(message['changes']) == 2
            assert message['changes'][0] == {'price': '0.5', 'size': '100', 'side': 'SELL'}
            assert message['changes'][1] == {'price': '0.4', 'size': '200', 'side': 'BUY'}
        finally:
            os.unlink(csv_file)

    def test_run_processes_messages(self):
        """Test that run method processes messages and calls handlers."""
        rows = [
            {'timestamp': '1750803262050', 'event_type': 'book', 'asset_id': '123', 'hash': 'abc', 'price': '0.5', 'size': '100', 'side': 'ask'},
            {'timestamp': '1750803262050', 'event_type': 'book', 'asset_id': '123', 'hash': 'abc', 'price': '0.4', 'size': '200', 'side': 'bid'},
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            mock_handler = Mock()
            processor = CSVMessageProcessor(csv_file, [mock_handler])
            
            processor.run()
            
            # Should have called handler once (both rows are grouped together)
            assert mock_handler.call_count == 1
            
            # Check the message structure passed to handler (now a List[Dict])
            called_messages = mock_handler.call_args[0][0]
            assert isinstance(called_messages, list)
            assert len(called_messages) == 1  # Should have one message per asset_id
            called_message = called_messages[0]
            assert called_message['event_type'] == 'book'
            assert called_message['asset_id'] == '123'
            assert len(called_message['asks']) == 1
            assert len(called_message['bids']) == 1
        finally:
            os.unlink(csv_file)

    def test_run_handles_malformed_data(self):
        """Test that run method handles malformed CSV data gracefully."""
        rows = [
            {'timestamp': '', 'event_type': 'book', 'price': '0.5', 'size': '100', 'side': 'ask'},  # Empty timestamp
            {'timestamp': '1750803262050', 'event_type': 'book', 'price': '0.4', 'size': '200', 'side': 'bid'},  # Valid row
        ]
        csv_file = self.create_test_csv(rows)
        
        try:
            mock_handler = Mock()
            processor = CSVMessageProcessor(csv_file, [mock_handler])
            
            # Should not raise exception, but should skip malformed row
            processor.run()
            
            # Should only process the valid row
            assert mock_handler.call_count == 1
        finally:
            os.unlink(csv_file)