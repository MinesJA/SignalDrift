import csv
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

FIELD_NAMES = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'executed_at', 'game_start_timestamp']

def _get_file_path(market_slug: str, executed_at: datetime) -> str:
    """Get the file path for the metadata CSV file."""
    csv_filename = os.path.join('data', f"{executed_at.strftime('%Y%m%d')}_{market_slug}_market-metadata.csv")
    return csv_filename

def _setup_csv(file_path: str) -> None:
    """Set up the CSV file with headers if it doesn't exist."""
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES, quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
        logger.info(f"Created new metadata CSV file: {file_path}")

def _write_to_csv(file_path: str, rows: List[Dict[str, Any]]) -> None:
    """Write rows to the CSV file."""
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES, quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

def write_metadata(
    market_slug: str,
    market_id: int,
    books: List[Any],  # List of SyntheticOrderBook objects
    executed_at: datetime,
    market_metadata: Dict[str, Any]
) -> None:
    """
    Write market metadata to CSV file.
    
    Args:
        market_slug: The market slug identifier
        market_id: The market ID
        books: List of SyntheticOrderBook objects containing asset and outcome info
        executed_at: Timestamp when SignalDrift executed
        market_metadata: Full market metadata from Polymarket API
    """
    try:
        file_path = _get_file_path(market_slug, executed_at)
        _setup_csv(file_path)
        
        # Extract game start time from market metadata
        # Polymarket typically has these fields, but they might be named differently
        game_start_timestamp = None
        
        # Try to extract start time from various possible fields
        for field in ['startDate', 'start_date', 'startTime', 'start_time', 'eventStartDate']:
            if field in market_metadata and market_metadata[field]:
                try:
                    # Convert to epoch timestamp
                    start_dt = datetime.fromisoformat(market_metadata[field].replace('Z', '+00:00'))
                    game_start_timestamp = int(start_dt.timestamp())
                    break
                except:
                    pass
        
        # Convert executed_at to epoch timestamp
        executed_at_timestamp = int(executed_at.timestamp())
        
        # Create a row for each asset/outcome
        rows = []
        for book in books:
            row = {
                'market_slug': market_slug,
                'market_id': market_id,
                'asset_id': book.asset_id,
                'outcome_name': book.outcome_name,
                'executed_at': executed_at_timestamp,
                'game_start_timestamp': game_start_timestamp or ''
            }
            rows.append(row)
        
        _write_to_csv(file_path, rows)
        logger.info(f"Wrote {len(rows)} metadata rows for market {market_slug}")
        
    except Exception as e:
        logger.error(f"Error writing metadata for {market_slug}: {e}")
        raise