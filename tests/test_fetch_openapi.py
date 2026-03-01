"""Tests for whoop_mcp_server.fetch_openapi."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from openapi_spec_validator import validate

from whoop_mcp_server.fetch_openapi import (
    fetch_openapi_spec,
    main,
    patch_version,
    write_spec,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

UPSTREAM_URL = "https://api.prod.whoop.com/developer/doc/openapi.json"

_OK = {"responses": {"200": {"description": "OK"}}}


def _path_param(name: str) -> dict[str, Any]:
    """Return an OpenAPI 3.0 path parameter object."""
    return {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}


def _op_with_param(name: str) -> dict[str, Any]:
    """Return a GET operation with a single path parameter."""
    return {"get": {**_OK, "parameters": [_path_param(name)]}}


SAMPLE_SPEC_NO_VERSION: dict[str, Any] = {
    "openapi": "3.0.1",
    "info": {"title": "WHOOP API"},
    "servers": [{"url": "https://api.prod.whoop.com"}],
    "tags": [{"name": "Cycle"}],
    "paths": {
        "/v1/activity-mapping/{activityV1Id}": _op_with_param("activityV1Id"),
        "/v2/cycle/{cycleId}": _op_with_param("cycleId"),
        "/v2/cycle": {"get": _OK},
        "/v2/cycle/{cycleId}/sleep": _op_with_param("cycleId"),
        "/v2/recovery": {"get": _OK},
        "/v2/cycle/{cycleId}/recovery": _op_with_param("cycleId"),
        "/v2/activity/sleep/{sleepId}": _op_with_param("sleepId"),
        "/v2/activity/sleep": {"get": _OK},
        "/v2/user/measurement/body": {"get": _OK},
        "/v2/user/profile/basic": {"get": _OK},
        "/v2/user/access": {"delete": _OK},
        "/v2/activity/workout/{workoutId}": _op_with_param("workoutId"),
        "/v2/activity/workout": {"get": _OK},
    },
    "components": {"schemas": {}},
}

SAMPLE_SPEC_WITH_VERSION: dict[str, Any] = {
    **SAMPLE_SPEC_NO_VERSION,
    "info": {"title": "WHOOP API", "version": "3.5.0"},
}


def _mock_transport(spec: dict[str, Any]) -> httpx.MockTransport:
    """Return a mock transport that responds with *spec* as JSON."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=spec)

    return httpx.MockTransport(handler)


# ---------------------------------------------------------------------------
# Tests: patch_version (FR-002, FR-003, FR-004, FR-005)
# ---------------------------------------------------------------------------


class TestPatchVersion:
    def test_adds_version_when_missing(self) -> None:
        """FR-002 / FR-004: version added as '2.0.0' when absent."""
        result = patch_version(SAMPLE_SPEC_NO_VERSION)
        assert result["info"]["version"] == "2.0.0"

    def test_preserves_existing_version(self) -> None:
        """FR-003: existing version is never overwritten."""
        result = patch_version(SAMPLE_SPEC_WITH_VERSION)
        assert result["info"]["version"] == "3.5.0"

    def test_preserves_all_other_fields(self) -> None:
        """FR-005: non-info fields are unchanged."""
        result = patch_version(SAMPLE_SPEC_NO_VERSION)
        assert result["openapi"] == "3.0.1"
        assert result["paths"] == SAMPLE_SPEC_NO_VERSION["paths"]
        assert result["servers"] == SAMPLE_SPEC_NO_VERSION["servers"]
        assert result["tags"] == SAMPLE_SPEC_NO_VERSION["tags"]
        assert result["components"] == SAMPLE_SPEC_NO_VERSION["components"]

    def test_preserves_info_title(self) -> None:
        """FR-005: info.title is not modified when version is patched."""
        result = patch_version(SAMPLE_SPEC_NO_VERSION)
        assert result["info"]["title"] == "WHOOP API"


# ---------------------------------------------------------------------------
# Tests: fetch_openapi_spec (FR-001)
# ---------------------------------------------------------------------------


class TestFetchOpenapiSpec:
    def test_fetches_and_returns_dict(self) -> None:
        """FR-001: fetches JSON from URL and returns a dict."""
        transport = _mock_transport(SAMPLE_SPEC_NO_VERSION)
        result = fetch_openapi_spec(UPSTREAM_URL, transport=transport)
        assert result == SAMPLE_SPEC_NO_VERSION


# ---------------------------------------------------------------------------
# Tests: write_spec (FR-006)
# ---------------------------------------------------------------------------


