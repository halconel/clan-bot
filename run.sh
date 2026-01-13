#!/usr/bin/env bash
# Convenience script to run commands with UV in PATH

set -e

# Add UV to PATH
export PATH="$HOME/snap/code/218/.local/share/../bin:$PATH"

# Check if UV is available
if ! command -v uv &> /dev/null; then
    echo "Error: UV not found in PATH"
    echo "Please install UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Run the command with uv
exec uv "$@"
