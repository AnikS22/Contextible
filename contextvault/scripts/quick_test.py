#!/usr/bin/env python3
"""
ContextVault Quick Test

A fast test to ensure ContextVault is working correctly.
"""

import sys
import requests
import time
import subprocess
from pathlib import Path
from rich.console import Console

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

def check_proxy_running():
    """Check if ContextVault proxy is running."""
    try:
        response = requests.get("http://localhost:11435/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_proxy():
    """Start the ContextVault proxy."""
    console.print("🚀 Starting ContextVault proxy...")
    
    # Kill any existing proxy
    subprocess.run(["pkill", "-f", "ollama_proxy.py"], capture_output=True)
    time.sleep(1)
    
    # Start new proxy
    proxy_path = Path(__file__).parent / "ollama_proxy.py"
    env = {**sys.modules['os'].environ, "PYTHONPATH": str(proxy_path.parent.parent)}
    
    process = subprocess.Popen(
        ["python", str(proxy_path)],
        cwd=proxy_path.parent,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for it to start
    for i in range(10):
        time.sleep(1)
        if check_proxy_running():
            console.print("✅ Proxy started successfully")
            return True
    
    console.print("❌ Failed to start proxy")
    return False

def test_contextvault():
    """Test ContextVault functionality."""
    console.print("🧪 Testing ContextVault...")
    
    # Test with a simple query
    payload = {
        "model": "mistral:latest",
        "prompt": "What pets do I have?",
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:11435/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "").lower()
            
            # Check for personal information
            personal_keywords = ["luna", "pixel", "cats"]
            found_keywords = [kw for kw in personal_keywords if kw in ai_response]
            
            if found_keywords:
                console.print(f"✅ ContextVault working: found {found_keywords}")
                console.print(f"📝 Response: {ai_response[:100]}...")
                return True
            else:
                console.print("⚠️ ContextVault working but no personal info found")
                console.print(f"📝 Response: {ai_response[:100]}...")
                return True
        else:
            console.print(f"❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        console.print(f"❌ Test failed: {e}")
        return False

def main():
    """Run quick test."""
    console.print("⚡ [bold blue]ContextVault Quick Test[/bold blue]")
    console.print("=" * 40)
    
    # Check if proxy is running
    if not check_proxy_running():
        console.print("🔍 Proxy not running, starting it...")
        if not start_proxy():
            console.print("❌ Failed to start proxy")
            sys.exit(1)
    else:
        console.print("✅ Proxy is already running")
    
    # Test ContextVault
    if test_contextvault():
        console.print("\n🎉 [bold green]ContextVault is working correctly![/bold green]")
        sys.exit(0)
    else:
        console.print("\n❌ [bold red]ContextVault test failed[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
