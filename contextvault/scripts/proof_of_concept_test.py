#!/usr/bin/env python3
"""
Proof of Concept Test for ContextVault
This test demonstrates that ContextVault's core functionality works.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests


def test_context_injection():
    """Test that ContextVault actually injects context into AI responses."""
    
    print("🧪 CONTEXTVAULT PROOF OF CONCEPT TEST")
    print("=" * 50)
    
    # Step 1: Add a specific test context
    print("\n1. Adding test context...")
    try:
        response = requests.post(
            "http://localhost:8000/api/context/",
            json={
                "content": "I am Alice, a teacher who loves cats and lives in Portland. I prefer coffee over tea and I am learning Spanish.",
                "context_type": "personal_facts",
                "source": "proof_of_concept_test",
                "tags": ["test", "alice", "teacher", "cats", "portland", "coffee", "spanish"]
            }
        )
        
        if response.status_code == 200:
            print("   ✅ Test context added successfully")
        else:
            print(f"   ❌ Failed to add context: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error adding context: {e}")
        return False
    
    # Step 2: Test AI response without context (direct to Ollama)
    print("\n2. Testing AI response WITHOUT ContextVault (direct to Ollama)...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral:latest",
                "prompt": "What do you know about me?",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response_direct = data.get("response", "")
            print(f"   ✅ Direct Ollama response received")
            print(f"   Response preview: {ai_response_direct[:100]}...")
            
            # Check if response mentions Alice
            mentions_alice = "alice" in ai_response_direct.lower()
            print(f"   Mentions Alice: {'✅ YES' if mentions_alice else '❌ NO'}")
            
        else:
            print(f"   ❌ Direct Ollama request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error with direct Ollama request: {e}")
        return False
    
    # Step 3: Test AI response WITH context (through ContextVault proxy)
    print("\n3. Testing AI response WITH ContextVault (through proxy)...")
    try:
        response = requests.post(
            "http://localhost:11435/api/generate",
            json={
                "model": "mistral:latest",
                "prompt": "What do you know about me?",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response_context = data.get("response", "")
            print(f"   ✅ ContextVault proxy response received")
            print(f"   Response preview: {ai_response_context[:100]}...")
            
            # Check if response mentions Alice or other test context
            test_keywords = ["alice", "teacher", "cats", "portland", "coffee", "spanish"]
            mentions_context = any(keyword in ai_response_context.lower() for keyword in test_keywords)
            print(f"   Mentions test context: {'✅ YES' if mentions_context else '❌ NO'}")
            
            if mentions_context:
                print(f"   🎉 SUCCESS: ContextVault is working!")
                print(f"   The AI mentioned: {[kw for kw in test_keywords if kw in ai_response_context.lower()]}")
                return True
            else:
                print(f"   ❌ FAILED: AI didn't mention any test context")
                return False
            
        else:
            print(f"   ❌ ContextVault proxy request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error with ContextVault proxy request: {e}")
        return False


def main():
    """Run the proof of concept test."""
    
    print("This test will prove that ContextVault actually works by:")
    print("1. Adding specific test context about 'Alice'")
    print("2. Asking AI 'What do you know about me?' through ContextVault")
    print("3. Verifying AI mentions Alice's details")
    print()
    
    success = test_context_injection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PROOF OF CONCEPT: PASSED")
        print("✅ ContextVault's core functionality is working!")
        print("✅ AI responses are personalized with stored context!")
    else:
        print("❌ PROOF OF CONCEPT: FAILED")
        print("❌ ContextVault is not working as expected")
    print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
