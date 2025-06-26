#!/usr/bin/env python3
"""
Script to fix missing market_id values in polymarket-market-events CSV files.

This script:
1. Identifies CSV files with missing market_id values (showing as empty fields)
2. Fetches market_id using market_slug via Polymarket API
3. Updates CSV files with correct market_id values
4. Creates backups before making changes
"""

import os
import sys
import argparse
import logging
import pandas as pd
from pathlib import Path
import shutil
from datetime import datetime
import json
import requests
from typing import Dict, Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.polymarket_service import PolymarketService


class MarketIdFixer:
    """Fixes missing market_id values in CSV files."""
    
    def __init__(self):
        self.polymarket_service = PolymarketService()
        self.market_id_cache = {}  # Cache to avoid repeated API calls
        
    def get_market_id_from_api(self, market_slug: str) -> Optional[str]:
        """Get market_id from Polymarket API using market_slug."""
        if market_slug in self.market_id_cache:
            return self.market_id_cache[market_slug]
        
        try:
            # First try with active markets
            market_data = self.polymarket_service.get_market_by_slug(market_slug)
            
            # If not found, try with closed markets
            if not market_data:
                market_data = self.get_market_by_slug_any_status(market_slug)
            
            if market_data and 'id' in market_data:
                market_id = str(market_data['id'])
                self.market_id_cache[market_slug] = market_id
                logger.info(f"Found market_id {market_id} for slug {market_slug}")
                return market_id
            else:
                logger.warning(f"No market_id found for slug {market_slug}")
                return None
        except Exception as e:
            logger.error(f"Error fetching market_id for {market_slug}: {e}")
            return None
    
    def get_market_by_slug_any_status(self, market_slug: str) -> Optional[Dict[str, Any]]:
        """Get market information including closed markets."""
        try:
            gamma_api_base = self.polymarket_service.gamma_api_base
            headers = self.polymarket_service.headers
            
            url = f"{gamma_api_base}/markets"
            params = {
                'slug': market_slug,
                # Don't filter by active/closed status to include all markets
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            markets = response.json()
            
            if not markets:
                return None
                
            return markets[0]  # Return the first matching market
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching any-status market data: {e}")
            return None
    
    def has_missing_market_id(self, csv_file_path: Path) -> bool:
        """Check if CSV file has missing market_id values."""
        try:
            # Read just a few rows to check
            df = pd.read_csv(csv_file_path, nrows=5)
            
            # Check if market_id column exists and has missing values
            if 'market_id' in df.columns:
                return df['market_id'].isnull().any() or (df['market_id'] == '').any()
            else:
                logger.warning(f"No market_id column found in {csv_file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error reading {csv_file_path}: {e}")
            return False
    
    def fix_csv_file(self, csv_file_path: Path, dry_run: bool = True) -> bool:
        """Fix missing market_id values in a single CSV file."""
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path)
            
            if 'market_id' not in df.columns:
                logger.warning(f"No market_id column in {csv_file_path}")
                return False
            
            # Check if there are missing market_id values
            missing_mask = df['market_id'].isnull() | (df['market_id'] == '')
            if not missing_mask.any():
                logger.info(f"No missing market_id values in {csv_file_path}")
                return True
            
            missing_count = missing_mask.sum()
            logger.info(f"Found {missing_count} missing market_id values in {csv_file_path}")
            
            # Get unique market_slugs that need fixing
            unique_slugs = df[missing_mask]['market_slug'].unique()
            
            # Fetch market_id for each unique slug
            slug_to_market_id = {}
            for slug in unique_slugs:
                market_id = self.get_market_id_from_api(slug)
                if market_id:
                    slug_to_market_id[slug] = market_id
                else:
                    logger.error(f"Could not fetch market_id for slug: {slug}")
                    return False
            
            if dry_run:
                logger.info(f"[DRY RUN] Would fix {missing_count} rows with market_id mappings:")
                for slug, market_id in slug_to_market_id.items():
                    count = len(df[missing_mask & (df['market_slug'] == slug)])
                    logger.info(f"  {slug} → {market_id} ({count} rows)")
                return True
            
            # Apply fixes
            for slug, market_id in slug_to_market_id.items():
                mask = missing_mask & (df['market_slug'] == slug)
                df.loc[mask, 'market_id'] = market_id
                fixed_count = mask.sum()
                logger.info(f"Fixed {fixed_count} rows for {slug} → {market_id}")
            
            # Create backup
            backup_path = csv_file_path.with_suffix('.csv.backup')
            shutil.copy2(csv_file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            
            # Write fixed CSV
            df.to_csv(csv_file_path, index=False)
            logger.info(f"Successfully fixed {csv_file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing {csv_file_path}: {e}")
            return False
    
    def scan_and_fix_directory(self, data_dir: str, dry_run: bool = True) -> bool:
        """Scan directory for polymarket-market-events files and fix missing market_id."""
        data_path = Path(data_dir)
        if not data_path.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return False
        
        # Find polymarket-market-events CSV files
        pattern = "*polymarket*market*events*.csv"
        csv_files = list(data_path.glob(pattern))
        
        if not csv_files:
            logger.warning(f"No polymarket-market-events CSV files found in {data_dir}")
            return True
        
        logger.info(f"Found {len(csv_files)} polymarket-market-events files")
        
        files_with_issues = []
        files_fixed = []
        files_failed = []
        
        # Check each file for missing market_id
        for csv_file in csv_files:
            if self.has_missing_market_id(csv_file):
                files_with_issues.append(csv_file)
        
        if not files_with_issues:
            logger.info("No files with missing market_id found!")
            return True
        
        logger.info(f"Found {len(files_with_issues)} files with missing market_id values")
        
        # Fix each file
        for csv_file in files_with_issues:
            logger.info(f"Processing {csv_file.name}...")
            
            if self.fix_csv_file(csv_file, dry_run):
                files_fixed.append(csv_file)
            else:
                files_failed.append(csv_file)
        
        # Summary
        logger.info(f"Summary:")
        logger.info(f"  Files with issues: {len(files_with_issues)}")
        logger.info(f"  Files {'would be ' if dry_run else ''}fixed: {len(files_fixed)}")
        logger.info(f"  Files failed: {len(files_failed)}")
        
        if files_failed:
            logger.error("Failed files:")
            for f in files_failed:
                logger.error(f"  - {f}")
        
        return len(files_failed) == 0


def main():
    parser = argparse.ArgumentParser(description="Fix missing market_id values in polymarket CSV files")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory (default: data)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting market_id fix {'(DRY RUN)' if args.dry_run else ''}")
    logger.info(f"Data directory: {args.data_dir}")
    
    fixer = MarketIdFixer()
    success = fixer.scan_and_fix_directory(args.data_dir, args.dry_run)
    
    if not success:
        sys.exit(1)
    
    if args.dry_run:
        logger.info("Run without --dry-run to apply changes")


if __name__ == "__main__":
    main()