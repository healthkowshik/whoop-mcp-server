"""Tests for timezone utilities."""

from datetime import datetime, timezone, timedelta

import pytest

from app.utils.timezone import (
    parse_timezone_offset,
    convert_to_local_time,
    format_local_datetime,
    process_record_timestamps,
    process_response_timestamps,
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
        dt = datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc)
        local_dt = convert_to_local_time(dt, "-08:00")
        assert local_dt.hour == 10
        assert local_dt.minute == 30

    def test_convert_naive_datetime(self):
        # Naive datetime should be assumed UTC
        dt = datetime(2024, 1, 15, 18, 30, 0)
        local_dt = convert_to_local_time(dt, "-08:00")
        assert local_dt.hour == 10

    def test_no_offset_returns_original(self):
        dt = datetime(2024, 1, 15, 18, 30, 0)
        result = convert_to_local_time(dt, None)
        assert result == dt


class TestFormatLocalDatetime:
    def test_format_with_offset(self):
        dt = datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc)
        result = format_local_datetime(dt, "-08:00")
        assert result == "2024-01-15 10:30 AM (-08:00)"

    def test_format_without_offset(self):
        dt = datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc)
        result = format_local_datetime(dt, None)
        assert "2024-01-15" in result


class TestProcessRecordTimestamps:
    def test_converts_to_local_times(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
            "timezone_offset": "-08:00",
        }
        result = process_record_timestamps(record)
        assert "10:30 AM" in result["start"]
        assert "06:30 PM" in result["end"]

    def test_no_offset_preserves_original(self):
        record = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
        }
        result = process_record_timestamps(record)
        assert result["start"] == "2024-01-15T18:30:00Z"
        assert result["end"] == "2024-01-16T02:30:00Z"


class TestProcessResponseTimestamps:
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
        result = process_response_timestamps(response)
        assert "(-08:00)" in result["records"][0]["start"]
        assert "(+05:30)" in result["records"][1]["start"]

    def test_processes_single_record(self):
        response = {
            "id": "123",
            "start": "2024-01-15T18:30:00Z",
            "end": "2024-01-16T02:30:00Z",
            "timezone_offset": "-08:00",
        }
        result = process_response_timestamps(response)
        assert "10:30 AM" in result["start"]

    def test_skips_error_response(self):
        response = {"error": "Not found", "status_code": 404}
        result = process_response_timestamps(response)
        assert result == response