class TestWriteSpec:
    def test_writes_to_specified_path(self, tmp_path: Path) -> None:
        """FR-006: output is written to the given path."""
        out = tmp_path / "output.json"
        write_spec(SAMPLE_SPEC_NO_VERSION, str(out))
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded == SAMPLE_SPEC_NO_VERSION

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        """FR-006: output file is parseable JSON."""
        out = tmp_path / "output.json"
        write_spec(SAMPLE_SPEC_NO_VERSION, str(out))
        json.loads(out.read_text())  # must not raise


# ---------------------------------------------------------------------------
# Tests: main CLI (FR-006 --output flag, default path)
# ---------------------------------------------------------------------------


class TestMainCli:
    def test_output_flag(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-006: --output flag writes to the specified path."""
        transport = _mock_transport(SAMPLE_SPEC_NO_VERSION)
        out = tmp_path / "custom.json"
        monkeypatch.setattr(
            "whoop_mcp_server.fetch_openapi._DEFAULT_TRANSPORT", transport
        )
        main(["--output", str(out)])
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded["info"]["version"] == "2.0.0"

    def test_default_output_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Default output is 'openapi.json' in the current directory."""
        transport = _mock_transport(SAMPLE_SPEC_NO_VERSION)
        monkeypatch.setattr(
            "whoop_mcp_server.fetch_openapi._DEFAULT_TRANSPORT", transport
        )
        monkeypatch.chdir(tmp_path)
        main([])
        assert (tmp_path / "openapi.json").exists()


# ---------------------------------------------------------------------------
# Tests: error handling (FR-008)
# ---------------------------------------------------------------------------


def _error_transport(status_code: int) -> httpx.MockTransport:
    """Return a transport that responds with the given status code."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="error")

    return httpx.MockTransport(handler)


def _malformed_json_transport() -> httpx.MockTransport:
    """Return a transport that responds with non-JSON content."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not valid json {{{")

    return httpx.MockTransport(handler)


class TestErrorHandling:
    def test_fetch_error_exits_with_code_1(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-008: non-200 response exits with code 1, error on stderr."""
        transport = _error_transport(500)
        with pytest.raises(SystemExit) as exc_info:
            fetch_openapi_spec(UPSTREAM_URL, transport=transport)
        assert exc_info.value.code == 1

    def test_malformed_json_exits_with_code_2(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-008: invalid JSON response exits with code 2, error on stderr."""
        transport = _malformed_json_transport()
        with pytest.raises(SystemExit) as exc_info:
            fetch_openapi_spec(UPSTREAM_URL, transport=transport)
        assert exc_info.value.code == 2

    def test_fetch_error_prints_to_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-008: error message is written to stderr."""
        transport = _error_transport(404)
        with pytest.raises(SystemExit):
            fetch_openapi_spec(UPSTREAM_URL, transport=transport)
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()

    def test_malformed_json_prints_to_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-008: JSON parse error message is written to stderr."""
        transport = _malformed_json_transport()
        with pytest.raises(SystemExit):
            fetch_openapi_spec(UPSTREAM_URL, transport=transport)
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()


# ---------------------------------------------------------------------------
# Tests: OpenAPI validation (SC-003, SC-004)
# ---------------------------------------------------------------------------

EXPECTED_PATHS = [
    "/v1/activity-mapping/{activityV1Id}",
    "/v2/cycle/{cycleId}",
    "/v2/cycle",
    "/v2/cycle/{cycleId}/sleep",
    "/v2/recovery",
    "/v2/cycle/{cycleId}/recovery",
    "/v2/activity/sleep/{sleepId}",
    "/v2/activity/sleep",
    "/v2/user/measurement/body",
    "/v2/user/profile/basic",
    "/v2/user/access",
    "/v2/activity/workout/{workoutId}",
    "/v2/activity/workout",
]


class TestOpenapiValidation:
    def test_patched_spec_is_valid_openapi(self) -> None:
        """SC-003: patched spec passes OpenAPI 3.0 validation."""
        patched = patch_version(SAMPLE_SPEC_NO_VERSION)
        validate(patched)  # raises on failure

    def test_all_13_endpoints_present(self) -> None:
        """SC-004: all 13 upstream endpoints are preserved."""
        patched = patch_version(SAMPLE_SPEC_NO_VERSION)
        paths = list(patched["paths"].keys())
        assert len(paths) == 13
        for path in EXPECTED_PATHS:
            assert path in paths, f"Missing endpoint: {path}"
