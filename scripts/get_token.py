#!/usr/bin/env python3
"""OAuth helper script to obtain WHOOP access token."""

import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
REDIRECT_PORT = 8888
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

SCOPES = [
    "read:profile",
    "read:body_measurement",
    "read:cycles",
    "read:recovery",
    "read:sleep",
    "read:workout",
    "offline",
]


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            if "code" in params:
                self.server.auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Success!</h1><p>You can close this window.</p>")
            else:
                self.server.auth_code = None
                self.send_response(400)
                self.end_headers()
                error = params.get("error", ["unknown"])[0]
                self.wfile.write(f"<h1>Error: {error}</h1>".encode())

    def log_message(self, format, *args):
        pass  # Suppress logging


def get_authorization_code(client_id: str) -> str | None:
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print(f"\nOpening browser for WHOOP authorization...")
    print(f"If browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    server.auth_code = None
    server.handle_request()

    return server.auth_code


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> dict:
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 50)
    print("WHOOP OAuth Token Generator")
    print("=" * 50)
    print("\nPrerequisites:")
    print("1. Create an app at https://developer-dashboard.whoop.com")
    print(f"2. Add redirect URI: {REDIRECT_URI}")
    print()

    client_id = input("Enter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required")
        return

    code = get_authorization_code(client_id)
    if not code:
        print("Error: Failed to get authorization code")
        return

    print("Exchanging code for token...")
    try:
        tokens = exchange_code_for_token(client_id, client_secret, code)
    except httpx.HTTPStatusError as e:
        print(f"Error: {e.response.text}")
        return

    print("\n" + "=" * 50)
    print("SUCCESS! Add this to config/.env:")
    print("=" * 50)
    print(f"\nWHOOP_ACCESS_TOKEN={tokens['access_token']}")

    if "refresh_token" in tokens:
        print(f"\n# Refresh token (save for later):")
        print(f"# WHOOP_REFRESH_TOKEN={tokens['refresh_token']}")

    print(f"\n# Token expires in {tokens.get('expires_in', 'unknown')} seconds")


if __name__ == "__main__":
    main()
