#!/usr/bin/env python3
"""Test script to verify ContextVault conversation learning is working."""

import requests
import time
import json

def test_conversation_learning():
    """Test that ContextVault learns from conversations."""
    
    print("🧪 Testing ContextVault Conversation Learning")
    print("=" * 50)
    
    # Test 1: Check initial learning stats
    print("\n📊 Step 1: Check initial learning statistics")
    try:
        response = requests.get("http://localhost:8080/api/context/entries", 
                              params={"source": "user_prompt,ai_response", "limit": 100})
        if response.status_code == 200:
            initial_count = len(response.json().get("entries", []))
            print(f"✅ Initial learned entries: {initial_count}")
        else:
            print(f"❌ Failed to get initial stats: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting initial stats: {e}")
        return
    
    # Test 2: Send a conversation with personal information
    print("\n💬 Step 2: Send conversation with personal information")
    test_prompt = """Hi! I'm testing ContextVault. My name is Alex, I'm a data scientist at Microsoft, 
    I love playing guitar in my free time, I have a pet cat named Whiskers, and I'm currently 
    learning machine learning. I prefer working with Python and TensorFlow."""
    
    try:
        response = requests.post("http://localhost:11435/api/generate",
                               json={
                                   "model": "mistral:latest",
                                   "prompt": test_prompt
                               },
                               timeout=30)
        
        if response.status_code == 200:
            print("✅ Conversation sent successfully")
            # Extract the AI response
            ai_response = ""
            for line in response.text.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            ai_response += data['response']
                    except:
                        continue
            print(f"🤖 AI Response: {ai_response[:100]}...")
        else:
            print(f"❌ Failed to send conversation: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error sending conversation: {e}")
        return
    
    # Test 3: Wait a moment for learning to process
    print("\n⏳ Step 3: Wait for learning to process...")
    time.sleep(2)
    
    # Test 4: Check if new context was learned
    print("\n📈 Step 4: Check if new context was learned")
    try:
        response = requests.get("http://localhost:8080/api/context/entries", 
                              params={"source": "user_prompt,ai_response", "limit": 100})
        if response.status_code == 200:
            final_count = len(response.json().get("entries", []))
            learned_count = final_count - initial_count
            print(f"✅ Final learned entries: {final_count}")
            print(f"🎯 New entries learned: {learned_count}")
            
            if learned_count > 0:
                print("🎉 SUCCESS: ContextVault learned from the conversation!")
                
                # Show the newest entries
                entries = response.json().get("entries", [])
                print("\n📝 Latest learned entries:")
                for entry in entries[:learned_count]:
                    print(f"  • {entry.get('content', '')[:60]}...")
                    print(f"    Source: {entry.get('source')}, Type: {entry.get('context_type')}")
            else:
                print("⚠️  No new entries were learned from this conversation")
        else:
            print(f"❌ Failed to get final stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting final stats: {e}")

def test_learning_with_cli():
    """Test learning using CLI commands."""
    print("\n🔧 CLI Learning Test")
    print("=" * 30)
    
    import subprocess
    import sys
    
    try:
        # Get learning stats
        result = subprocess.run([
            sys.executable, "-m", "contextvault.cli", "learning", "stats"
        ], capture_output=True, text=True, cwd="/Users/aniksahai/Desktop/Contextive/contextvault")
        
        if result.returncode == 0:
            print("✅ CLI learning stats command works")
            print(result.stdout)
        else:
            print(f"❌ CLI command failed: {result.stderr}")
            
        # List learned context
        result = subprocess.run([
            sys.executable, "-m", "contextvault.cli", "learning", "list", "--limit", "3"
        ], capture_output=True, text=True, cwd="/Users/aniksahai/Desktop/Contextive/contextvault")
        
        if result.returncode == 0:
            print("✅ CLI learning list command works")
            print(result.stdout)
        else:
            print(f"❌ CLI list command failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing CLI: {e}")

if __name__ == "__main__":
    print("🚀 ContextVault Learning Verification Test")
    print("=" * 60)
    
    # Test 1: API-based learning test
    test_conversation_learning()
    
    # Test 2: CLI-based learning test
    test_learning_with_cli()
    
    print("\n" + "=" * 60)
    print("✅ Learning verification test completed!")
    print("\n📋 How to verify ContextVault is learning:")
    print("1. Check learning stats: python -m contextvault.cli learning stats")
    print("2. List learned context: python -m contextvault.cli learning list")
    print("3. Send conversations through port 11435")
    print("4. Watch the learned entries count increase")
    print("5. Use the web dashboard at http://localhost:8080")
