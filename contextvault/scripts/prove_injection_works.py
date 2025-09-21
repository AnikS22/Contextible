#!/usr/bin/env python3
"""
DEFINITIVE PROOF: Context Injection is Working
This script provides bulletproof evidence that ContextVault is successfully injecting context.
"""

import sys
import os
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.models.context import ContextEntry
from contextvault.database import get_db_context
from contextvault.services.injection_debugger import injection_debugger


def prove_context_injection_works():
    """Provide definitive proof that context injection is working."""
    print("🔬 DEFINITIVE PROOF: Context Injection Analysis")
    print("=" * 60)
    print()
    
    # Step 1: Check if ContextVault is running
    print("Step 1: Checking ContextVault Status")
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code == 200:
            print("✅ ContextVault proxy is running on port 11435")
        else:
            print(f"❌ ContextVault proxy not healthy: {response.status_code}")
            return False
    except:
        print("❌ ContextVault proxy not running")
        print("   Start with: python -m contextvault.main &")
        print("   Then: python scripts/ollama_proxy.py &")
        return False
    print()
    
    # Step 2: Check current context database
    print("Step 2: Analyzing Context Database")
    with get_db_context() as db:
        total_contexts = db.query(ContextEntry).count()
        auto_extracted = db.query(ContextEntry).filter(
            ContextEntry.entry_metadata.contains({'auto_extracted': True})
        ).count()
        manual_contexts = total_contexts - auto_extracted
        
    print(f"   Total context entries: {total_contexts}")
    print(f"   Auto-extracted entries: {auto_extracted}")
    print(f"   Manual entries: {manual_contexts}")
    print()
    
    # Step 3: Clear existing context for clean test
    print("Step 3: Setting up Clean Test Environment")
    with get_db_context() as db:
        # Keep only a few test contexts
        test_contexts = [
            "I am ProofTestUser, a software engineer at Google who specializes in Python and machine learning.",
            "I live in San Francisco and I love working with open source projects.",
            "My favorite programming language is Python and I prefer using VSCode as my editor."
        ]
        
        # Clear all context
        db.query(ContextEntry).delete()
        db.commit()
        
        # Add test contexts
        for i, content in enumerate(test_contexts):
            context_entry = ContextEntry(
                content=content,
                context_type="note",
                source="proof_test",
                tags=["proof_test", "test_user"],
                entry_metadata={"test_id": i, "proof_test": True}
            )
            db.add(context_entry)
        db.commit()
    
    print(f"   Added {len(test_contexts)} test context entries")
    print()
    
    # Step 4: Test WITHOUT context injection (direct to Ollama)
    print("Step 4: Testing WITHOUT Context Injection (Baseline)")
    try:
        # Direct request to Ollama (bypassing ContextVault)
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
            print("   Direct Ollama response (no context):")
            print(f"   [italic]{direct_ai_response[:200]}...[/italic]")
            
            # Analyze for generic indicators
            generic_indicators = ["i don't know", "i don't have", "i can't tell", "i'm not sure"]
            is_generic = any(indicator in direct_ai_response.lower() for indicator in generic_indicators)
            print(f"   Generic response: {'Yes' if is_generic else 'No'}")
        else:
            print(f"   ❌ Direct Ollama request failed: {direct_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Direct Ollama request error: {e}")
        return False
    print()
    
    # Step 5: Test WITH context injection (through ContextVault)
    print("Step 5: Testing WITH Context Injection (ContextVault)")
    try:
        # Request through ContextVault proxy
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
            print("   ContextVault proxy response (with context):")
            print(f"   [italic]{proxy_ai_response[:200]}...[/italic]")
            
            # Analyze for personalized indicators
            personal_indicators = ["prooftestuser", "software engineer", "google", "python", "san francisco", "vscode"]
            found_indicators = [indicator for indicator in personal_indicators if indicator in proxy_ai_response.lower()]
            personalization_score = len(found_indicators) / len(personal_indicators)
            
            print(f"   Found personal indicators: {found_indicators}")
            print(f"   Personalization score: {personalization_score:.1%}")
            
        else:
            print(f"   ❌ ContextVault proxy request failed: {proxy_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ContextVault proxy request error: {e}")
        return False
    print()
    
    # Step 6: Compare responses
    print("Step 6: Response Comparison Analysis")
    
    # Calculate improvement metrics
    direct_length = len(direct_ai_response)
    proxy_length = len(proxy_ai_response)
    length_change = proxy_length - direct_length
    
    # Check for specific test context mentions
    test_keywords = ["prooftestuser", "google", "python", "san francisco", "vscode"]
    direct_mentions = sum(1 for keyword in test_keywords if keyword in direct_ai_response.lower())
    proxy_mentions = sum(1 for keyword in test_keywords if keyword in proxy_ai_response.lower())
    
    print(f"   Response length change: {length_change:+d} characters")
    print(f"   Test keywords mentioned:")
    print(f"     Direct Ollama: {direct_mentions}/{len(test_keywords)}")
    print(f"     ContextVault:  {proxy_mentions}/{len(test_keywords)}")
    print(f"   Improvement: {proxy_mentions - direct_mentions:+d} more keywords mentioned")
    print()
    
    # Step 7: Final verdict
    print("Step 7: DEFINITIVE VERDICT")
    print("=" * 40)
    
    improvement_detected = proxy_mentions > direct_mentions
    significant_improvement = proxy_mentions >= 3  # At least 3 keywords mentioned
    context_injection_working = improvement_detected and significant_improvement
    
    if context_injection_working:
        print("🎉 PROOF: CONTEXT INJECTION IS WORKING!")
        print()
        print("Evidence:")
        print(f"   ✅ ContextVault mentioned {proxy_mentions} test keywords")
        print(f"   ✅ Direct Ollama mentioned only {direct_mentions} test keywords")
        print(f"   ✅ Improvement of {proxy_mentions - direct_mentions} keywords")
        print(f"   ✅ Response personalization score: {personalization_score:.1%}")
        print()
        print("Conclusion: ContextVault is successfully injecting context")
        print("           and the AI is using it to provide personalized responses!")
        
    else:
        print("❌ PROOF: CONTEXT INJECTION NOT WORKING PROPERLY")
        print()
        print("Evidence:")
        print(f"   ❌ Limited improvement detected")
        print(f"   ❌ ContextVault: {proxy_mentions} keywords vs Direct: {direct_mentions}")
        print(f"   ❌ Personalization score: {personalization_score:.1%}")
        print()
        print("Conclusion: Context injection needs investigation")
    
    print()
    print("=" * 60)
    return context_injection_working


def main():
    """Run the definitive proof test."""
    success = prove_context_injection_works()
    
    if success:
        print("\n🎯 FINAL RESULT: ContextVault is working as intended!")
        return 0
    else:
        print("\n⚠️  FINAL RESULT: Context injection needs debugging")
        return 1


if __name__ == "__main__":
    sys.exit(main())
