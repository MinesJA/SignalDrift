import pytest
import os
import csv
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, call
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daos.market_dao import write_marketEvents, _write_to_csv, _setup_csv, _create_rows, FIELD_NAMES
from models import MarketEvent, EventType


class TestMarketDAO:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        # Save original directory
        original_dir = os.getcwd()
        
        # Create temp directory and change to it
        temp_dir = tempfile.mkdtemp()
        os.chdir(temp_dir)
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        
        yield os.path.join(temp_dir, 'data')
        
        # Restore original directory and cleanup
        os.chdir(original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_market_events(self):
        """Create mock MarketEvent objects."""
        event1 = Mock(spec=MarketEvent)
        event1.asdict_rows.return_value = [
            {
                'market_slug': 'test-market',
                'asset_id': '1',
                'outcome_name': 'Team A',
                'event_type': EventType.PRICE_CHANGE,
                'price': 0.45,
                'side': 'BUY',
                'size': 100,
                'hash': 'hash1',
                'timestamp': 1640995200
            }
        ]
        
        event2 = Mock(spec=MarketEvent)
        event2.asdict_rows.return_value = [
            {
                'market_slug': 'test-market',
                'asset_id': '2',
                'outcome_name': 'Team B',
                'event_type': EventType.BOOK,
                'price': 0.55,
                'side': 'SELL',
                'size': 200,
                'hash': 'hash2',
                'timestamp': 1640995300
            }
        ]
        
        return [event1, event2]
    
    def test_field_names_correct(self):
        """Test that field names match expected specification."""
        expected_fields = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'event_type', 'price', 'side', 'size', 'hash', 'timestamp']
        assert FIELD_NAMES == expected_fields
    
    def test_write_marketEvents_creates_file(self, temp_data_dir, mock_market_events):
        """Test that market events writer creates file correctly."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        csv_filename = f"data/20250701_{market_slug}_polymarket-market-events.csv"
        
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=False)
        
        # Check file was created
        assert os.path.exists(csv_filename)
        
        # Check headers
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            assert reader.fieldnames == FIELD_NAMES
    
    def test_write_marketEvents_test_mode(self, temp_data_dir, mock_market_events):
        """Test that test_mode adds correct suffix to filename."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        csv_filename = f"data/20250701_{market_slug}_polymarket-market-events_test.csv"
        
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=True)
        
        # Check test file was created
        assert os.path.exists(csv_filename)
    
    def test_write_marketEvents_appends_correct_data(self, temp_data_dir, mock_market_events):
        """Test that market events are written with correct data."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        csv_filename = f"data/20250701_{market_slug}_polymarket-market-events.csv"
        
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=False)
        
        # Read and verify data
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 2  # One row per event
            
            # Check first row
            assert rows[0]['market_slug'] == 'test-market'
            assert rows[0]['market_id'] == '12345'
            assert rows[0]['asset_id'] == '1'
            assert rows[0]['outcome_name'] == 'Team A'
            assert rows[0]['price'] == '0.45'
            assert rows[0]['side'] == 'BUY'
            assert rows[0]['size'] == '100'
            
            # Check second row
            assert rows[1]['asset_id'] == '2'
            assert rows[1]['outcome_name'] == 'Team B'
            assert rows[1]['price'] == '0.55'
            assert rows[1]['side'] == 'SELL'
            assert rows[1]['size'] == '200'
    
    def test_write_marketEvents_empty_list(self, temp_data_dir):
        """Test that empty event list doesn't create file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        csv_filename = f"data/20250701_{market_slug}_polymarket-market-events.csv"
        
        write_marketEvents(market_slug, market_id, [], test_datetime, test_mode=False)
        
        # Check file was not created
        assert not os.path.exists(csv_filename)
    
    def test_write_marketEvents_multiple_runs_appends(self, temp_data_dir, mock_market_events):
        """Test that multiple runs append to existing file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        csv_filename = f"data/20250701_{market_slug}_polymarket-market-events.csv"
        
        # First run
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=False)
        
        # Second run
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=False)
        
        # Check that data was appended
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 4  # 2 events * 2 runs
    
    def test_create_rows_adds_market_id(self):
        """Test that _create_rows adds market_id to event rows."""
        event = Mock(spec=MarketEvent)
        event.asdict_rows.return_value = [
            {'asset_id': '1', 'price': 0.45},
            {'asset_id': '2', 'price': 0.55}
        ]
        
        market_id = 12345
        rows = _create_rows(event, market_id)
        
        assert len(rows) == 2
        assert all(row['market_id'] == 12345 for row in rows)
    
    def test_create_rows_filters_fields(self):
        """Test that _create_rows only includes fields in FIELD_NAMES."""
        event = Mock(spec=MarketEvent)
        event.asdict_rows.return_value = [
            {
                'market_slug': 'test',
                'market_id': 999,  # This will be overridden
                'asset_id': '1',
                'outcome_name': 'Team A',
                'event_type': 'PRICE_CHANGE',
                'price': 0.45,
                'side': 'BUY',
                'size': 100,
                'hash': 'hash1',
                'timestamp': 1640995200,
                'extra_field': 'should_be_removed'  # This should be filtered out
            }
        ]
        
        market_id = 12345
        rows = _create_rows(event, market_id)
        
        assert len(rows) == 1
        assert 'extra_field' not in rows[0]
        assert rows[0]['market_id'] == 12345
        assert set(rows[0].keys()) == set(FIELD_NAMES)
    
    def test_setup_csv_creates_directory(self):
        """Test that _setup_csv creates data directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_dir = os.getcwd()
            os.chdir(temp_dir)
            
            csv_filename = "data/test.csv"
            
            # Data directory should not exist yet
            assert not os.path.exists("data")
            
            _setup_csv(csv_filename)
            
            # Data directory should now exist
            assert os.path.exists("data")
            assert os.path.exists(csv_filename)
            
            # Restore original directory
            os.chdir(original_dir)
    
    @patch('daos.market_dao.logger')
    def test_write_marketEvents_logs_info(self, mock_logger, temp_data_dir, mock_market_events):
        """Test that appropriate logging occurs."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        market_id = 12345
        
        write_marketEvents(market_slug, market_id, mock_market_events, test_datetime, test_mode=False)
        
        # Check that info was logged (can be called multiple times)
        mock_logger.info.assert_any_call(f"Writing 2 market events for market -- {market_slug}")
    
    @patch('daos.market_dao.logger')
    def test_write_to_csv_exception_handling(self, mock_logger):
        """Test that exceptions in _write_to_csv are caught and logged."""
        with patch('daos.market_dao._write_to_csv', side_effect=Exception("Test error")):
            test_datetime = datetime(2025, 7, 1, 12, 0, 0)
            market_slug = "test-market"
            market_id = 12345
            
            event = Mock(spec=MarketEvent)
            event.asdict_rows.return_value = [{'test': 'data'}]
            
            # Should not raise exception
            write_marketEvents(market_slug, market_id, [event], test_datetime, test_mode=False)
            
            # Check that error was logged
            mock_logger.error.assert_called_with("Failed to write rows in market_writer")