"""Tests for file naming cleanup script."""

import tempfile
from pathlib import Path

from src.utils.cleanup_file_names import get_new_filename, parse_filename, rename_files


class TestFileNameCleanup:
    """Test cases for file name cleanup functionality."""

    def test_parse_filename_standard(self):
        """Test parsing standard filename formats."""
        # Test with hyphen separator
        date, slug, ftype = parse_filename("20250619-mlb-laa-nyy-2025-06-19-order_book.csv")
        assert date == "20250619"
        assert slug == "mlb-laa-nyy-2025-06-19"
        assert ftype == "order_book"

        # Test with underscore separator
        date, slug, ftype = parse_filename("20250619-mlb-laa-nyy-2025-06-19_orders.csv")
        assert date == "20250619"
        assert slug == "mlb-laa-nyy-2025-06-19"
        assert ftype == "orders"

        # Test with version suffix
        date, slug, ftype = parse_filename("20250619-mlb-hou-bal-2025-06-19-order_book_vers_2.csv")
        assert date == "20250619"
        assert slug == "mlb-hou-bal-2025-06-19"
        assert ftype == "order_book"

    def test_parse_filename_invalid(self):
        """Test parsing invalid filename formats."""
        date, slug, ftype = parse_filename("invalid-filename.csv")
        assert date is None
        assert slug is None
        assert ftype is None

    def test_get_new_filename(self):
        """Test generating new filenames."""
        # Test order_book mapping
        new_name = get_new_filename("20250619", "mlb-laa-nyy-2025-06-19", "order_book")
        assert new_name == "20250619_mlb-laa-nyy-2025-06-19_synthetic-order-book.csv"

        # Test polymarket_market_events mapping
        new_name = get_new_filename("20250619", "mlb-laa-nyy-2025-06-19", "polymarket_market_events")
        assert new_name == "20250619_mlb-laa-nyy-2025-06-19_polymarket-market-events.csv"

        # Test orders (no mapping needed)
        new_name = get_new_filename("20250619", "mlb-laa-nyy-2025-06-19", "orders")
        assert new_name == "20250619_mlb-laa-nyy-2025-06-19_orders.csv"

        # Test synthetic_orders mapping
        new_name = get_new_filename("20250624", "mlb-tor-cle-2025-06-24", "synthetic_orders")
        assert new_name == "20250624_mlb-tor-cle-2025-06-24_synthetic-order-book.csv"

    def test_rename_files_dry_run(self):
        """Test renaming files in dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = [
                "20250619-mlb-laa-nyy-2025-06-19-order_book.csv",
                "20250619-mlb-laa-nyy-2025-06-19_orders.csv",
                "20250619-mlb-laa-nyy-2025-06-19-polymarket_market_events.csv"
            ]

            for filename in test_files:
                Path(tmpdir, filename).touch()

            # Run in dry-run mode
            success = rename_files(tmpdir, dry_run=True)
            assert success

            # Verify no files were renamed
            for filename in test_files:
                assert Path(tmpdir, filename).exists()

    def test_rename_files_actual(self):
        """Test actually renaming files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_files = [
                ("20250619-mlb-laa-nyy-2025-06-19-order_book.csv",
                 "20250619_mlb-laa-nyy-2025-06-19_synthetic-order-book.csv"),
                ("20250619-mlb-laa-nyy-2025-06-19_orders.csv",
                 "20250619_mlb-laa-nyy-2025-06-19_orders.csv"),
                ("20250619-mlb-laa-nyy-2025-06-19-polymarket_market_events.csv",
                 "20250619_mlb-laa-nyy-2025-06-19_polymarket-market-events.csv"),
                ("20250619-mlb-hou-bal-2025-06-19-order_book_vers_2.csv",
                 "20250619_mlb-hou-bal-2025-06-19_synthetic-order-book.csv")
            ]

            for old_name, _ in test_files:
                Path(tmpdir, old_name).touch()

            # Run actual rename
            success = rename_files(tmpdir, dry_run=False)
            assert success

            # Verify files were renamed correctly
            for old_name, new_name in test_files:
                assert not Path(tmpdir, old_name).exists()
                assert Path(tmpdir, new_name).exists()

    def test_rename_files_with_conflicts(self):
        """Test handling of filename conflicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files that would conflict
            Path(tmpdir, "20250619-mlb-laa-nyy-2025-06-19-order_book.csv").touch()
            Path(tmpdir, "20250619_mlb-laa-nyy-2025-06-19_synthetic-order-book.csv").touch()

            # Run rename - should report error but not fail completely
            success = rename_files(tmpdir, dry_run=False)
            assert not success  # Should return False due to conflict

            # Original file should still exist
            assert Path(tmpdir, "20250619-mlb-laa-nyy-2025-06-19-order_book.csv").exists()
            assert Path(tmpdir, "20250619_mlb-laa-nyy-2025-06-19_synthetic-order-book.csv").exists()
