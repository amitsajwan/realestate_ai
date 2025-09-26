"""
Datetime utilities for consistent formatting across the PropertyAI platform
"""
from datetime import datetime, timezone
from typing import Optional


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime consistently across all APIs.
    Ensures all datetimes are in ISO format with timezone info.
    """
    if dt is None:
        return None
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def parse_datetime(date_string: str) -> datetime:
    """
    Parse datetime string consistently.
    Handles various input formats and ensures timezone awareness.
    """
    if not date_string:
        raise ValueError("Empty date string")
    
    # Clean up common issues
    date_string = date_string.replace('+00:00', 'Z')
    if not date_string.endswith('Z') and not date_string.includes('+') and not date_string.includes('-', 10):
        date_string += 'Z'
    
    try:
        dt = datetime.fromisoformat(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {date_string}") from e