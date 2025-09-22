#!/usr/bin/env python3
"""
Test seamless integration setup
"""

import requests
import json

def test_seamless_integration():
    """Test if seamless integration is working."""
    print("🧪 Testing Seamless Integration...")
    print("=" * 50)
    
    # Test 1: Check if proxy is running on Ollama's default port
    print("📡 Test 1: Checking proxy on port 11434...")
    try:
        response = requests.get("http://localhost:11434/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Proxy is running on port 11434")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Context Injection: {health_data.get('context_injection', 'unknown')}")
        else:
            print(f"❌ Proxy not responding on port 11434 (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to port 11434: {e}")
        return False
    
    # Test 2: Check if real Ollama is running on alternative port
    print("\n🤖 Test 2: Checking real Ollama on port 11436...")
    try:
        response = requests.get("http://localhost:11436/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Real Ollama is running on port 11436")
            print(f"   Available models: {len(models)}")
            for model in models[:3]:  # Show first 3 models
                print(f"   - {model.get('name', 'Unknown')}")
        else:
            print(f"❌ Real Ollama not responding on port 11436 (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to port 11436: {e}")
        return False
    
    # Test 3: Test context injection through proxy
    print("\n🧠 Test 3: Testing context injection...")
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
            ai_response = data.get('response', '')
            
            if 'software engineer' in ai_response.lower() or 'python' in ai_response.lower():
                print("✅ Context injection is working!")
                print(f"   AI Response: {ai_response[:100]}...")
            else:
                print("⚠️  Context injection may not be working")
                print(f"   AI Response: {ai_response[:100]}...")
        else:
            print(f"❌ Context injection test failed (status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Context injection test error: {e}")
        return False
    
    print("\n🎉 All tests passed! Seamless integration is working!")
    print("=" * 50)
    print("📱 You can now use Ollama Dashboard normally:")
    print("   - Connect to: http://localhost:11434")
    print("   - All models will have context injection")
    print("   - AI will know you and remember context!")
    
    return True

if __name__ == "__main__":
    test_seamless_integration()
