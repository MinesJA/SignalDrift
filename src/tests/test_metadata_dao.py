import pytest
import os
import csv
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from daos.metadata_dao import write_metadata, _get_file_path, FIELD_NAMES


class TestMetadataDAO:
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_books(self):
        """Create mock SyntheticOrderBook objects."""
        book1 = Mock()
        book1.asset_id = "1"
        book1.outcome_name = "Team A"
        
        book2 = Mock()
        book2.asset_id = "2"
        book2.outcome_name = "Team B"
        
        return [book1, book2]
    
    @pytest.fixture
    def market_metadata(self):
        """Create sample market metadata."""
        return {
            'id': 12345,
            'slug': 'mlb-test-match',
            'startDate': '2025-06-27T19:00:00Z',
            'outcomes': '["Team A", "Team B"]',
            'clobTokenIds': '["1", "2"]'
        }
    
    def test_get_file_path(self):
        """Test file path generation with new naming convention."""
        executed_at = datetime(2025, 6, 27, 12, 0, 0)
        market_slug = "mlb-test-match"
        
        file_path = _get_file_path(market_slug, executed_at)
        expected_path = "data/20250627_mlb-test-match_market-metadata.csv"
        
        assert file_path == expected_path
    
    def test_write_metadata_creates_file(self, mock_books, market_metadata):
        """Test that metadata writer creates file with correct headers."""
        executed_at = datetime(2025, 6, 27, 12, 0, 0)
        unique_slug = f"mlb-test-create-file-{executed_at.timestamp()}"
        
        # Clean up any existing test file
        file_path = f"data/20250627_{unique_slug}_market-metadata.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        write_metadata(
            market_slug=unique_slug,
            market_id=12345,
            books=mock_books,
            executed_at=executed_at,
            market_metadata=market_metadata
        )
        
        # Check file was created
        assert os.path.exists(file_path)
        
        # Check headers
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            assert reader.fieldnames == FIELD_NAMES
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def test_write_metadata_appends_rows(self, mock_books, market_metadata):
        """Test that metadata writer appends correct data."""
        executed_at = datetime(2025, 6, 27, 12, 0, 0)
        unique_slug = f"mlb-test-append-rows-{executed_at.timestamp()}"
        
        # Clean up any existing test file
        file_path = f"data/20250627_{unique_slug}_market-metadata.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        write_metadata(
            market_slug=unique_slug,
            market_id=12345,
            books=mock_books,
            executed_at=executed_at,
            market_metadata=market_metadata
        )
        
        # Read and verify data
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            assert len(rows) == 2  # One row per book/outcome
            
            # Check first row
            assert rows[0]['market_slug'] == unique_slug
            assert rows[0]['market_id'] == '12345'
            assert rows[0]['asset_id'] == '1'
            assert rows[0]['outcome_name'] == 'Team A'
            assert rows[0]['executed_at'] == str(int(executed_at.timestamp()))
            # Check that date was parsed (should be epoch timestamp)
            assert rows[0]['game_start_timestamp'].isdigit()
            
            # Check second row
            assert rows[1]['asset_id'] == '2'
            assert rows[1]['outcome_name'] == 'Team B'
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def test_write_metadata_handles_missing_dates(self, mock_books):
        """Test handling of missing start dates."""
        executed_at = datetime(2025, 6, 27, 12, 0, 0)
        unique_slug = f"mlb-test-missing-dates-{executed_at.timestamp()}"
        
        # Market metadata without dates
        metadata = {
            'id': 12345,
            'slug': unique_slug
        }
        
        # Clean up any existing test file
        file_path = f"data/20250627_{unique_slug}_market-metadata.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        write_metadata(
            market_slug=unique_slug,
            market_id=12345,
            books=mock_books,
            executed_at=executed_at,
            market_metadata=metadata
        )
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            # Check that missing date is empty string
            assert rows[0]['game_start_timestamp'] == ''
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def test_write_metadata_multiple_runs(self, mock_books, market_metadata):
        """Test that multiple runs append to existing file."""
        executed_at1 = datetime(2025, 6, 27, 12, 0, 0)
        executed_at2 = datetime(2025, 6, 27, 13, 0, 0)
        unique_slug = f"mlb-test-multiple-runs-{executed_at1.timestamp()}"
        
        # Clean up any existing test file
        file_path = f"data/20250627_{unique_slug}_market-metadata.csv"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # First run
        write_metadata(
            market_slug=unique_slug,
            market_id=12345,
            books=mock_books,
            executed_at=executed_at1,
            market_metadata=market_metadata
        )
        
        # Second run
        write_metadata(
            market_slug=unique_slug,
            market_id=12345,
            books=mock_books,
            executed_at=executed_at2,
            market_metadata=market_metadata
        )
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, quotechar='|')
            rows = list(reader)
            
            # Should have 4 rows total (2 per run)
            assert len(rows) == 4
            
            # Check different executed_at timestamps
            assert rows[0]['executed_at'] == str(int(executed_at1.timestamp()))
            assert rows[2]['executed_at'] == str(int(executed_at2.timestamp()))
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def test_field_names_updated(self):
        """Test that field names match new specification."""
        expected_fields = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'executed_at', 'game_start_timestamp']
        assert FIELD_NAMES == expected_fields