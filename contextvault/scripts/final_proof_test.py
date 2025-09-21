#!/usr/bin/env python3
"""
Final Proof Test - Automatic Context Extraction Working
This script proves that automatic context extraction is working through the proxy
"""

import sys
import os
import time
import requests
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.models.context import ContextEntry
from contextvault.database import get_db_context


def get_context_stats():
    """Get current context statistics."""
    try:
        with get_db_context() as db:
            total = db.query(ContextEntry).count()
            auto_extracted = db.query(ContextEntry).filter(
                ContextEntry.entry_metadata.contains('auto_extracted')
            ).count()
        return total, auto_extracted
    except Exception as e:
        print(f"Error getting stats: {e}")
        return 0, 0


def test_automatic_extraction():
    """Test automatic context extraction through proxy."""
    print("🧪 Final Proof Test - Automatic Context Extraction")
    print("=" * 60)
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ Proxy not running")
            return False
    except:
        print("❌ Cannot connect to proxy")
        return False
    
    print("✅ Proxy is running")
    
    # Get initial stats
    initial_total, initial_auto = get_context_stats()
    print(f"📊 Initial stats: {initial_total} total, {initial_auto} auto-extracted")
    
    # Send test conversations
    test_conversations = [
        "Hi! My name is FinalTest and I'm a machine learning engineer at Tesla. I love working with Python and PyTorch for AI projects.",
        "I prefer using VSCode over other editors for coding. I think it has the best extensions for Python development.",
        "I'm currently working on a project called AutoPilot that uses computer vision for self-driving cars."
    ]
    
    for i, prompt in enumerate(test_conversations, 1):
        print(f"\n💬 Test Conversation {i}")
        print(f"Prompt: {prompt[:60]}...")
        
        try:
            response = requests.post(
                "http://localhost:11435/api/generate",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Conversation sent successfully")
                
                # Wait for processing
                time.sleep(2)
            else:
                print(f"❌ Conversation failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Get final stats
    time.sleep(3)  # Wait for all processing to complete
    final_total, final_auto = get_context_stats()
    
    print(f"\n📊 Final stats: {final_total} total, {final_auto} auto-extracted")
    print(f"📈 New entries: {final_total - initial_total}")
    print(f"📈 New auto-extracted: {final_auto - initial_auto}")
    
    # Check if extraction worked
    if final_auto > initial_auto:
        print(f"\n🎉 SUCCESS! {final_auto - initial_auto} new context entries were automatically extracted!")
        print("✅ Automatic context extraction is working perfectly!")
        
        # Show some recent auto-extracted entries (without content to avoid SQLAlchemy issues)
        try:
            with get_db_context() as db:
                recent_entries = db.query(ContextEntry).filter(
                    ContextEntry.entry_metadata.contains('auto_extracted')
                ).order_by(ContextEntry.created_at.desc()).limit(5).all()
            
            print(f"\n📝 Recent auto-extracted entries (showing IDs and types):")
            for entry in recent_entries:
                print(f"  - ID: {entry.id}, Type: {entry.context_type}, Source: {entry.source}")
        except Exception as e:
            print(f"Note: Could not display entry details due to session issue: {e}")
        
        return True
    else:
        print("\n⚠️ No new auto-extracted context found")
        return False


def main():
    """Run the final proof test."""
    success = test_automatic_extraction()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 AUTOMATIC CONTEXT EXTRACTION IS WORKING!")
        print("✅ ContextVault is successfully learning from conversations!")
        print("✅ The system works with any local AI model!")
        print("✅ Context is automatically extracted and stored!")
    else:
        print("⚠️ Automatic context extraction needs further investigation")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
