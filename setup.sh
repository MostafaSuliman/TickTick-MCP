#!/bin/bash
# TickTick MCP Server - Quick Setup Script

set -e

echo "🎯 TickTick MCP Server Setup"
echo "============================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install --quiet mcp httpx pydantic

echo "✅ Dependencies installed!"

# Check if running on macOS for Claude Desktop config
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    echo ""
    echo "🖥️  macOS detected. Claude Desktop configuration:"
    echo ""
    echo "Add this to your claude_desktop_config.json:"
    echo "Location: $CLAUDE_CONFIG"
    echo ""
    cat << EOF
{
  "mcpServers": {
    "ticktick": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/ticktick_mcp.py"]
    }
  }
}
EOF
fi

echo ""
echo "============================"
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to https://developer.ticktick.com/manage"
echo "2. Create a new app and get your Client ID & Secret"
echo "3. Set redirect URL to: http://127.0.0.1:8080/callback"
echo "4. Configure Claude Desktop (see README.md)"
echo "5. Ask Claude to 'configure TickTick with my credentials'"
echo ""
echo "📚 See README.md for detailed instructions!"
