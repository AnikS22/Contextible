#!/usr/bin/env python3
"""
Test Proxy Integration for Automatic Context Extraction
This script tests if the proxy is actually calling the learning methods
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.models.context import ContextEntry
from contextvault.database import get_db_context


def test_proxy_learning():
    """Test if the proxy is calling the learning methods."""
    print("🤖 Testing Proxy Learning Integration")
    print("=" * 60)
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ Proxy not running on port 11435")
            return False
    except:
        print("❌ Cannot connect to proxy on port 11435")
        return False
    
    print("✅ Proxy is running")
    
    # Get initial stats
    with get_db_context() as db:
        initial_count = db.query(ContextEntry).count()
        initial_auto = db.query(ContextEntry).filter(
            ContextEntry.entry_metadata.contains('auto_extracted')
        ).count()
    
    print(f"📊 Initial: {initial_count} total, {initial_auto} auto-extracted")
    
    # Send a conversation that should definitely trigger extraction
    test_prompt = "Hello! My name is Alice Johnson and I work as a software engineer at Google. I love Python programming and machine learning. I live in San Francisco, California."
    
    print(f"\n💬 Sending test conversation:")
    print(f"Prompt: {test_prompt}")
    
    try:
        response = requests.post(
            "http://localhost:11435/api/generate",
            headers={"Content-Type": "application/json"},
            json={
                "model": "mistral:latest",
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Conversation sent successfully")
            
            # Parse response
            response_data = response.json()
            ai_response = response_data.get("response", "")
            print(f"🤖 AI Response: {ai_response[:100]}...")
            
            # Wait for processing
            print("⏳ Waiting for context extraction...")
            time.sleep(5)
            
            # Check for new context
            with get_db_context() as db:
                final_count = db.query(ContextEntry).count()
                final_auto = db.query(ContextEntry).filter(
                    ContextEntry.entry_metadata.contains('auto_extracted')
                ).count()
            
            print(f"📊 Final: {final_count} total, {final_auto} auto-extracted")
            
            if final_auto > initial_auto:
                print(f"🎉 SUCCESS: {final_auto - initial_auto} new auto-extracted entries!")
                
                # Show the new entries
                with get_db_context() as db:
                    recent_entries = db.query(ContextEntry).filter(
                        ContextEntry.entry_metadata.contains('auto_extracted')
                    ).order_by(ContextEntry.created_at.desc()).limit(3).all()
                
                print("📝 New auto-extracted entries:")
                for entry in recent_entries:
                    print(f"  - {entry.content}")
                    print(f"    Type: {entry.context_type}, Source: {entry.source}")
                    if entry.entry_metadata:
                        print(f"    Metadata: {entry.entry_metadata}")
                    print()
                
                return True
            else:
                print("⚠️ No new auto-extracted context found")
                
                # Check if any new context was added at all
                if final_count > initial_count:
                    print(f"ℹ️ {final_count - initial_count} new context entries added, but not auto-extracted")
                
                return False
        else:
            print(f"❌ Conversation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_conversation_logs():
    """Check if conversations are being logged."""
    print("\n📝 Checking Conversation Logs")
    print("=" * 60)
    
    try:
        # Check if conversation database exists
        conversation_db = Path("./conversations.db")
        if conversation_db.exists():
            print("✅ Conversation database exists")
            
            # Try to read some stats
            import sqlite3
            conn = sqlite3.connect(conversation_db)
            cursor = conn.cursor()
            
            # Count conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conv_count = cursor.fetchone()[0]
            
            # Count messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            msg_count = cursor.fetchone()[0]
            
            print(f"📊 Conversations: {conv_count}, Messages: {msg_count}")
            
            # Show recent conversations
            cursor.execute("SELECT id, model_id, start_time FROM conversations ORDER BY start_time DESC LIMIT 3")
            recent_convs = cursor.fetchall()
            
            if recent_convs:
                print("📋 Recent conversations:")
                for conv_id, model_id, start_time in recent_convs:
                    print(f"  - {conv_id}: {model_id} at {time.ctime(start_time)}")
            
            conn.close()
            
        else:
            print("❌ Conversation database does not exist")
            print("   This suggests the conversation logger is not working")
            
    except Exception as e:
        print(f"❌ Error checking conversation logs: {e}")


def test_direct_extraction():
    """Test context extraction directly."""
    print("\n🔍 Testing Direct Context Extraction")
    print("=" * 60)
    
    try:
        from contextvault.services.conversation_logger import conversation_logger
        from contextvault.services.context_extractor import context_extractor
        
        # Create a test conversation
        conversation_id = conversation_logger.start_conversation("test_model")
        
        # Log test messages
        user_msg = "Hi, my name is Bob and I'm a data scientist at Microsoft. I love working with Python and machine learning."
        assistant_msg = "Hello Bob! It's great to meet you. As a data scientist at Microsoft who loves Python, you must be working on some exciting projects."
        
        conversation_logger.log_user_message(conversation_id, user_msg)
        conversation_logger.log_assistant_message(conversation_id, assistant_msg)
        
        # Get conversation
        conversation = conversation_logger.get_conversation(conversation_id)
        
        if conversation:
            print(f"✅ Created test conversation with {len(conversation.messages)} messages")
            
            # Extract context
            extracted = context_extractor.extract_from_conversation(conversation_id, conversation)
            
            print(f"✅ Extracted {len(extracted)} context entries:")
            for i, context in enumerate(extracted, 1):
                print(f"  {i}. {context.content}")
                print(f"     Type: {context.context_type}, Confidence: {context.confidence}")
            
            return len(extracted) > 0
        else:
            print("❌ Failed to create test conversation")
            return False
            
    except Exception as e:
        print(f"❌ Direct extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("🧪 Proxy Integration Test Suite")
    print("Testing if automatic context extraction works through the proxy")
    print()
    
    # Test 1: Direct extraction (should work)
    direct_success = test_direct_extraction()
    
    # Test 2: Conversation logging (should work)
    check_conversation_logs()
    
    # Test 3: Proxy learning (might not work)
    proxy_success = test_proxy_learning()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Direct extraction: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"  Proxy learning: {'✅ PASS' if proxy_success else '❌ FAIL'}")
    
    if direct_success and proxy_success:
        print("\n🎉 All tests passed! Automatic context extraction is working!")
    elif direct_success and not proxy_success:
        print("\n⚠️ Direct extraction works but proxy integration has issues")
        print("   The context extraction system is working but not being called by the proxy")
    else:
        print("\n❌ Context extraction system has issues")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
