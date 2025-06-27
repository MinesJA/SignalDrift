#!/usr/bin/env python3
"""
Script to backfill existing orders CSV files to match the new format.

The old format had these columns:
market_slug,asset_id,market_id,price,size,side,timestamp

The new format should have these columns (based on Order class):
asset_id,market_slug,order_type,price,size,timestamp

This script will:
1. Read each existing orders CSV file
2. Convert the data to the new format
3. Create a backup of the original file
4. Write the converted data to the original filename
"""

import os
import csv
import glob
import shutil
from datetime import datetime
import argparse


def convert_side_to_order_type(side):
    """Convert old 'side' field to new 'order_type' field."""
    # Based on the data, 'bid' likely means LIMIT_BUY
    # This is an assumption - adjust if needed based on actual logic
    if side.lower() == 'bid':
        return 'LIMIT_BUY'
    elif side.lower() == 'ask':
        return 'LIMIT_SELL'
    else:
        # Default to LIMIT_BUY if unclear
        return 'LIMIT_BUY'


def backfill_csv_file(filepath, dry_run=False):
    """
    Convert a single CSV file to the new format.
    
    Args:
        filepath: Path to the CSV file to convert
        dry_run: If True, don't actually modify files, just report what would be done
    """
    print(f"\nProcessing: {filepath}")
    
    # Read the existing data
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        existing_headers = reader.fieldnames
        rows = list(reader)
    
    # Check if file is already in new format
    expected_headers = ['asset_id', 'market_slug', 'order_type', 'price', 'size', 'timestamp']
    if existing_headers == expected_headers:
        print(f"  Skipping - file already in new format")
        return
    
    # Handle files with only headers (no data rows)
    if not rows:
        print(f"  Converting headers for empty file")
        if dry_run:
            print(f"    Would update headers from: {existing_headers}")
            print(f"    Would update headers to: {expected_headers}")
        else:
            # Create backup
            backup_path = filepath + '.backup'
            shutil.copy2(filepath, backup_path)
            print(f"  Created backup: {backup_path}")
            
            # Write just the new headers
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=expected_headers)
                writer.writeheader()
            
            print(f"  Updated headers successfully")
        return
    
    # Convert the data
    new_rows = []
    for row in rows:
        new_row = {
            'asset_id': row.get('asset_id', ''),
            'market_slug': row.get('market_slug', ''),
            'order_type': convert_side_to_order_type(row.get('side', 'bid')),
            'price': row.get('price', ''),
            'size': row.get('size', ''),
            'timestamp': row.get('timestamp', '')
        }
        new_rows.append(new_row)
    
    if dry_run:
        print(f"  Would convert {len(rows)} rows")
        print(f"  Old headers: {existing_headers}")
        print(f"  New headers: {expected_headers}")
        if rows:
            print(f"  Sample conversion:")
            print(f"    Old: {rows[0]}")
            print(f"    New: {new_rows[0]}")
    else:
        # Create backup
        backup_path = filepath + '.backup'
        shutil.copy2(filepath, backup_path)
        print(f"  Created backup: {backup_path}")
        
        # Write the converted data
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=expected_headers)
            writer.writeheader()
            writer.writerows(new_rows)
        
        print(f"  Converted {len(rows)} rows successfully")


def main():
    parser = argparse.ArgumentParser(description='Backfill orders CSV files to new format')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without actually modifying files')
    parser.add_argument('--data-dir', default='data', 
                        help='Directory containing CSV files (default: data)')
    args = parser.parse_args()
    
    # Find all orders CSV files
    pattern = os.path.join(args.data_dir, '*_orders*.csv')
    csv_files = glob.glob(pattern)
    
    # Exclude backup files
    csv_files = [f for f in csv_files if not f.endswith('.backup')]
    
    if not csv_files:
        print(f"No orders CSV files found in {args.data_dir}")
        return
    
    print(f"Found {len(csv_files)} orders CSV files to process")
    
    for filepath in csv_files:
        try:
            backfill_csv_file(filepath, dry_run=args.dry_run)
        except Exception as e:
            print(f"  ERROR processing {filepath}: {e}")
            continue
    
    print("\nBackfill complete!")
    if args.dry_run:
        print("This was a dry run - no files were modified")


if __name__ == '__main__':
    main()