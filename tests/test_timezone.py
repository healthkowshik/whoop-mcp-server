"""Tests for timezone utilities."""

from datetime import datetime, timezone, timedelta

import pytest

from app.utils.timezone import (
    parse_timezone_offset,
    convert_to_local_time,
    preprocess_timestamps,
    preprocess_response,
)


class TestParseTimezoneOffset:
    def test_positive_offset(self):
        tz = parse_timezone_offset("+05:30")
        assert tz == timezone(timedelta(hours=5, minutes=30))

    def test_negative_offset(self):
        tz = parse_timezone_offset("-08:00")
        assert tz == timezone(timedelta(hours=-8))

    def test_zero_offset(self):
        tz = parse_timezone_offset("+00:00")
        assert tz == timezone.utc


class TestConvertToLocalTime:
    def test_convert_utc_to_pacific(self):
        local_dt = convert_to_local_time("2024-01-15T18:30:00Z", "-08:00")
        assert local_dt.hour == 10
        assert local_dt.minute == 30

    def test_convert_utc_to_india(self):
        local_dt = convert_to_local_time("2024-01-15T18:30:00Z", "+05:30")
        # 18:30 UTC + 5:30 = 00:00 next day
        assert local_dt.hour == 0
        assert local_dt.minute == 0
        assert local_dt.day == 16

    def test_no_offset_returns_utc(self):
        result = convert_to_local_time("2024-01-15T18:30:00Z", None)
        assert result.hour == 18
        assert result.minute == 30


class TestPreprocessTimestamps:
    def test_converts_to_local_datetime_objects(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
            "timezone_offset": "-08:00",
        }
        result = preprocess_timestamps(record)
        # Should be datetime objects, not strings
        assert isinstance(result["start"], datetime)
        assert isinstance(result["end"], datetime)
        # Converted to local time
        assert result["start"].hour == 10  # 18:30 UTC - 8 hours
        assert result["end"].hour == 18    # 02:30 UTC - 8 hours (previous day)

    def test_handles_missing_end(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "timezone_offset": "-08:00",
        }
        result = preprocess_timestamps(record)
        assert isinstance(result["start"], datetime)
        assert "end" not in result

    def test_handles_null_end(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": None,
            "timezone_offset": "-08:00",
        }
        result = preprocess_timestamps(record)
        assert isinstance(result["start"], datetime)
        assert result["end"] is None

    def test_no_offset_still_parses_datetime(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
        }
        result = preprocess_timestamps(record)
        assert isinstance(result["start"], datetime)
        assert isinstance(result["end"], datetime)
        # Should remain in UTC
        assert result["start"].hour == 18
        assert result["end"].hour == 2

    def test_preserves_other_fields(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "timezone_offset": "-08:00",
            "score_state": "SCORED",
            "score": {"strain": 10.5},
        }
        result = preprocess_timestamps(record)
        assert result["id"] == "123"
        assert result["score_state"] == "SCORED"
        assert result["score"] == {"strain": 10.5}


class TestPreprocessResponse:
    def test_processes_paginated_response(self):
        response = {
            "records": [
                {
                    "id": "1",
                    "start": "2024-01-15T18:30:00Z",
                    "end": "2024-01-16T02:30:00Z",
                    "timezone_offset": "-08:00",
                },
                {
                    "id": "2",
                    "start": "2024-01-16T19:00:00Z",
                    "end": "2024-01-17T03:00:00Z",
                    "timezone_offset": "+05:30",
                },
            ],
            "has_more": False,
        }
        result = preprocess_response(response)
        assert isinstance(result["records"][0]["start"], datetime)
        assert isinstance(result["records"][1]["start"], datetime)
        # First record: 18:30 UTC - 8 hours = 10:30 local
        assert result["records"][0]["start"].hour == 10
        # Second record: 19:00 UTC + 5:30 = 00:30 next day local
        assert result["records"][1]["start"].hour == 0
        assert result["records"][1]["start"].minute == 30

    def test_processes_single_record(self):
        response = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
            "timezone_offset": "-08:00",
        }
        result = preprocess_response(response)
        assert isinstance(result["start"], datetime)
        assert result["start"].hour == 10

    def test_skips_error_response(self):
        response = {"error": "Not found", "status_code": 404}
        result = preprocess_response(response)
        assert result == response
