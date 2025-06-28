#!/usr/bin/env python3
"""
Script to standardize CSV file naming convention in the data directory.

New format: {YYYYMMDD}_{market_slug}_{file_type}.csv

File type mappings:
- order_book → synthetic-order-book
- Replace underscores with hyphens in file types
"""

import argparse
import logging
import re
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File type mappings
FILE_TYPE_MAPPINGS = {
    'order_book': 'synthetic-order-book',
    'polymarket_market_events': 'polymarket-market-events',
    'synthetic_orders': 'synthetic-order-book',
    'synthetic-orders': 'synthetic-order-book',
    'orders': 'orders'
}


def parse_filename(filename):
    """Parse existing filename to extract components."""
    # Remove .csv extension
    base_name = filename.replace('.csv', '')

    # Try different patterns
    patterns = [
        # Pattern 1: YYYYMMDD_market-slug_file-type (current format)
        r'^(\d{8})_(.+?)_(order_book|polymarket-market-events|synthetic-orders|synthetic_orders|orders)$',
        # Pattern 2: YYYYMMDD-market-slug-file-type (old format)
        r'^(\d{8})-(.+?)-(order_book|polymarket_market_events|synthetic_orders|synthetic-orders|orders)$',
        # Pattern 3: YYYYMMDD-market-slug_file_type (underscore before file type)
        r'^(\d{8})-(.+?)_(order_book|polymarket_market_events|synthetic_orders|synthetic-orders|orders)$',
        # Pattern 4: Special case with version
        r'^(\d{8})-(.+?)-(order_book|polymarket_market_events|synthetic_orders|synthetic-orders|orders)_vers_\d+$',
    ]

    for pattern in patterns:
        match = re.match(pattern, base_name)
        if match:
            date_str = match.group(1)
            market_slug = match.group(2)
            file_type = match.group(3)
            return date_str, market_slug, file_type

    return None, None, None


def get_new_filename(date_str, market_slug, file_type):
    """Generate new filename following the standard convention."""
    # Map file type if needed
    new_file_type = FILE_TYPE_MAPPINGS.get(file_type, file_type)

    # Replace any remaining underscores with hyphens in file type
    new_file_type = new_file_type.replace('_', '-')

    return f"{date_str}_{market_slug}_{new_file_type}.csv"


def rename_files(data_dir, dry_run=True):
    """Rename files in the data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return False

    csv_files = list(data_path.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files")

    renamed_count = 0
    errors = []

    for csv_file in csv_files:
        filename = csv_file.name
        date_str, market_slug, file_type = parse_filename(filename)

        if not all([date_str, market_slug, file_type]):
            logger.warning(f"Could not parse filename: {filename}")
            errors.append(filename)
            continue

        new_filename = get_new_filename(date_str, market_slug, file_type)

        if filename != new_filename:
            old_path = csv_file
            new_path = data_path / new_filename

            if dry_run:
                logger.info(f"[DRY RUN] Would rename: {filename} → {new_filename}")
            else:
                try:
                    # Check if target already exists
                    if new_path.exists():
                        logger.warning(f"Target file already exists: {new_filename}")
                        errors.append(f"Conflict: {filename} → {new_filename}")
                        continue

                    old_path.rename(new_path)
                    logger.info(f"Renamed: {filename} → {new_filename}")
                    renamed_count += 1
                except Exception as e:
                    logger.error(f"Error renaming {filename}: {e}")
                    errors.append(f"Error: {filename} - {str(e)}")

    logger.info(f"{'Would rename' if dry_run else 'Renamed'} {renamed_count} files")

    if errors:
        logger.warning(f"Encountered {len(errors)} errors:")
        for error in errors:
            logger.warning(f"  - {error}")

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Standardize CSV file naming convention")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory (default: data)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without renaming files"
    )

    args = parser.parse_args()

    logger.info(f"Starting file renaming {'(DRY RUN)' if args.dry_run else ''}")
    logger.info(f"Data directory: {args.data_dir}")

    success = rename_files(args.data_dir, args.dry_run)

    if not success:
        sys.exit(1)

    if args.dry_run:
        logger.info("Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()
