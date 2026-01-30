"""Timezone utilities for converting WHOOP API timestamps.

Converts UTC timestamps to the user's local timezone when the event was recorded.
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


def convert_to_local_time(iso_string: str, timezone_offset: str | None) -> datetime:
    """Convert an ISO datetime string to the user's local timezone.

    Args:
        iso_string: ISO 8601 datetime string (e.g., '2024-01-08T17:30:00Z')
        timezone_offset: WHOOP timezone offset string (e.g., '+05:30')

    Returns:
        Datetime in the user's local timezone
    """
    # Parse ISO string to datetime
    dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))

    if not timezone_offset:
        return dt

    # Convert to local timezone
    tz = parse_timezone_offset(timezone_offset)
    return dt.astimezone(tz)


def preprocess_timestamps(record: dict) -> dict:
    """Convert ISO timestamp strings to local datetime objects.

    Converts 'start', 'end', 'created_at', 'updated_at' fields from ISO strings
    to datetime objects in the user's local timezone (based on timezone_offset).

    Args:
        record: A WHOOP API record dict with timestamp fields

    Returns:
        The record with timestamp strings converted to local datetime objects
    """
    tz_offset = record.get("timezone_offset")
    timestamp_fields = ["start", "end", "created_at", "updated_at"]

    for field in timestamp_fields:
        if field in record and record[field] is not None:
            value = record[field]
            if isinstance(value, str):
                record[field] = convert_to_local_time(value, tz_offset)

    return record


def preprocess_response(response: dict) -> dict:
    """Convert timestamps in a paginated API response.

    Args:
        response: A WHOOP API response with 'records' list or single record

    Returns:
        The response with timestamp strings converted to local datetime objects
    """
    if "records" in response and isinstance(response["records"], list):
        response["records"] = [
            preprocess_timestamps(record) for record in response["records"]
        ]
    elif "error" not in response:
        # Single record response
        response = preprocess_timestamps(response)

    return response
