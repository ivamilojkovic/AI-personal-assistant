#!/bin/bash
# ==========================================
# Script to setup and run MCP server
# ==========================================

# Exit immediately if a command fails
set -e

# 1. Variables
REPO_URL="https://github.com/jeremyjordan/mcp-gmail.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR/mcp-gmail"

# 2. Clone repo if it doesn't exist
if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "Repository exists, pulling latest..."
    cd "$REPO_DIR"
    git pull
fi

# 3. Navigate to repo
cd "$REPO_DIR"

# 4. Copy credentials.json from script folder to repo root
CREDENTIALS_SRC="$SCRIPT_DIR/credentials.json"
CREDENTIALS_DEST="$REPO_DIR/credentials.json"

if [ ! -f "$CREDENTIALS_SRC" ]; then
    echo "ERROR: credentials.json not found in script folder!"
    exit 1
fi

echo "Copying credentials.json to repository root..."
cp "$CREDENTIALS_SRC" "$CREDENTIALS_DEST"

# 5. Sync dependencies
echo "Running: uv sync"
uv sync

# 6. Run test_gmail_setup.py
echo "Running: uv run python scripts/test_gmail_setup.py"
if ! uv run python scripts/test_gmail_setup.py; then
    echo "Test failed. Check your setup."
    exit 1
fi

# 7. Start MCP server
echo "Starting MCP server..."
uv run mcp dev mcp_gmail/server.py 