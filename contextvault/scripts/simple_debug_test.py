#!/usr/bin/env python3
"""
Simple debug test for context injection functionality.
This script tests the basic context injection pipeline.
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Add the parent directory to the path so we can import contextvault modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextvault.services.vault import VaultService
from contextvault.database import get_db_context
from contextvault.models import ContextEntry, ContextType

def test_context_injection():
    """Test basic context injection functionality."""
    print("🧪 Testing Context Injection Pipeline")
    print("=" * 50)
    
    try:
        # Test 1: Add some test context
        print("📝 Test 1: Adding test context...")
        test_context = "I am a software engineer who loves Python and AI. I work on machine learning projects and enjoy coding."
        
        with get_db_context() as db:
            context_entry = ContextEntry(
                content=test_context,
                context_type=ContextType.PERSONAL_INFO,
                source="test_script",
                metadata={"test": True, "timestamp": datetime.now().isoformat()}
            )
            db.add(context_entry)
            db.commit()
            context_id = context_entry.id
            print(f"✅ Added test context with ID: {context_id}")
        
        # Test 2: Retrieve context
        print("\n🔍 Test 2: Retrieving context...")
        with get_db_context() as db:
            retrieved = db.query(ContextEntry).filter(ContextEntry.id == context_id).first()
            if retrieved:
                print(f"✅ Successfully retrieved context: {retrieved.content[:50]}...")
            else:
                print("❌ Failed to retrieve context")
                return False
        
        # Test 3: Search context
        print("\n🔎 Test 3: Searching context...")
        with get_db_context() as db:
            vault_service_with_db = VaultService(db_session=db)
            results, total = vault_service_with_db.search_context("software engineer", limit=5)
            if results:
                print(f"✅ Found {len(results)} matching contexts")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result.content[:40]}...")
            else:
                print("❌ No contexts found in search")
                return False
        
        # Test 4: Test proxy connectivity (if running)
        print("\n🌐 Test 4: Testing proxy connectivity...")
        try:
            response = requests.get("http://localhost:11435/health", timeout=5)
            if response.status_code == 200:
                print("✅ Proxy is running and responding")
            else:
                print("⚠️  Proxy responded with non-200 status")
        except requests.exceptions.RequestException:
            print("⚠️  Proxy not running or not accessible")
            print("   To enable context injection, run: python scripts/ollama_proxy.py")
        
        # Test 5: Test Ollama connectivity
        print("\n🤖 Test 5: Testing Ollama connectivity...")
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if models:
                    print(f"✅ Ollama is running with {len(models)} models available")
                    for model in models[:3]:  # Show first 3 models
                        print(f"   • {model.get('name', 'Unknown')}")
                else:
                    print("⚠️  Ollama is running but no models found")
            else:
                print("❌ Ollama not responding properly")
        except requests.exceptions.RequestException:
            print("❌ Ollama not running")
            print("   Start Ollama with: ollama serve")
        
        print("\n🎉 Context injection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("ContextVault - Context Injection Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    success = test_context_injection()
    
    if success:
        print("\n✅ All tests passed! Context injection is working.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
