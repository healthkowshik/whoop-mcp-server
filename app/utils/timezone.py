"""Timezone utilities for converting WHOOP API timestamps.

Converts UTC timestamps to the user's timezone when the event was recorded.
"""

from datetime import datetime, timedelta, timezone


def parse_timezone_offset(offset_str: str) -> timezone:
    """Parse WHOOP timezone offset string to a timezone object.

    Args:
        offset_str: Timezone offset like '+05:30', '-08:00', or '+00:00'

    Returns:
        A timezone object representing the offset
    """
    sign = 1 if offset_str[0] == "+" else -1
    hours, minutes = map(int, offset_str[1:].split(":"))
    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))


def convert_to_local_time(dt: datetime, timezone_offset: str | None) -> datetime:
    """Convert a UTC datetime to the timezone where the event was recorded.

    Args:
        dt: A datetime object (assumed UTC if naive)
        timezone_offset: WHOOP timezone offset string (e.g., '-08:00')

    Returns:
        Datetime converted to the user's timezone at time of recording
    """
    if not timezone_offset:
        return dt

    # Ensure the datetime is timezone-aware (assume UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    tz = parse_timezone_offset(timezone_offset)
    return dt.astimezone(tz)


def format_local_datetime(dt: datetime, timezone_offset: str | None) -> str:
    """Format a datetime for display in the timezone where the event was recorded.

    Args:
        dt: A datetime object (assumed UTC if naive)
        timezone_offset: WHOOP timezone offset string (e.g., '-08:00')

    Returns:
        Formatted string like '2024-01-15 10:30 PM (-08:00)'
    """
    if timezone_offset:
        local_dt = convert_to_local_time(dt, timezone_offset)
        return f"{local_dt.strftime('%Y-%m-%d %I:%M %p')} ({timezone_offset})"
    return dt.isoformat()


def process_record_timestamps(record: dict) -> dict:
    """Convert timestamps to the user's timezone when the event was recorded.

    Overwrites `start` and `end` with human-readable times in the timezone
    where the user was located when the activity occurred (based on timezone_offset).
    Also calculates duration_hours if both start and end are present.

    Args:
        record: A WHOOP API record dict with start, end, and timezone_offset

    Returns:
        The record with timestamps converted to user's timezone at time of recording
        and duration_hours added if applicable
    """
    tz_offset = record.get("timezone_offset")
    
    # Parse datetimes for duration calculation
    start_dt = None
    end_dt = None
    
    if "start" in record and record["start"]:
        start = record["start"]
        if isinstance(start, str):
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        else:
            start_dt = start
    
    if "end" in record and record["end"]:
        end = record["end"]
        if isinstance(end, str):
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        else:
            end_dt = end
    
    # Calculate duration_hours if both start and end exist
    if start_dt and end_dt:
        delta = end_dt - start_dt
        record["duration_hours"] = round(delta.total_seconds() / 3600, 2)
    else:
        record["duration_hours"] = None
    
    # Convert timestamps to formatted strings if timezone_offset is available
    if tz_offset:
        if start_dt:
            record["start"] = format_local_datetime(start_dt, tz_offset)
        if end_dt:
            record["end"] = format_local_datetime(end_dt, tz_offset)

    return record


def process_response_timestamps(response: dict) -> dict:
    """Convert timestamps in a paginated API response to user's timezone when recorded.

    Args:
        response: A WHOOP API response with 'records' list

    Returns:
        The response with timestamps converted to user's timezone at time of recording
    """
    if "records" in response and isinstance(response["records"], list):
        response["records"] = [
            process_record_timestamps(record) for record in response["records"]
        ]
    elif "error" not in response:
        # Single record response
        response = process_record_timestamps(response)

    return response
