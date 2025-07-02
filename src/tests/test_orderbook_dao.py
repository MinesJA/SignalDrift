import pytest
import os
import csv
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daos.orderbook_dao import write_orderBookStore, _write_to_csv, _setup_csv, FIELD_NAMES
from models import OrderBookStore, SyntheticOrderBook


class TestOrderBookDAO:
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
    def mock_orderbook_store(self):
        """Create mock OrderBookStore with SyntheticOrderBook objects."""
        book1 = Mock(spec=SyntheticOrderBook)
        book1.asdict_rows.return_value = [
            {
                'market_slug': 'test-market',
                'market_id': 12345,
                'asset_id': '1',
                'outcome_name': 'Team A',
                'price': 0.45,
                'size': 100,
                'side': 'BUY',
                'timestamp': 1640995200
            },
            {
                'market_slug': 'test-market',
                'market_id': 12345,
                'asset_id': '1',
                'outcome_name': 'Team A',
                'price': 0.44,
                'size': 150,
                'side': 'BUY',
                'timestamp': 1640995200
            }
        ]
        
        book2 = Mock(spec=SyntheticOrderBook)
        book2.asdict_rows.return_value = [
            {
                'market_slug': 'test-market',
                'market_id': 12345,
                'asset_id': '2',
                'outcome_name': 'Team B',
                'price': 0.55,
                'size': 200,
                'side': 'SELL',
                'timestamp': 1640995300
            }
        ]
        
        store = Mock(spec=OrderBookStore)
        store.books = [book1, book2]
        
        return store
    
    def test_field_names_correct(self):
        """Test that field names match expected specification."""
        expected_fields = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'price', 'size', 'side', 'timestamp']
        assert FIELD_NAMES == expected_fields
    
    def test_write_orderBookStore_creates_file(self, temp_data_dir, mock_orderbook_store):
        """Test that orderbook store writer creates file correctly."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=False)
        
        # Check file was created
        assert os.path.exists(csv_filename)
        
        # Check headers
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            assert reader.fieldnames == FIELD_NAMES
    
    def test_write_orderBookStore_test_mode(self, temp_data_dir, mock_orderbook_store):
        """Test that test_mode adds correct suffix to filename."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book_test.csv"
        
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=True)
        
        # Check test file was created
        assert os.path.exists(csv_filename)
    
    def test_write_orderBookStore_appends_correct_data(self, temp_data_dir, mock_orderbook_store):
        """Test that orderbook data is written correctly."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=False)
        
        # Read and verify data
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 3  # Total rows from both books
            
            # Check first row (from book1)
            assert rows[0]['market_slug'] == 'test-market'
            assert rows[0]['market_id'] == '12345'
            assert rows[0]['asset_id'] == '1'
            assert rows[0]['outcome_name'] == 'Team A'
            assert rows[0]['price'] == '0.45'
            assert rows[0]['size'] == '100'
            assert rows[0]['side'] == 'BUY'
            assert rows[0]['timestamp'] == '1640995200'
            
            # Check second row (from book1)
            assert rows[1]['price'] == '0.44'
            assert rows[1]['size'] == '150'
            
            # Check third row (from book2)
            assert rows[2]['asset_id'] == '2'
            assert rows[2]['outcome_name'] == 'Team B'
            assert rows[2]['price'] == '0.55'
            assert rows[2]['size'] == '200'
            assert rows[2]['side'] == 'SELL'
    
    def test_write_orderBookStore_empty_books(self, temp_data_dir):
        """Test that empty books list doesn't create file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        # Create store with empty books
        store = Mock(spec=OrderBookStore)
        store.books = []
        
        write_orderBookStore(market_slug, store, test_datetime, test_mode=False)
        
        # Check file was not created
        assert not os.path.exists(csv_filename)
    
    def test_write_orderBookStore_empty_rows(self, temp_data_dir):
        """Test that books with no rows don't create file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        # Create store with books that return empty rows
        book = Mock(spec=SyntheticOrderBook)
        book.asdict_rows.return_value = []
        
        store = Mock(spec=OrderBookStore)
        store.books = [book]
        
        write_orderBookStore(market_slug, store, test_datetime, test_mode=False)
        
        # Check file was not created
        assert not os.path.exists(csv_filename)
    
    def test_write_orderBookStore_multiple_runs_appends(self, temp_data_dir, mock_orderbook_store):
        """Test that multiple runs append to existing file."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        # First run
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=False)
        
        # Second run
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=False)
        
        # Check that data was appended
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 6  # 3 rows * 2 runs
    
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
    
    @patch('daos.orderbook_dao.logger')
    def test_write_orderBookStore_logs_info(self, mock_logger, temp_data_dir, mock_orderbook_store):
        """Test that appropriate logging occurs."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        write_orderBookStore(market_slug, mock_orderbook_store, test_datetime, test_mode=False)
        
        # Check that info was logged
        mock_logger.info.assert_any_call(f"Writing 3 synthetic orders for market -- {market_slug}")
    
    def test_write_to_csv_preserves_order_of_fields(self, temp_data_dir):
        """Test that CSV writer preserves the order of fields as defined in FIELD_NAMES."""
        csv_filename = os.path.join(temp_data_dir, "test.csv")
        
        # Setup CSV
        _setup_csv(csv_filename)
        
        # Write a row with fields in different order
        row = {
            'timestamp': 1640995200,
            'side': 'BUY',
            'size': 100,
            'price': 0.45,
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
    
    def test_multiple_books_combined(self, temp_data_dir):
        """Test that rows from multiple books are combined correctly."""
        test_datetime = datetime(2025, 7, 1, 12, 0, 0)
        market_slug = "test-market"
        
        # Create books with different data
        book1 = Mock(spec=SyntheticOrderBook)
        book1.asdict_rows.return_value = [
            {'market_slug': 'test', 'market_id': 1, 'asset_id': '1', 'outcome_name': 'A', 
             'price': 0.1, 'size': 10, 'side': 'BUY', 'timestamp': 100}
        ]
        
        book2 = Mock(spec=SyntheticOrderBook)
        book2.asdict_rows.return_value = [
            {'market_slug': 'test', 'market_id': 1, 'asset_id': '2', 'outcome_name': 'B', 
             'price': 0.2, 'size': 20, 'side': 'SELL', 'timestamp': 200}
        ]
        
        book3 = Mock(spec=SyntheticOrderBook)
        book3.asdict_rows.return_value = [
            {'market_slug': 'test', 'market_id': 1, 'asset_id': '3', 'outcome_name': 'C', 
             'price': 0.3, 'size': 30, 'side': 'BUY', 'timestamp': 300}
        ]
        
        store = Mock(spec=OrderBookStore)
        store.books = [book1, book2, book3]
        
        csv_filename = f"data/20250701_{market_slug}_synthetic-order-book.csv"
        
        write_orderBookStore(market_slug, store, test_datetime, test_mode=False)
        
        # Verify all books' data was written
        with open(csv_filename, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]['asset_id'] == '1'
            assert rows[1]['asset_id'] == '2'
            assert rows[2]['asset_id'] == '3'