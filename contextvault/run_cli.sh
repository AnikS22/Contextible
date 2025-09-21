#!/bin/bash

# ContextVault Enhanced CLI Runner
# This script makes it easy to run the ContextVault CLI from anywhere

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the contextvault directory
cd "$SCRIPT_DIR"

# Run the CLI
python -m contextvault.cli "$@"
