#!/usr/bin/env python3
"""
Test Connection Script

Verifies that the TickTick MCP server can connect to the TickTick API.

Usage:
    python scripts/test_connection.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ticktick_mcp.api.client import TickTickClient
    from ticktick_mcp.services import AuthService, ProjectService, TaskService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install the package: pip install -e .")
    sys.exit(1)


async def test_oauth_connection(client: TickTickClient) -> bool:
    """Test OAuth2 (v1 API) connection."""
    print("\n--- Testing OAuth2 (v1 API) Connection ---")

    token_path = Path.home() / ".ticktick-mcp" / "oauth_token.json"
    if not token_path.exists():
        print(f"  OAuth token not found at: {token_path}")
        print("  Run 'python scripts/get_token.py' to authenticate first.")
        return False

    try:
        with open(token_path) as f:
            token_data = json.load(f)

        # Set the token
        client._access_token = token_data.get("access_token")
        client._oauth_config = {"configured": True}

        # Try to list projects
        project_service = ProjectService(client)
        projects = await project_service.list()

        print(f"  Connection successful!")
        print(f"  Found {len(projects)} projects")

        if projects:
            print(f"  First project: {projects[0].name}")

        return True

    except Exception as e:
        print(f"  Error: {e}")
        return False


async def test_v2_connection(client: TickTickClient) -> bool:
    """Test v2 API connection (if session token exists)."""
    print("\n--- Testing v2 API Connection ---")

    token_path = Path.home() / ".ticktick-mcp" / "session_token.json"
    if not token_path.exists():
        print(f"  Session token not found at: {token_path}")
        print("  Use 'ticktick_login' to authenticate with username/password.")
        return False

    try:
        with open(token_path) as f:
            token_data = json.load(f)

        # Set the session token
        client._session_token = token_data.get("token")
        client._user_id = token_data.get("user_id")

        # Try to list tasks
        task_service = TaskService(client)
        tasks = await task_service.list(include_completed=False)

        print(f"  Connection successful!")
        print(f"  Found {len(tasks)} tasks")

        return True

    except Exception as e:
        print(f"  Error: {e}")
        return False


async def main():
    print("\n" + "=" * 60)
    print("TickTick MCP Connection Test")
    print("=" * 60)

    client = TickTickClient()

    oauth_ok = await test_oauth_connection(client)
    v2_ok = await test_v2_connection(client)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  OAuth2 (v1 API): {'✓ Connected' if oauth_ok else '✗ Not Connected'}")
    print(f"  v2 API:          {'✓ Connected' if v2_ok else '✗ Not Connected'}")

    if oauth_ok or v2_ok:
        print("\n  At least one API is connected. You can use the MCP server.")
    else:
        print("\n  No API connected. Please authenticate first.")
        print("  For OAuth2: python scripts/get_token.py --client-id XXX --client-secret XXX")
        print("  For v2 API: Use ticktick_login tool after starting the MCP server")

    print("=" * 60 + "\n")

    return oauth_ok or v2_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
