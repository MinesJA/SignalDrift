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
            'endDate': '2025-06-27T22:00:00Z',
            'outcomes': '["Team A", "Team B"]',
            'clobTokenIds': '["1", "2"]'
        }
    
    def test_get_file_path(self, temp_data_dir):
        """Test file path generation."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            # Test normal mode
            path = _get_file_path("mlb-test-match", test_mode=False)
            assert path.endswith("data/metadata_mlb-test-match.csv")
            
            # Test test mode
            path = _get_file_path("mlb-test-match", test_mode=True)
            assert path.endswith("data/metadata_mlb-test-match_test.csv")
    
    def test_write_metadata_creates_file(self, temp_data_dir, mock_books, market_metadata):
        """Test that metadata writer creates file with correct headers."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            run_at = datetime(2025, 6, 27, 12, 0, 0)
            unique_slug = "mlb-test-create-file"
            
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at,
                market_metadata=market_metadata,
                test_mode=False
            )
            
            # Check file was created
            file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}.csv')
            file_path = os.path.normpath(file_path)
            assert os.path.exists(file_path)
            
            # Check headers
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f, quotechar='|')
                assert reader.fieldnames == FIELD_NAMES
    
    def test_write_metadata_appends_rows(self, temp_data_dir, mock_books, market_metadata):
        """Test that metadata writer appends correct data."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            run_at = datetime(2025, 6, 27, 12, 0, 0)
            unique_slug = "mlb-test-append-rows"
            
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at,
                market_metadata=market_metadata,
                test_mode=False
            )
            
            file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}.csv')
            file_path = os.path.normpath(file_path)
            
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
                assert rows[0]['run_at'] == str(int(run_at.timestamp()))
                # Check that dates were parsed (should be epoch timestamps)
                assert rows[0]['game_start_at'].isdigit()
                assert rows[0]['game_end_at'].isdigit()
                
                # Check second row
                assert rows[1]['asset_id'] == '2'
                assert rows[1]['outcome_name'] == 'Team B'
    
    def test_write_metadata_handles_missing_dates(self, temp_data_dir, mock_books):
        """Test handling of missing start/end dates."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            # Market metadata without dates
            unique_slug = "mlb-test-missing-dates"
            metadata = {
                'id': 12345,
                'slug': unique_slug
            }
            
            run_at = datetime(2025, 6, 27, 12, 0, 0)
            
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at,
                market_metadata=metadata,
                test_mode=False
            )
            
            file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}.csv')
            file_path = os.path.normpath(file_path)
            
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f, quotechar='|')
                rows = list(reader)
                
                # Check that missing dates are empty strings
                assert rows[0]['game_start_at'] == ''
                assert rows[0]['game_end_at'] == ''
    
    def test_write_metadata_multiple_runs(self, temp_data_dir, mock_books, market_metadata):
        """Test that multiple runs append to existing file."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            unique_slug = "mlb-test-multiple-runs"
            
            # First run
            run_at1 = datetime(2025, 6, 27, 12, 0, 0)
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at1,
                market_metadata=market_metadata,
                test_mode=False
            )
            
            # Second run
            run_at2 = datetime(2025, 6, 27, 13, 0, 0)
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at2,
                market_metadata=market_metadata,
                test_mode=False
            )
            
            file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}.csv')
            file_path = os.path.normpath(file_path)
            
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f, quotechar='|')
                rows = list(reader)
                
                # Should have 4 rows total (2 per run)
                assert len(rows) == 4
                
                # Check different run_at timestamps
                assert rows[0]['run_at'] == str(int(run_at1.timestamp()))
                assert rows[2]['run_at'] == str(int(run_at2.timestamp()))
    
    def test_write_metadata_test_mode(self, temp_data_dir, mock_books, market_metadata):
        """Test that test mode creates separate file."""
        with patch('daos.metadata_dao.os.path.dirname') as mock_dirname:
            mock_dirname.return_value = temp_data_dir
            
            unique_slug = "mlb-test-mode-unique"
            run_at = datetime(2025, 6, 27, 12, 0, 0)
            
            # Write in test mode
            write_metadata(
                market_slug=unique_slug,
                market_id=12345,
                books=mock_books,
                run_at=run_at,
                market_metadata=market_metadata,
                test_mode=True
            )
            
            # Check test file was created
            test_file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}_test.csv')
            test_file_path = os.path.normpath(test_file_path)
            assert os.path.exists(test_file_path)
            
            # Check normal file was NOT created
            normal_file_path = os.path.join(temp_data_dir, '..', '..', 'data', f'metadata_{unique_slug}.csv')
            normal_file_path = os.path.normpath(normal_file_path)
            assert not os.path.exists(normal_file_path)