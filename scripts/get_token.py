#!/usr/bin/env python3
"""
OAuth2 Token Helper Script

This script helps you obtain OAuth2 tokens for the TickTick MCP server.
It starts a local web server to handle the OAuth callback.

Usage:
    python scripts/get_token.py --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
"""

import argparse
import asyncio
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    sys.exit(1)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth2 callback."""

    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            error = params.get("error", [None])[0]

            if error:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Error: {error}</h1>".encode())
                self.server.oauth_code = None
            elif code:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """)
                self.server.oauth_code = code
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Missing authorization code</h1>")
                self.server.oauth_code = None
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


async def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://ticktick.com/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "scope": "tasks:read tasks:write",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Get OAuth2 tokens for TickTick MCP"
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="TickTick OAuth2 Client ID",
    )
    parser.add_argument(
        "--client-secret",
        required=True,
        help="TickTick OAuth2 Client Secret",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Local port for OAuth callback (default: 8080)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".ticktick-mcp" / "oauth_token.json",
        help="Output path for token file",
    )

    args = parser.parse_args()

    redirect_uri = f"http://127.0.0.1:{args.port}/callback"

    # Build authorization URL
    auth_params = {
        "client_id": args.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "tasks:read tasks:write",
        "state": "mcp_auth",
    }
    auth_url = f"https://ticktick.com/oauth/authorize?{urlencode(auth_params)}"

    print("\n" + "=" * 60)
    print("TickTick OAuth2 Authorization")
    print("=" * 60)
    print(f"\n1. Opening browser to authorize...")
    print(f"\n   If browser doesn't open, visit:\n   {auth_url}\n")

    # Start callback server
    server = HTTPServer(("127.0.0.1", args.port), OAuthCallbackHandler)
    server.oauth_code = None

    # Open browser
    webbrowser.open(auth_url)

    print(f"2. Waiting for callback on port {args.port}...")

    # Wait for callback (with timeout)
    server.timeout = 120  # 2 minutes
    while server.oauth_code is None:
        server.handle_request()

    if not server.oauth_code:
        print("\nError: No authorization code received")
        sys.exit(1)

    print(f"\n3. Got authorization code, exchanging for tokens...")

    # Exchange code for tokens
    try:
        tokens = asyncio.run(exchange_code(
            args.client_id,
            args.client_secret,
            server.oauth_code,
            redirect_uri,
        ))
    except Exception as e:
        print(f"\nError exchanging code: {e}")
        sys.exit(1)

    # Save tokens
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(tokens, f, indent=2)
    args.output.chmod(0o600)

    print(f"\n4. Tokens saved to: {args.output}")
    print(f"\n   Access token expires in: {tokens.get('expires_in', 'unknown')} seconds")
    print("\n" + "=" * 60)
    print("Authorization complete! You can now use the MCP server.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
