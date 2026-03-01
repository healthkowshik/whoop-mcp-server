"""Fetch the WHOOP OpenAPI spec, patch the missing version, write to file."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any

import httpx

WHOOP_OPENAPI_URL = "https://api.prod.whoop.com/developer/doc/openapi.json"
DEFAULT_VERSION = "2.0.0"

# Overridable transport for testing; production uses ``None`` (default httpx behaviour).
_DEFAULT_TRANSPORT: httpx.BaseTransport | None = None


def fetch_openapi_spec(
    url: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Fetch the OpenAPI spec from *url* and return the parsed JSON.

    Exits with code 1 on HTTP errors and code 2 on JSON parse errors.
    """
    effective_transport = transport or _DEFAULT_TRANSPORT
    try:
        client_kwargs: dict[str, Any] = {}
        if effective_transport is not None:
            client_kwargs["transport"] = effective_transport
        with httpx.Client(**client_kwargs) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"Error: failed to fetch OpenAPI spec: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    try:
        return response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Error: response is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def patch_version(
    spec: dict[str, Any],
    default: str = DEFAULT_VERSION,
) -> dict[str, Any]:
    """Return a copy of *spec* with ``info.version`` set if missing."""
    result = copy.deepcopy(spec)
    info = result.setdefault("info", {})
    if "version" not in info:
        info["version"] = default
    return result


def write_spec(spec: dict[str, Any], output_path: str) -> None:
    """Write *spec* as formatted JSON to *output_path*."""
    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and patch the WHOOP OpenAPI specification.",
    )
    parser.add_argument(
        "--output",
        default="openapi.json",
        help="path to write the corrected spec (default: openapi.json)",
    )
    args = parser.parse_args(argv)

    spec = fetch_openapi_spec(WHOOP_OPENAPI_URL)
    patched = patch_version(spec)
    write_spec(patched, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
