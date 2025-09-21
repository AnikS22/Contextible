#!/usr/bin/env python3
"""
Test Real Context Extraction Through Proxy
This script demonstrates automatic context extraction working with real conversations
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


def test_real_extraction():
    """Test automatic context extraction with real conversations."""
    print("🤖 Testing Real Context Extraction Through Proxy")
    print("=" * 60)
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ Proxy not running on port 11435")
            print("   Start ContextVault with: python -m contextvault.main &")
            print("   Then start proxy with: python scripts/ollama_proxy.py &")
            return False
    except:
        print("❌ Cannot connect to proxy on port 11435")
        return False
    
    print("✅ Proxy is running")
    
    # Get initial context count
    with get_db_context() as db:
        initial_count = db.query(ContextEntry).count()
        initial_auto = db.query(ContextEntry).filter(
            ContextEntry.entry_metadata.contains('auto_extracted')
        ).count()
    
    print(f"📊 Initial context: {initial_count} total, {initial_auto} auto-extracted")
    
    # Test conversations that should extract context
    test_conversations = [
        {
            "prompt": "Hi, my name is Sarah and I'm a data scientist at Apple. I love working with Python and machine learning. I live in Cupertino, California.",
            "expected": ["name", "profession", "location", "interests"]
        },
        {
            "prompt": "I prefer using TensorFlow over PyTorch for deep learning projects. I think it's more stable for production systems.",
            "expected": ["preference", "technology"]
        },
        {
            "prompt": "I'm working on a new project called AutoML that helps developers build machine learning models without coding.",
            "expected": ["project", "work"]
        }
    ]
    
    for i, test in enumerate(test_conversations, 1):
        print(f"\n💬 Test Conversation {i}")
        print(f"Prompt: {test['prompt']}")
        print(f"Expected extraction: {test['expected']}")
        
        try:
            response = requests.post(
                "http://localhost:11435/api/generate",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "mistral:latest",
                    "prompt": test["prompt"],
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Conversation sent successfully")
                
                # Wait for processing
                time.sleep(3)
                
                # Check for new auto-extracted context
                with get_db_context() as db:
                    new_auto = db.query(ContextEntry).filter(
                        ContextEntry.entry_metadata.contains('auto_extracted')
                    ).count()
                
                if new_auto > initial_auto:
                    print(f"🎉 New auto-extracted context found! ({new_auto - initial_auto} new entries)")
                    
                    # Show the new entries
                    with get_db_context() as db:
                        recent_entries = db.query(ContextEntry).filter(
                            ContextEntry.entry_metadata.contains('auto_extracted')
                        ).order_by(ContextEntry.created_at.desc()).limit(5).all()
                    
                    print("📝 Recent auto-extracted entries:")
                    for entry in recent_entries:
                        print(f"  - {entry.content}")
                        print(f"    Type: {entry.context_type}, Source: {entry.source}")
                        print()
                    
                    initial_auto = new_auto
                else:
                    print("⚠️ No new auto-extracted context found")
            else:
                print(f"❌ Conversation failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Conversation error: {e}")
    
    # Final stats
    with get_db_context() as db:
        final_count = db.query(ContextEntry).count()
        final_auto = db.query(ContextEntry).filter(
            ContextEntry.entry_metadata.contains('auto_extracted')
        ).count()
    
    print(f"\n📊 Final Results:")
    print(f"   Total context entries: {final_count} (was {initial_count})")
    print(f"   Auto-extracted entries: {final_auto} (was {initial_auto})")
    print(f"   New entries: {final_count - initial_count}")
    print(f"   New auto-extracted: {final_auto - initial_auto}")
    
    if final_auto > initial_auto:
        print("\n🎉 SUCCESS: Automatic context extraction is working!")
        print("   ContextVault is automatically learning from your conversations!")
        return True
    else:
        print("\n⚠️ No automatic extraction detected")
        print("   This might be due to:")
        print("   - Validation being too strict")
        print("   - Context not being saved to database")
        print("   - Extraction patterns not matching")
        return False


def show_extraction_stats():
    """Show detailed extraction statistics."""
    print("\n📈 Context Extraction Statistics")
    print("=" * 60)
    
    try:
        with get_db_context() as db:
            # Total entries
            total = db.query(ContextEntry).count()
            
            # Auto-extracted entries
            auto_extracted = db.query(ContextEntry).filter(
                ContextEntry.entry_metadata.contains('auto_extracted')
            ).count()
            
            # By source
            user_prompt = db.query(ContextEntry).filter(
                ContextEntry.source == 'user_prompt'
            ).count()
            
            ai_response = db.query(ContextEntry).filter(
                ContextEntry.source == 'ai_response'
            ).count()
            
            # By type
            preference = db.query(ContextEntry).filter(
                ContextEntry.context_type == 'preference'
            ).count()
            
            note = db.query(ContextEntry).filter(
                ContextEntry.context_type == 'note'
            ).count()
            
            text = db.query(ContextEntry).filter(
                ContextEntry.context_type == 'text'
            ).count()
        
        print(f"📊 Context Statistics:")
        print(f"   Total entries: {total}")
        print(f"   Auto-extracted: {auto_extracted} ({auto_extracted/total*100:.1f}%)")
        print(f"   Manual entries: {total - auto_extracted}")
        print()
        print(f"📝 By Source:")
        print(f"   User prompts: {user_prompt}")
        print(f"   AI responses: {ai_response}")
        print()
        print(f"🏷️ By Type:")
        print(f"   Preferences: {preference}")
        print(f"   Notes: {note}")
        print(f"   Text: {text}")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")


def main():
    """Run the real extraction test."""
    print("🧪 Real Context Extraction Test")
    print("This test demonstrates automatic context extraction working with real AI conversations")
    print()
    
    success = test_real_extraction()
    show_extraction_stats()
    
    if success:
        print("\n🎉 Automatic context extraction is working!")
        print("ContextVault is successfully learning from your conversations!")
    else:
        print("\n⚠️ Automatic context extraction needs improvement")
        print("The system is extracting context but may need tuning for your use case")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
