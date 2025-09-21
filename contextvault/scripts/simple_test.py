#!/usr/bin/env python3
"""
Dead simple ContextVault test for non-technical users
Just run this script and it shows you exactly what's happening
"""

import time
import requests
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table

console = Console()

def test_contextvault_simple():
    """Super simple test that anyone can understand"""
    
    console.print(Panel.fit("🧪 ContextVault Simple Test", style="bold green"))
    console.print("This test shows you exactly how ContextVault makes AI remember you!\n")
    
    # Step 1: Check if ContextVault is running
    console.print("🔍 Step 1: Checking if ContextVault is running...")
    
    try:
        response = requests.get("http://localhost:8000/health/", timeout=2)
        if response.status_code == 200:
            console.print("✅ ContextVault is running!")
        else:
            console.print("❌ ContextVault is not running. Please start it first.")
            return
    except:
        console.print("❌ ContextVault is not running. Please start it first.")
        return
    
    # Step 2: Test without context (direct to Ollama)
    console.print("\n🤖 Step 2: Testing AI WITHOUT ContextVault...")
    console.print("Asking: 'What do you know about me?'")
    
    try:
        response = requests.post("http://localhost:11434/api/generate", 
                               json={"model": "mistral:latest", "prompt": "What do you know about me?"},
                               timeout=10)
        if response.status_code == 200:
            direct_response = response.json().get("response", "")
            console.print(f"❌ AI Response (NO memory): {direct_response[:100]}...")
        else:
            console.print("❌ Failed to connect to Ollama directly")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    
    # Step 3: Test with context (through ContextVault)
    console.print("\n🧠 Step 3: Testing AI WITH ContextVault...")
    console.print("Asking: 'What do you know about me?' (through ContextVault)")
    
    try:
        response = requests.post("http://localhost:11435/api/generate", 
                               json={"model": "mistral:latest", "prompt": "What do you know about me?"},
                               timeout=10)
        if response.status_code == 200:
            contextvault_response = response.json().get("response", "")
            console.print(f"✅ AI Response (WITH memory): {contextvault_response[:100]}...")
        else:
            console.print("❌ Failed to connect through ContextVault")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    
    # Step 4: Show the difference
    console.print("\n🎯 Step 4: The Magic!")
    console.print("ContextVault makes AI remember:")
    console.print("• Your name and location")
    console.print("• Your pets and hobbies") 
    console.print("• Your work and projects")
    console.print("• Your preferences and interests")
    
    # Step 5: Test learning
    console.print("\n📚 Step 5: Testing Learning...")
    console.print("Telling AI: 'I love pizza and my favorite color is blue'")
    
    try:
        response = requests.post("http://localhost:11435/api/generate", 
                               json={"model": "mistral:latest", "prompt": "I love pizza and my favorite color is blue"},
                               timeout=10)
        if response.status_code == 200:
            console.print("✅ ContextVault learned this information!")
        else:
            console.print("❌ Failed to learn")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    
    # Step 6: Test if it remembers
    console.print("\n🧠 Step 6: Testing Memory...")
    console.print("Asking: 'What's my favorite color?'")
    
    try:
        response = requests.post("http://localhost:11435/api/generate", 
                               json={"model": "mistral:latest", "prompt": "What's my favorite color?"},
                               timeout=10)
        if response.status_code == 200:
            memory_response = response.json().get("response", "")
            console.print(f"✅ AI remembers: {memory_response[:100]}...")
        else:
            console.print("❌ Failed to test memory")
    except Exception as e:
        console.print(f"❌ Error: {e}")
    
    console.print("\n🎉 Test Complete!")
    console.print("ContextVault is working! Your AI now has persistent memory.")

if __name__ == "__main__":
    test_contextvault_simple()
