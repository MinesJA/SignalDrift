"""Tests for missing market_id fix functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from src.daos.market_dao import (
    _create_book_rows,
    _create_price_change_rows,
    write_marketMessages,
)
from src.utils.fix_missing_market_id import MarketIdFixer


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

    def test_create_book_rows_with_market_id(self):
        """Test that book rows include market_id when provided."""
        event = {
            'event_type': 'book',
            'asset_id': '123456',
            'asks': [{'price': '0.5', 'size': '100', 'hash': 'abc123'}],
            'bids': [{'price': '0.4', 'size': '200', 'hash': 'def456'}],
            'timestamp': 1750888000000
        }

        rows = _create_book_rows('test-slug', event, market_id='554912')

        assert len(rows) == 2  # One ask, one bid

        # Check ask row
        ask_row = rows[0]
        assert ask_row['market_slug'] == 'test-slug'
        assert ask_row['market_id'] == '554912'
        assert ask_row['side'] == 'ask'
        assert ask_row['price'] == '0.5'

        # Check bid row
        bid_row = rows[1]
        assert bid_row['market_slug'] == 'test-slug'
        assert bid_row['market_id'] == '554912'
        assert bid_row['side'] == 'bid'
        assert bid_row['price'] == '0.4'

    def test_create_price_change_rows_with_market_id(self):
        """Test that price change rows include market_id when provided."""
        event = {
            'event_type': 'price_change',
            'asset_id': '123456',
            'changes': [
                {'side': 'BUY', 'price': '0.55', 'size': '150', 'hash': 'xyz789'}
            ],
            'timestamp': 1750888000000
        }

        rows = _create_price_change_rows('test-slug', event, market_id='554912')

        assert len(rows) == 1

        row = rows[0]
        assert row['market_slug'] == 'test-slug'
        assert row['market_id'] == '554912'
        assert row['side'] == 'bid'  # BUY -> bid
        assert row['price'] == '0.55'

    def test_create_book_rows_without_market_id(self):
        """Test that book rows handle missing market_id gracefully."""
        event = {
            'event_type': 'book',
            'asset_id': '123456',
            'asks': [{'price': '0.5', 'size': '100', 'hash': 'abc123'}],
            'bids': [],
            'timestamp': 1750888000000
        }

        rows = _create_book_rows('test-slug', event)  # No market_id provided

        assert len(rows) == 1  # One ask, no bids

        ask_row = rows[0]
        assert ask_row['market_slug'] == 'test-slug'
        assert ask_row['market_id'] is None  # Should be None, not missing
        assert ask_row['side'] == 'ask'

    def test_write_market_messages_with_market_id(self):
        """Test that write_marketMessages includes market_id in CSV output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for CSV output
            import os
            original_cwd = os.getcwd()
            temp_data_dir = Path(temp_dir) / 'data'
            temp_data_dir.mkdir()

            try:
                os.chdir(temp_dir)

                market_messages = [{
                    'event_type': 'book',
                    'asset_id': '123456789',
                    'asks': [{'price': '0.6', 'size': '100', 'hash': 'test123'}],
                    'bids': [{'price': '0.4', 'size': '200', 'hash': 'test456'}],
                    'timestamp': 1750888000000
                }]

                test_datetime = datetime(2025, 6, 25, 10, 0, 0)
                write_marketMessages('test-market', test_datetime, market_messages, market_id='554912')

                # Check that CSV was created with correct data (new underscore format)
                csv_path = temp_data_dir / '20250625_test-market_polymarket-market-events.csv'
                assert csv_path.exists()

                df = pd.read_csv(csv_path)
                assert len(df) == 2  # One ask, one bid
                assert all(df['market_id'] == 554912)  # Should be int, not string
                assert all(df['market_slug'] == 'test-market')
                assert df['side'].tolist() == ['ask', 'bid']

            finally:
                os.chdir(original_cwd)
