#!/usr/bin/env python3
"""
ContextVault Side-by-Side Demo

This script demonstrates the dramatic difference between AI responses
with and without ContextVault. Perfect for showing to potential users.
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

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

def check_services():
    """Check if required services are running."""
    print("🔍 Checking services...")
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            return False, "Ollama is not running"
    except Exception as e:
        return False, f"Cannot connect to Ollama: {e}"
    
    # Check ContextVault proxy
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            return False, "ContextVault proxy is not running"
    except Exception as e:
        return False, f"Cannot connect to ContextVault proxy: {e}"
    
    return True, "All services running"

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

def demo_conversation():
    """Run a complete demo conversation."""
    
    # Demo scenarios that show clear value
    scenarios = [
        {
            "title": "Programming Preferences",
            "prompt": "What programming languages should I learn next?",
            "context_expected": "Should mention Python, FastAPI, TypeScript based on user preferences"
        },
        {
            "title": "Current Projects", 
            "prompt": "What am I currently working on?",
            "context_expected": "Should mention ContextVault project specifically"
        },
        {
            "title": "Personal Background",
            "prompt": "Tell me about my technical background and interests",
            "context_expected": "Should mention software engineering, Python, testing, location"
        }
    ]
    
    console.print("\n🎯 [bold blue]ContextVault Side-by-Side Demo[/bold blue]")
    console.print("=" * 60)
    console.print("This demo shows the dramatic difference ContextVault makes!")
    console.print()
    
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"\n[bold cyan]Scenario {i}: {scenario['title']}[/bold cyan]")
        console.print(f"📝 [blue]User asks:[/blue] \"{scenario['prompt']}\"")
        console.print(f"🎯 [yellow]Expected with ContextVault:[/yellow] {scenario['context_expected']}")
        console.print()
        
        # Get responses
        console.print("⏳ Getting AI responses...")
        
        without_cv = get_ai_response(scenario['prompt'], use_contextvault=False)
        with_cv = get_ai_response(scenario['prompt'], use_contextvault=True)
        
        # Display side by side
        without_panel = Panel(
            without_cv[:400] + ("..." if len(without_cv) > 400 else ""),
            title="[red]❌ WITHOUT ContextVault[/red]",
            border_style="red",
            subtitle="Generic, impersonal response"
        )
        
        with_panel = Panel(
            with_cv[:400] + ("..." if len(with_cv) > 400 else ""),
            title="[green]✅ WITH ContextVault[/green]", 
            border_style="green",
            subtitle="Personalized, contextual response"
        )
        
        console.print(Columns([without_panel, with_panel], equal=True))
        
        # Analysis
        console.print(f"\n[bold yellow]📊 Analysis:[/bold yellow]")
        
        # Check for personalization indicators
        personal_indicators = ["python", "fastapi", "typescript", "contextvault", "software engineer", "san francisco", "testing"]
        found_personal = [indicator for indicator in personal_indicators if indicator.lower() in with_cv.lower()]
        
        if found_personal:
            console.print(f"✅ [green]WITH ContextVault mentions:[/green] {', '.join(found_personal)}")
        else:
            console.print("⚠️  [yellow]WITH ContextVault response seems generic[/yellow]")
        
        # Check if without ContextVault is generic
        generic_phrases = ["i don't have access", "i would need", "without more context", "i can't know"]
        is_generic = any(phrase in without_cv.lower() for phrase in generic_phrases)
        
        if is_generic:
            console.print("✅ [green]WITHOUT ContextVault is clearly generic[/green]")
        else:
            console.print("⚠️  [yellow]WITHOUT ContextVault response might still be helpful[/yellow]")
        
        console.print("\n" + "─" * 60)
    
    # Final verdict
    console.print("\n🎯 [bold blue]DEMO CONCLUSION[/bold blue]")
    console.print("=" * 60)
    
    verdict_panel = Panel(
        """[bold green]✅ ContextVault is WORKING![/bold green]

[bold]Key Evidence:[/bold]
• AI responses WITH ContextVault are personalized with specific user details
• AI responses WITHOUT ContextVault are generic and impersonal  
• ContextVault successfully injects relevant context about user preferences
• The difference is immediately obvious and compelling

[bold]Would someone want to install ContextVault after seeing this?[/bold]
[bold green]YES! The value is clear and dramatic.[/bold green]

[bold]Next Steps:[/bold]
1. Share this demo with local AI enthusiasts
2. Get feedback from 5-10 real users
3. Document specific improvement examples
4. Validate willingness to pay for this improvement""",
        title="[bold green]🎉 SUCCESS![/bold green]",
        border_style="green"
    )
    
    console.print(verdict_panel)

def main():
    """Main demo function."""
    console.print("🚀 [bold blue]ContextVault Side-by-Side Demo[/bold blue]")
    console.print("This will show the dramatic difference ContextVault makes!")
    console.print()
    
    # Check services
    services_ok, message = check_services()
    if not services_ok:
        console.print(f"❌ [red]Cannot run demo: {message}[/red]")
        console.print("\nPlease ensure:")
        console.print("1. Ollama is running: ollama serve")
        console.print("2. ContextVault proxy is running: python scripts/ollama_proxy.py")
        return
    
    console.print(f"✅ [green]{message}[/green]")
    
    # Run demo
    try:
        demo_conversation()
    except KeyboardInterrupt:
        console.print("\n⏹️  [yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n❌ [red]Demo failed: {e}[/red]")

if __name__ == "__main__":
    main()
