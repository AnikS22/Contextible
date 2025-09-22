#!/usr/bin/env python3
"""
Seamless Ollama Integration Setup
This script implements Option 2: Port Interception
- Stops Ollama on port 11434 (default)
- Starts Ollama on port 11436 (alternative)
- Starts our proxy on port 11434 (Ollama's default)
- Ollama app connects to 11434 → gets context injection automatically
"""

import os
import sys
import time
import signal
import subprocess
import requests
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.config import settings

class OllamaManager:
    """Manages Ollama server lifecycle for seamless integration."""
    
    def __init__(self):
        self.ollama_process = None
        self.proxy_process = None
        self.original_port = 11434
        self.alternative_port = 11436
        self.proxy_port = 11435  # Our proxy port
        
    def is_ollama_running(self, port=11434):
        """Check if Ollama is running on a specific port."""
        try:
            response = requests.get(f"http://localhost:{port}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def stop_ollama(self, port=11434):
        """Stop Ollama server on a specific port."""
        print(f"🛑 Stopping Ollama on port {port}...")
        
        try:
            # Try graceful shutdown via API
            response = requests.post(f"http://localhost:{port}/api/generate", 
                                   json={"model": "dummy", "prompt": "shutdown"}, 
                                   timeout=2)
        except:
            pass
        
        # Kill any Ollama processes
        try:
            result = subprocess.run(['pkill', '-f', 'ollama'], capture_output=True)
            time.sleep(2)
            print(f"✅ Ollama stopped")
        except Exception as e:
            print(f"⚠️  Could not stop Ollama: {e}")
    
    def start_ollama_on_port(self, port):
        """Start Ollama server on a specific port."""
        print(f"🚀 Starting Ollama on port {port}...")
        
        # Set Ollama port via environment variable
        env = os.environ.copy()
        env['OLLAMA_HOST'] = f'0.0.0.0:{port}'
        
        try:
            # Start Ollama in background
            self.ollama_process = subprocess.Popen(
                ['ollama', 'serve'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Ollama to start
            for i in range(30):  # Wait up to 30 seconds
                if self.is_ollama_running(port):
                    print(f"✅ Ollama started on port {port}")
                    return True
                time.sleep(1)
            
            print(f"❌ Failed to start Ollama on port {port}")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Ollama: {e}")
            return False
    
    def start_proxy_on_port(self, port):
        """Start our proxy on a specific port."""
        print(f"🔗 Starting ContextVault proxy on port {port}...")
        
        # Update settings to use the specified port
        settings.proxy_port = port
        
        try:
            # Start proxy in background
            self.proxy_process = subprocess.Popen(
                [sys.executable, 'scripts/ollama_proxy.py'],
                cwd=Path(__file__).parent.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for proxy to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"http://localhost:{port}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ ContextVault proxy started on port {port}")
                        return True
                except:
                    pass
                time.sleep(1)
            
            print(f"❌ Failed to start proxy on port {port}")
            return False
            
        except Exception as e:
            print(f"❌ Error starting proxy: {e}")
            return False
    
    def setup_seamless_integration(self):
        """Set up seamless integration with port interception."""
        print("🔧 Setting up seamless Ollama integration...")
        print("=" * 60)
        
        # Step 1: Stop Ollama on default port
        if self.is_ollama_running(self.original_port):
            self.stop_ollama(self.original_port)
        
        # Step 2: Start Ollama on alternative port
        if not self.start_ollama_on_port(self.alternative_port):
            print("❌ Failed to start Ollama on alternative port")
            return False
        
        # Step 3: Start our proxy on Ollama's default port
        if not self.start_proxy_on_port(self.original_port):
            print("❌ Failed to start proxy on default port")
            return False
        
        print()
        print("🎉 Seamless integration setup complete!")
        print("=" * 60)
        print("📱 Ollama Dashboard:")
        print(f"   - Connect to: http://localhost:{self.original_port}")
        print(f"   - Models: http://localhost:{self.original_port}/api/tags")
        print("   - All requests now get context injection automatically!")
        print()
        print("🔧 Technical details:")
        print(f"   - Ollama Dashboard → localhost:{self.original_port} → Our Proxy → Real Ollama (port {self.alternative_port})")
        print(f"   - Context injection: ✅ Enabled")
        print(f"   - Transparency: ✅ Complete")
        print()
        print("💡 Usage:")
        print("   - Open Ollama Dashboard")
        print("   - Chat with any model")
        print("   - AI now knows you and remembers context!")
        print()
        
        return True
    
    def cleanup(self):
        """Clean up processes."""
        print("\n🧹 Cleaning up...")
        
        if self.ollama_process:
            self.ollama_process.terminate()
            self.ollama_process.wait()
        
        if self.proxy_process:
            self.proxy_process.terminate()
            self.proxy_process.wait()
        
        # Restart Ollama on original port
        print("🔄 Restarting Ollama on original port...")
        self.start_ollama_on_port(self.original_port)
        print("✅ Cleanup complete")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n🛑 Received interrupt signal...")
    manager.cleanup()
    sys.exit(0)

def main():
    """Main function."""
    global manager
    manager = OllamaManager()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Set up seamless integration
        if manager.setup_seamless_integration():
            print("🔄 Integration is running. Press Ctrl+C to stop...")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
        else:
            print("❌ Failed to set up seamless integration")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()
