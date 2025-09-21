#!/usr/bin/env python3
"""
Simple Debug Test - Prove Context Injection is Working
This bypasses the complex debugging system and directly tests what matters.
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


def test_context_injection_directly():
    """Test context injection by comparing responses directly."""
    print("🔬 SIMPLE CONTEXT INJECTION TEST")
    print("=" * 50)
    
    # Step 1: Clear and add test context
    print("Step 1: Setting up test context...")
    with get_db_context() as db:
        # Clear all context
        db.query(ContextEntry).delete()
        db.commit()
        
        # Add specific test context
        test_context = ContextEntry(
            content="I am SimpleTestUser, a data scientist at Microsoft who loves Python and machine learning.",
            context_type="note",
            source="simple_test",
            tags=["test", "simple_test"],
            entry_metadata={"test_id": "simple_debug_test"}
        )
        db.add(test_context)
        db.commit()
    
    print("✅ Added test context: 'SimpleTestUser, data scientist at Microsoft'")
    
    # Step 2: Test direct Ollama (no context)
    print("\nStep 2: Testing direct Ollama (no context)...")
    try:
        direct_response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            json={
                "model": "mistral:latest",
                "prompt": "What do you know about me?",
                "stream": False
            },
            timeout=30
        )
        
        if direct_response.status_code == 200:
            direct_data = direct_response.json()
            direct_ai_response = direct_data.get("response", "")
            print(f"✅ Direct Ollama response received")
            print(f"Response: {direct_ai_response[:150]}...")
        else:
            print(f"❌ Direct Ollama failed: {direct_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Direct Ollama error: {e}")
        return False
    
    # Step 3: Test ContextVault proxy (with context)
    print("\nStep 3: Testing ContextVault proxy (with context)...")
    try:
        proxy_response = requests.post(
            "http://localhost:11435/api/generate",
            headers={"Content-Type": "application/json"},
            json={
                "model": "mistral:latest",
                "prompt": "What do you know about me?",
                "stream": False
            },
            timeout=30
        )
        
        if proxy_response.status_code == 200:
            proxy_data = proxy_response.json()
            proxy_ai_response = proxy_data.get("response", "")
            print(f"✅ ContextVault proxy response received")
            print(f"Response: {proxy_ai_response[:150]}...")
        else:
            print(f"❌ ContextVault proxy failed: {proxy_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ContextVault proxy error: {e}")
        return False
    
    # Step 4: Compare responses
    print("\nStep 4: Comparing responses...")
    
    # Look for test keywords in responses
    test_keywords = ["simpletestuser", "data scientist", "microsoft", "python", "machine learning"]
    
    direct_mentions = []
    proxy_mentions = []
    
    for keyword in test_keywords:
        if keyword in direct_ai_response.lower():
            direct_mentions.append(keyword)
        if keyword in proxy_ai_response.lower():
            proxy_mentions.append(keyword)
    
    print(f"Test keywords: {test_keywords}")
    print(f"Direct Ollama mentioned: {direct_mentions}")
    print(f"ContextVault mentioned: {proxy_mentions}")
    
    # Step 5: Verdict
    print("\nStep 5: VERDICT")
    print("=" * 30)
    
    improvement = len(proxy_mentions) - len(direct_mentions)
    
    if improvement > 0:
        print("🎉 CONTEXT INJECTION IS WORKING!")
        print(f"✅ ContextVault mentioned {len(proxy_mentions)} test keywords")
        print(f"✅ Direct Ollama mentioned {len(direct_mentions)} test keywords")
        print(f"✅ Improvement: +{improvement} keywords")
        print("\nPROOF: ContextVault is successfully injecting context!")
        return True
    else:
        print("❌ CONTEXT INJECTION NOT WORKING")
        print(f"❌ No improvement detected")
        print(f"❌ Direct: {len(direct_mentions)} keywords")
        print(f"❌ ContextVault: {len(proxy_mentions)} keywords")
        return False


def main():
    """Run the simple debug test."""
    print("🧪 Simple Context Injection Debug Test")
    print("This test bypasses complex debugging and directly proves context injection.")
    print()
    
    success = test_context_injection_directly()
    
    if success:
        print("\n🎯 RESULT: Context injection is working!")
        return 0
    else:
        print("\n⚠️ RESULT: Context injection is not working")
        return 1


if __name__ == "__main__":
    sys.exit(main())
