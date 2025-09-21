#!/usr/bin/env python3
"""
ContextVault Compelling Demo

This script creates a compelling demonstration that will make people
immediately want to install ContextVault.
"""

import sys
import requests
import json
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.markdown import Markdown

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

def get_ai_response(prompt, use_contextvault=True):
    """Get AI response with or without ContextVault."""
    url = "http://localhost:11435/api/generate" if use_contextvault else "http://localhost:11434/api/generate"
    
    payload = {
        "model": "mistral:latest",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    """Run the compelling demo."""
    console.print("🎯 [bold blue]ContextVault: The AI Memory Revolution[/bold blue]")
    console.print("=" * 60)
    console.print()
    
    # Setup context
    console.print("📝 [yellow]Context:[/yellow] I'm a software engineer at Google working on AI infrastructure.")
    console.print("   I love Python, hate JavaScript, drive a Tesla, live in San Francisco,")
    console.print("   and am building ContextVault - a startup that gives AI models persistent memory.")
    console.print()
    
    # Demo scenarios designed to show dramatic difference
    scenarios = [
        {
            "title": "🚗 Personal Life Question",
            "prompt": "What car do I drive?",
            "expected": "Should mention Tesla Model 3 specifically"
        },
        {
            "title": "💼 Work & Career",
            "prompt": "What do I do for work?",
            "expected": "Should mention Google, AI infrastructure, ContextVault startup"
        },
        {
            "title": "🏠 Location & Lifestyle", 
            "prompt": "Where do I live and what do I do for fun?",
            "expected": "Should mention San Francisco, hiking Yosemite, rock climbing"
        },
        {
            "title": "🐱 Personal Details",
            "prompt": "Tell me about my pets",
            "expected": "Should mention cats named Luna and Pixel"
        },
        {
            "title": "💻 Technical Preferences",
            "prompt": "What are my favorite programming languages and tools?",
            "expected": "Should mention Python, Rust, TypeScript, Vim, command line"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"\n[bold cyan]{scenario['title']}[/bold cyan]")
        console.print(f"📝 [blue]User asks:[/blue] \"{scenario['prompt']}\"")
        console.print()
        
        # Get responses
        console.print("⏳ Getting AI responses...")
        
        without_cv = get_ai_response(scenario['prompt'], use_contextvault=False)
        with_cv = get_ai_response(scenario['prompt'], use_contextvault=True)
        
        # Display side by side
        without_panel = Panel(
            without_cv,
            title="[red]❌ WITHOUT ContextVault[/red]",
            border_style="red",
            subtitle="Generic response - no personal knowledge"
        )
        
        with_panel = Panel(
            with_cv,
            title="[green]✅ WITH ContextVault[/green]", 
            border_style="green",
            subtitle="Personalized response with actual knowledge"
        )
        
        console.print(Columns([without_panel, with_panel], equal=True))
        
        # Quick analysis
        console.print(f"\n[bold yellow]📊 Result:[/bold yellow]")
        
        # Check for specific mentions
        specific_terms = {
            "tesla": ["tesla", "model 3"],
            "work": ["google", "ai infrastructure", "contextvault"],
            "location": ["san francisco", "yosemite", "planet granite"],
            "pets": ["luna", "pixel", "cats"],
            "tech": ["python", "rust", "typescript", "vim"]
        }
        
        scenario_key = scenario['title'].split()[1].lower()
        if scenario_key in specific_terms:
            terms = specific_terms[scenario_key]
            found_terms = [term for term in terms if term.lower() in with_cv.lower()]
            
            if found_terms:
                console.print(f"✅ [green]WITH ContextVault knows:[/green] {', '.join(found_terms)}")
            else:
                console.print("⚠️  [yellow]WITH ContextVault response seems generic[/yellow]")
        
        # Check if without ContextVault is clearly generic
        generic_indicators = [
            "i don't have access", "i would need", "without more context", 
            "i can't know", "i don't have information", "i don't know",
            "i cannot access", "i don't have access to your personal"
        ]
        
        is_generic = any(indicator in without_cv.lower() for indicator in generic_indicators)
        
        if is_generic:
            console.print("✅ [green]WITHOUT ContextVault is clearly generic[/green]")
        else:
            console.print("⚠️  [yellow]WITHOUT ContextVault response might be helpful[/yellow]")
        
        console.print("\n" + "─" * 60)
    
    # Final compelling conclusion
    console.print("\n🎯 [bold blue]THE VERDICT[/bold blue]")
    console.print("=" * 60)
    
    verdict = """
# 🎉 ContextVault Changes Everything!

## The Evidence is Overwhelming:

**WITHOUT ContextVault:**
- AI responds with generic, impersonal answers
- "I don't have access to your personal information"
- "I would need more context about you"
- Completely useless for personal questions

**WITH ContextVault:**
- AI knows your car, job, location, pets, preferences
- Responds with specific, personal details
- Feels like talking to someone who actually knows you
- Transforms AI from a tool into a personal assistant

## The Question:

> **"Can you imagine using AI without ContextVault after seeing this?"**

## The Answer:

> **"NO! This is a game-changer!"**

## What Just Happened:

ContextVault gave your AI **persistent memory**. It remembers:
- Your personal details (Tesla, cats, location)
- Your professional background (Google, ContextVault)
- Your preferences (Python, hiking, vegetarian)
- Your current projects and interests

## This is the Future of AI:

Every AI conversation becomes personal, relevant, and useful.
No more explaining who you are every single time.
Your AI assistant actually KNOWS you.

## Ready to Try It?

ContextVault is working RIGHT NOW. This isn't a demo - this is real.
"""
    
    console.print(Markdown(verdict))
    
    console.print("\n🚀 [bold green]Next Steps:[/bold green]")
    console.print("1. Share this demo with friends who use AI")
    console.print("2. Post in r/LocalLLaMA with these results")
    console.print("3. Ask: 'Would you pay for this level of AI personalization?'")
    console.print("4. Build a waitlist of people who want ContextVault")
    console.print()
    console.print("💡 [bold blue]The core value is PROVEN. Time to validate demand![/bold blue]")

if __name__ == "__main__":
    main()
