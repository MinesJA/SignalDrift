"""Tests for missing market_id fix functionality."""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from src.utils.fix_missing_market_id import MarketIdFixer
from src.daos.market_dao import write_marketEvents


class TestMarketIdFixer:
    """Test cases for MarketIdFixer functionality."""
    
    def test_has_missing_market_id_true(self):
        """Test detection of files with missing market_id."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create CSV with missing market_id (empty values)
            f.write("market_slug,asset_id,market_id,event_type,price\n")
            f.write("test-slug,123,,book,0.5\n")
            f.write("test-slug,456,,price_change,0.6\n")
            temp_path = Path(f.name)
        
        try:
            fixer = MarketIdFixer()
            assert fixer.has_missing_market_id(temp_path)
        finally:
            temp_path.unlink()
    
    def test_has_missing_market_id_false(self):
        """Test detection of files without missing market_id."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create CSV with populated market_id
            f.write("market_slug,asset_id,market_id,event_type,price\n")
            f.write("test-slug,123,554912,book,0.5\n")
            f.write("test-slug,456,554912,price_change,0.6\n")
            temp_path = Path(f.name)
        
        try:
            fixer = MarketIdFixer()
            assert not fixer.has_missing_market_id(temp_path)
        finally:
            temp_path.unlink()
    
    @patch('src.utils.fix_missing_market_id.PolymarketService')
    def test_get_market_id_from_api_success(self, mock_service):
        """Test successful market_id retrieval from API."""
        # Mock the service response
        mock_instance = Mock()
        mock_instance.get_market_by_slug.return_value = {'id': '554912'}
        mock_service.return_value = mock_instance
        
        fixer = MarketIdFixer()
        result = fixer.get_market_id_from_api('test-slug')
        
        assert result == '554912'
        mock_instance.get_market_by_slug.assert_called_once_with('test-slug')
    
    @patch('src.utils.fix_missing_market_id.PolymarketService')
    def test_get_market_id_from_api_cache(self, mock_service):
        """Test that API results are cached."""
        mock_instance = Mock()
        mock_instance.get_market_by_slug.return_value = {'id': '554912'}
        mock_service.return_value = mock_instance
        
        fixer = MarketIdFixer()
        
        # First call should hit API
        result1 = fixer.get_market_id_from_api('test-slug')
        assert result1 == '554912'
        
        # Second call should use cache
        result2 = fixer.get_market_id_from_api('test-slug')
        assert result2 == '554912'
        
        # API should only be called once
        mock_instance.get_market_by_slug.assert_called_once_with('test-slug')
    
    def test_fix_csv_file_dry_run(self):
        """Test CSV fixing in dry-run mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("market_slug,asset_id,market_id,event_type,price\n")
            f.write("test-slug,123,,book,0.5\n")
            temp_path = Path(f.name)
        
        try:
            fixer = MarketIdFixer()
            # Mock the API call
            fixer.get_market_id_from_api = Mock(return_value='554912')
            
            result = fixer.fix_csv_file(temp_path, dry_run=True)
            assert result is True
            
            # File should not be modified in dry-run
            df = pd.read_csv(temp_path)
            assert df['market_id'].isnull().any()
            
        finally:
            temp_path.unlink()


class TestMarketDaoFixes:
    """Test cases for market_dao.py fixes."""
    
    def test_write_market_events_with_market_id(self):
        """Test that write_marketEvents includes market_id in CSV output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for CSV output
            import os
            original_cwd = os.getcwd()
            temp_data_dir = Path(temp_dir) / 'data'
            temp_data_dir.mkdir()
            
            try:
                os.chdir(temp_dir)
                
                # Import the required models
                from src.models.market_event import BookEvent, EventType
                from src.models.synthetic_orderbook import SyntheticOrder
                from src.models.order import OrderSide
                
                # Create MarketEvent objects instead of raw dicts
                market_events = [
                    BookEvent(
                        event_type=EventType.BOOK,
                        market_slug='test-market',
                        market_id=554912,
                        market='test-market-address',
                        asset_id='123456789',
                        outcome_name='Yes',
                        timestamp=1750888000000,
                        hash='test-hash-1',
                        asks=[SyntheticOrder(price=0.6, size=100.0, side=OrderSide.SELL)],
                        bids=[SyntheticOrder(price=0.4, size=200.0, side=OrderSide.BUY)]
                    )
                ]
                
                test_datetime = datetime(2025, 6, 25, 10, 0, 0)
                write_marketEvents('test-market', 554912, market_events, test_datetime, test_mode=True)
                
                # Check that CSV was created with correct data (new underscore format)
                csv_path = temp_data_dir / '20250625_test-market_polymarket-market-events_test.csv'
                assert csv_path.exists()
                
                df = pd.read_csv(csv_path)
                assert len(df) == 2  # One ask, one bid
                assert all(df['market_id'] == 554912)  # Should be int, not string
                assert all(df['market_slug'] == 'test-market')
                assert df['side'].tolist() == ['SELL', 'BUY']
                
            finally:
                os.chdir(original_cwd)
    
    def test_write_market_events_with_none_market_id(self):
        """Test that write_marketEvents handles None market_id gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            import os
            original_cwd = os.getcwd()
            temp_data_dir = Path(temp_dir) / 'data'
            temp_data_dir.mkdir()
            
            try:
                os.chdir(temp_dir)
                
                from src.models.market_event import BookEvent, EventType
                from src.models.synthetic_orderbook import SyntheticOrder
                from src.models.order import OrderSide
                
                # Create MarketEvent objects
                market_events = [
                    BookEvent(
                        event_type=EventType.BOOK,
                        market_slug='test-market',
                        market_id=554912,
                        market='test-market-address',
                        asset_id='123456789',
                        outcome_name='Yes',
                        timestamp=1750888000000,
                        hash='test-hash-1',
                        asks=[SyntheticOrder(price=0.6, size=100.0, side=OrderSide.SELL)],
                        bids=[SyntheticOrder(price=0.4, size=200.0, side=OrderSide.BUY)]
                    )
                ]
                
                test_datetime = datetime(2025, 6, 25, 10, 0, 0)
                
                # Test with None market_id - should not create file and should log error
                write_marketEvents('test-market-none', None, market_events, test_datetime, test_mode=True)
                
                # Check that CSV was NOT created for None market_id
                csv_path = temp_data_dir / '20250625_test-market-none_polymarket-market-events_test.csv'
                assert not csv_path.exists(), "CSV should not be created when market_id is None"
                
            finally:
                os.chdir(original_cwd)