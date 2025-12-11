"""
TickTick MCP CLI - Command-line interface for authentication and management.
"""

import argparse
import asyncio
import json
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

try:
    import httpx
except ImportError:
    print("Please install httpx: pip install httpx")
    sys.exit(1)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth2 callback."""

    def do_GET(self):
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
                <html><body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window.</p>
                </body></html>
                """)
                self.server.oauth_code = code
            else:
                self.send_response(400)
                self.end_headers()
                self.server.oauth_code = None
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
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


def auth_command():
    """Authentication command entry point."""
    parser = argparse.ArgumentParser(description="TickTick MCP Authentication")
    parser.add_argument("--client-id", required=True, help="OAuth2 Client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth2 Client Secret")
    parser.add_argument("--port", type=int, default=8080, help="Callback port")
    args = parser.parse_args()

    redirect_uri = f"http://127.0.0.1:{args.port}/callback"
    auth_params = {
        "client_id": args.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "tasks:read tasks:write",
        "state": "mcp_auth",
    }
    auth_url = f"https://ticktick.com/oauth/authorize?{urlencode(auth_params)}"

    print("\n" + "=" * 50)
    print("TickTick OAuth2 Authentication")
    print("=" * 50)
    print(f"\nOpening browser for authorization...")

    server = HTTPServer(("127.0.0.1", args.port), OAuthCallbackHandler)
    server.oauth_code = None
    server.timeout = 120

    webbrowser.open(auth_url)
    print(f"Waiting for callback on port {args.port}...")

    while server.oauth_code is None:
        server.handle_request()

    if not server.oauth_code:
        print("Error: No authorization code received")
        sys.exit(1)

    print("Exchanging code for tokens...")

    try:
        tokens = asyncio.run(exchange_code(
            args.client_id, args.client_secret,
            server.oauth_code, redirect_uri
        ))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save tokens
    token_path = Path.home() / ".ticktick-mcp" / "oauth_token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(tokens, f, indent=2)
    token_path.chmod(0o600)

    print(f"\nTokens saved to: {token_path}")
    print("=" * 50)
    print("Authentication complete!")
    print("=" * 50 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TickTick MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  (default)  Start the MCP server
  auth       Authenticate with TickTick OAuth2

Examples:
  ticktick-mcp                    # Start server
  ticktick-mcp auth --help        # Auth help
        """
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="server",
        choices=["server", "auth"],
        help="Command to run"
    )

    # Parse just the command
    args, remaining = parser.parse_known_args()

    if args.command == "auth":
        # Re-parse with auth arguments
        sys.argv = [sys.argv[0]] + remaining
        auth_command()
    else:
        # Start server
        from .server import main as server_main
        server_main()


if __name__ == "__main__":
    main()
