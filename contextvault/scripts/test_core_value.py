#!/usr/bin/env python3
"""
Test ContextVault Core Value Proposition

This script demonstrates the core value of ContextVault by showing
AI responses with and without context injection.
"""

import sys
import requests
import json
from pathlib import Path

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context
from contextvault.services.vault import VaultService
from contextvault.services.context_retrieval import ContextRetrievalService
from contextvault.models.context import ContextType


def setup_test_context():
    """Set up test context entries."""
    print("🔧 Setting up test context...")
    
    with get_db_context() as db:
        vault_service = VaultService(db_session=db)
        
        # Clear existing test entries
        from contextvault.models.context import ContextEntry
        existing_entries = db.query(ContextEntry).filter(
            ContextEntry.source == "test_setup"
        ).all()
        
        for entry in existing_entries:
            db.delete(entry)
        db.commit()
        
        # Add comprehensive test context
        test_contexts = [
            {
                "content": "I am a software engineer who loves Python and FastAPI for backend development. I prefer detailed explanations and want to understand how systems work.",
                "context_type": ContextType.PREFERENCE,
                "source": "test_setup",
                "tags": ["programming", "python", "fastapi", "backend", "engineering"]
            },
            {
                "content": "I am currently working on ContextVault, a system for giving AI models persistent memory. I love rigorous testing and debugging.",
                "context_type": ContextType.NOTE,
                "source": "test_setup", 
                "tags": ["project", "contextvault", "ai", "memory", "testing"]
            },
            {
                "content": "I prefer TypeScript over JavaScript for frontend development, and I use React with modern hooks and functional components.",
                "context_type": ContextType.PREFERENCE,
                "source": "test_setup",
                "tags": ["frontend", "typescript", "react", "javascript"]
            },
            {
                "content": "I live in San Francisco and work remotely. I enjoy hiking on weekends and learning about machine learning in my spare time.",
                "context_type": ContextType.NOTE,
                "source": "test_setup",
                "tags": ["personal", "location", "hobbies", "machine learning"]
            }
        ]
        
        for ctx_data in test_contexts:
            vault_service.save_context(
                content=ctx_data["content"],
                context_type=ctx_data["context_type"],
                source=ctx_data["source"],
                tags=ctx_data["tags"]
            )
        
        db.commit()
        print(f"✅ Added {len(test_contexts)} test context entries")


def test_context_retrieval():
    """Test if context retrieval is working."""
    print("\n🔍 Testing context retrieval...")
    
    test_queries = [
        "What programming languages should I learn next?",
        "What are my current programming preferences?",
        "What am I working on right now?",
        "Tell me about my hobbies and interests"
    ]
    
    with get_db_context() as db:
        retrieval_service = ContextRetrievalService(db_session=db)
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="mistral:latest",
                query_context=query,
                limit=3
            )
            
            print(f"   Found {len(entries)} relevant entries")
            for i, entry in enumerate(entries, 1):
                print(f"   {i}. [{entry.context_type}] {entry.content[:80]}...")
                if hasattr(entry, 'relevance_score'):
                    print(f"      Relevance score: {entry.relevance_score:.3f}")


def test_ai_responses():
    """Test AI responses with and without context."""
    print("\n🤖 Testing AI responses...")
    
    test_prompts = [
        "What programming languages should I learn next?",
        "What are my current programming preferences?",
        "What am I working on right now?"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"📝 Prompt: {prompt}")
        print('='*60)
        
        # Test without ContextVault (direct to Ollama)
        print("\n🔴 WITHOUT ContextVault (Direct to Ollama):")
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result.get('response', '')[:200]}...")
            else:
                print(f"   Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test with ContextVault (through proxy)
        print("\n🟢 WITH ContextVault (Through Proxy):")
        try:
            response = requests.post(
                "http://localhost:11435/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {result.get('response', '')[:200]}...")
            else:
                print(f"   Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")


def main():
    """Main test function."""
    print("🎯 ContextVault Core Value Test")
    print("="*50)
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama is not running. Please start Ollama first.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return
    
    # Check if ContextVault proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ ContextVault proxy is not running. Please start it first.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to ContextVault proxy: {e}")
        return
    
    print("✅ Both Ollama and ContextVault proxy are running")
    
    # Setup test context
    setup_test_context()
    
    # Test context retrieval
    test_context_retrieval()
    
    # Test AI responses
    test_ai_responses()
    
    print("\n" + "="*60)
    print("🎯 CORE VALUE TEST COMPLETE")
    print("="*60)
    print("\nKey Questions to Answer:")
    print("1. Are the 'WITH ContextVault' responses more personalized?")
    print("2. Do they mention specific details about the user?")
    print("3. Are they more relevant and helpful?")
    print("4. Would you want to use ContextVault after seeing this?")
    print("\nIf the answers aren't clearly YES, we need to fix the core system first!")


if __name__ == "__main__":
    main()
