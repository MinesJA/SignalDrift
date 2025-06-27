import csv
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

FIELD_NAMES = ['market_slug', 'market_id', 'asset_id', 'outcome_name', 'run_at', 'game_start_at', 'game_end_at']

def _get_file_path(market_slug: str, test_mode: bool = False) -> str:
    """Get the file path for the metadata CSV file."""
    file_name = f"metadata_{market_slug}"
    
    if test_mode:
        file_name = f"{file_name}_test"
    
    file_name = f"{file_name}.csv"
    
    # Get the data directory path (parent of src)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', '..', 'data')
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    return os.path.join(data_dir, file_name)

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
    run_at: datetime,
    market_metadata: Dict[str, Any],
    test_mode: bool = False
) -> None:
    """
    Write market metadata to CSV file.
    
    Args:
        market_slug: The market slug identifier
        market_id: The market ID
        books: List of SyntheticOrderBook objects containing asset and outcome info
        run_at: Timestamp when SignalDrift executed
        market_metadata: Full market metadata from Polymarket API
        test_mode: Whether to use test file suffix
    """
    try:
        file_path = _get_file_path(market_slug, test_mode)
        _setup_csv(file_path)
        
        # Extract game start and end times from market metadata
        # Polymarket typically has these fields, but they might be named differently
        game_start_at = None
        game_end_at = None
        
        # Try to extract start time from various possible fields
        for field in ['startDate', 'start_date', 'startTime', 'start_time', 'eventStartDate']:
            if field in market_metadata and market_metadata[field]:
                try:
                    # Convert to epoch timestamp
                    start_dt = datetime.fromisoformat(market_metadata[field].replace('Z', '+00:00'))
                    game_start_at = int(start_dt.timestamp())
                    break
                except:
                    pass
        
        # Try to extract end time from various possible fields
        for field in ['endDate', 'end_date', 'endTime', 'end_time', 'eventEndDate', 'closeDate']:
            if field in market_metadata and market_metadata[field]:
                try:
                    # Convert to epoch timestamp
                    end_dt = datetime.fromisoformat(market_metadata[field].replace('Z', '+00:00'))
                    game_end_at = int(end_dt.timestamp())
                    break
                except:
                    pass
        
        # Convert run_at to epoch timestamp
        run_at_timestamp = int(run_at.timestamp())
        
        # Create a row for each asset/outcome
        rows = []
        for book in books:
            row = {
                'market_slug': market_slug,
                'market_id': market_id,
                'asset_id': book.asset_id,
                'outcome_name': book.outcome_name,
                'run_at': run_at_timestamp,
                'game_start_at': game_start_at or '',
                'game_end_at': game_end_at or ''
            }
            rows.append(row)
        
        _write_to_csv(file_path, rows)
        logger.info(f"Wrote {len(rows)} metadata rows for market {market_slug}")
        
    except Exception as e:
        logger.error(f"Error writing metadata for {market_slug}: {e}")
        raise