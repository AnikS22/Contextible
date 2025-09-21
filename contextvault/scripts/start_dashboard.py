#!/usr/bin/env python3
"""
ContextVault Dashboard Server

Starts the web dashboard for ContextVault.
"""

import sys
import uvicorn
from pathlib import Path

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.dashboard.app import app

if __name__ == "__main__":
    print("🌐 Starting ContextVault Dashboard")
    print("   Dashboard: http://localhost:8080")
    print("   Proxy: http://localhost:11435")
    print("   Press CTRL+C to stop")
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info"
    )
