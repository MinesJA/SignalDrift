from datetime import datetime


# TODO: May not need this after all
def datetime_to_epoch(dt: datetime) -> int:
    """
    Convert a datetime object to epoch time in milliseconds.

    Args:
        dt: datetime object to convert

    Returns:
        int: Epoch time in milliseconds

    Example:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 1, 1, 0, 0, 0)
        >>> epoch_ms = datetime_to_epoch(dt)
        >>> print(epoch_ms)
        1704067200000
    """
    return int(dt.timestamp() * 1000)
