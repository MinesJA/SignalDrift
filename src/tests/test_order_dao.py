import pytest
import os
import csv
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daos.order_dao import write_orders, _write_to_csv, _setup_csv, FIELD_NAMES
from models import Order, OrderType, OrderSide


class TestOrderDAO:
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
    def mock_orders(self):
        """Create mock Order objects."""
        order1 = Mock(spec=Order)
        order1.asdict.return_value = {
            'market_slug': 'test-market',
            'market_id': 12345,
            'asset_id': '1',
            'outcome_name': 'Team A',
            'side': OrderSide.BUY,
            'order_type': OrderType.GTC,
            'price': 0.45,
            'size': 100,
            'timestamp': 1640995200
        }
        
        order2 = Mock(spec=Order)
        order2.asdict.return_value = {
            'market_slug': 'test-market',
            'market_id': 12345,
            'asset_id': '2',
            'outcome_name': 'Team B',
            'side': OrderSide.SELL,
            'order_type': OrderType.GTC,
            'price': 0.55,
            'size': 200,
            'timestamp': 1640995300
        }
        
        return [order1, order2]
    
    def test_field_names_correct(self):
        """Test that field names match expected specification."""
        expected_fields = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'side', 'order_type', 'price', 'size', 'timestamp']
        assert FIELD_NAMES == expected_fields
    
    def test_write_orders_creates_file(self, temp_data_dir, mock_orders):
        """Test that orders writer creates file correctly."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_orders.csv"
        
        write_orders(market_slug, mock_orders, test_datetime, test_mode=False)
        
        # Check file was created
        assert os.path.exists(csv_filename)
        
        # Check headers
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            assert reader.fieldnames == FIELD_NAMES
    
    def test_write_orders_test_mode(self, temp_data_dir, mock_orders):
        """Test that test_mode adds correct suffix to filename."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_orders_test.csv"
        
        write_orders(market_slug, mock_orders, test_datetime, test_mode=True)
        
        # Check test file was created
        assert os.path.exists(csv_filename)
    
    def test_write_orders_appends_correct_data(self, temp_data_dir, mock_orders):
        """Test that orders are written with correct data."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_orders.csv"
        
        write_orders(market_slug, mock_orders, test_datetime, test_mode=False)
        
        # Read and verify data
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 2  # One row per order
            
            # Check first row
            assert rows[0]['market_slug'] == 'test-market'
            assert rows[0]['market_id'] == '12345'
            assert rows[0]['asset_id'] == '1'
            assert rows[0]['outcome_name'] == 'Team A'
            assert rows[0]['side'] == str(OrderSide.BUY)
            assert rows[0]['order_type'] == str(OrderType.GTC)
            assert rows[0]['price'] == '0.45'
            assert rows[0]['size'] == '100'
            assert rows[0]['timestamp'] == '1640995200'
            
            # Check second row
            assert rows[1]['asset_id'] == '2'
            assert rows[1]['outcome_name'] == 'Team B'
            assert rows[1]['side'] == str(OrderSide.SELL)
            assert rows[1]['price'] == '0.55'
            assert rows[1]['size'] == '200'
            assert rows[1]['timestamp'] == '1640995300'
    
    def test_write_orders_empty_list(self, temp_data_dir):
        """Test that empty order list doesn't create file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_orders.csv"
        
        write_orders(market_slug, [], test_datetime, test_mode=False)
        
        # Check file was not created
        assert not os.path.exists(csv_filename)
    
    def test_write_orders_multiple_runs_appends(self, temp_data_dir, mock_orders):
        """Test that multiple runs append to existing file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_orders.csv"
        
        # First run
        write_orders(market_slug, mock_orders, test_datetime, test_mode=False)
        
        # Second run
        write_orders(market_slug, mock_orders, test_datetime, test_mode=False)
        
        # Check that data was appended
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 4  # 2 orders * 2 runs
    
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
    
    def test_setup_csv_writes_headers(self):
        """Test that _setup_csv writes correct headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)
            csv_filename = os.path.join(temp_dir, "data", "test.csv")
            
            _setup_csv(csv_filename)
            
            with open(csv_filename, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                assert headers == FIELD_NAMES
    
    @patch('daos.order_dao.logger')
    def test_write_orders_logs_info(self, mock_logger, temp_data_dir, mock_orders):
        """Test that appropriate logging occurs."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        write_orders(market_slug, mock_orders, test_datetime, test_mode=False)
        
        # Check that info was logged (can be called multiple times)
        mock_logger.info.assert_any_call(f"Writing 2 orders for market -- {market_slug}")
    
    def test_write_to_csv_preserves_order_of_fields(self, temp_data_dir):
        """Test that CSV writer preserves the order of fields as defined in FIELD_NAMES."""
        csv_filename = os.path.join(temp_data_dir, "test.csv")
        
        # Setup CSV
        _setup_csv(csv_filename)
        
        # Write a row with fields in different order
        row = {
            'timestamp': 1640995200,
            'size': 100,
            'price': 0.45,
            'order_type': 'GTC',
            'side': 'BUY',
            'outcome_name': 'Team A',
            'asset_id': '1',
            'market_id': 12345,
            'market_slug': 'test-market'
        }
        
        _write_to_csv(csv_filename, [row])
        
        # Read and verify field order
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            read_row = next(reader)
            
            # Convert keys to list to check order
            field_order = list(read_row.keys())
            assert field_order == FIELD_NAMES
    
    def test_write_to_csv_quoting(self, temp_data_dir):
        """Test that CSV writer handles special characters correctly."""
        csv_filename = os.path.join(temp_data_dir, "test.csv")
        
        # Setup CSV
        _setup_csv(csv_filename)
        
        # Write a row with special characters
        row = {
            'market_slug': 'test|market',  # Contains quote char
            'market_id': 12345,
            'asset_id': '1',
            'outcome_name': 'Team, A',  # Contains comma
            'side': 'BUY',
            'order_type': 'GTC',
            'price': 0.45,
            'size': 100,
            'timestamp': 1640995200
        }
        
        _write_to_csv(csv_filename, [row])
        
        # Read and verify data
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            read_row = next(reader)
            
            assert read_row['market_slug'] == 'test|market'
            assert read_row['outcome_name'] == 'Team, A'