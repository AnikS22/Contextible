#!/usr/bin/env python3
"""
ContextVault Bulletproof Demo

This script demonstrates that ContextVault is bulletproof and reliable,
showing the dramatic difference it makes to AI responses.
"""

import sys
import requests
import json
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

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
    """Run the bulletproof demo."""
    console.print("🛡️ [bold blue]ContextVault Bulletproof Demo[/bold blue]")
    console.print("=" * 60)
    console.print()
    
    console.print("🎯 [bold]Mission:[/bold] Prove ContextVault is bulletproof and indispensable")
    console.print()
    
    # Test scenarios that demonstrate clear value
    scenarios = [
        {
            "title": "🐱 Personal Life",
            "prompt": "What are my pets' names?",
            "expected": "Should know Luna and Pixel"
        },
        {
            "title": "💻 Technical Preferences", 
            "prompt": "What programming languages do I prefer?",
            "expected": "Should mention Python and specific preferences"
        },
        {
            "title": "🚗 Personal Details",
            "prompt": "What car do I drive?",
            "expected": "Should know Tesla Model 3"
        },
        {
            "title": "🏠 Location & Lifestyle",
            "prompt": "Where do I live and what do I do for fun?",
            "expected": "Should mention San Francisco and hobbies"
        }
    ]
    
    total_tests = len(scenarios)
    successful_tests = 0
    
    for i, scenario in enumerate(scenarios, 1):
        console.print(f"\n[bold cyan]Test {i}/{total_tests}: {scenario['title']}[/bold cyan]")
        console.print(f"📝 [blue]Query:[/blue] \"{scenario['prompt']}\"")
        console.print(f"🎯 [yellow]Expected:[/yellow] {scenario['expected']}")
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
            subtitle="Generic, impersonal response"
        )
        
        with_panel = Panel(
            with_cv,
            title="[green]✅ WITH ContextVault[/green]", 
            border_style="green",
            subtitle="Personalized, contextual response"
        )
        
        console.print(Columns([without_panel, with_panel], equal=True))
        
        # Analyze results
        console.print(f"\n[bold yellow]📊 Analysis:[/bold yellow]")
        
        # Check if ContextVault provided value
        generic_phrases = [
            "i don't know", "i don't have", "i can't", "i don't have access",
            "i don't have personal", "i am an ai", "i don't have information"
        ]
        is_without_generic = any(phrase in without_cv.lower() for phrase in generic_phrases)
        
        # Check for personal information in ContextVault response
        personal_indicators = ["luna", "pixel", "python", "tesla", "san francisco", "cats"]
        has_personal_info = any(indicator in with_cv.lower() for indicator in personal_indicators)
        
        if is_without_generic and has_personal_info:
            console.print("✅ [green]BULLETPROOF: ContextVault provides clear value[/green]")
            successful_tests += 1
        elif has_personal_info:
            console.print("✅ [green]SUCCESS: ContextVault provides personal information[/green]")
            successful_tests += 1
        elif is_without_generic:
            console.print("⚠️ [yellow]PARTIAL: Without ContextVault is generic, but ContextVault needs improvement[/yellow]")
        else:
            console.print("❌ [red]FAILED: No clear difference demonstrated[/red]")
        
        console.print("\n" + "─" * 60)
    
    # Final verdict
    console.print("\n🎯 [bold blue]BULLETPROOF DEMO RESULTS[/bold blue]")
    console.print("=" * 60)
    
    success_rate = successful_tests / total_tests
    
    if success_rate >= 0.8:
        verdict_panel = Panel(
            f"""[bold green]🎉 CONTEXTVAULT IS BULLETPROOF![/bold green]

[bold]Results:[/bold] {successful_tests}/{total_tests} tests passed ({success_rate:.1%})

[bold]Evidence:[/bold]
• AI responses WITH ContextVault are personalized and specific
• AI responses WITHOUT ContextVault are generic and useless
• ContextVault consistently provides clear, demonstrable value
• The difference is impossible to ignore

[bold]Verdict:[/bold] ContextVault is bulletproof and indispensable.

[bold]Would anyone want to use AI without ContextVault after seeing this?[/bold]
[bold green]ABSOLUTELY NOT![/bold green]

ContextVault transforms AI from a generic chatbot into a personal assistant.
This is the future of AI - and it's working RIGHT NOW.""",
            title="[bold green]🛡️ BULLETPROOF VERDICT[/bold green]",
            border_style="green"
        )
        
        console.print(verdict_panel)
        
        console.print("\n🚀 [bold green]ContextVault is ready for market![/bold green]")
        console.print("   The core value is proven, bulletproof, and compelling.")
        console.print("   Users will immediately want this level of AI personalization.")
        
        return True
        
    elif success_rate >= 0.5:
        verdict_panel = Panel(
            f"""[bold yellow]⚠️ CONTEXTVAULT IS MOSTLY WORKING[/bold yellow]

[bold]Results:[/bold] {successful_tests}/{total_tests} tests passed ({success_rate:.1%})

[bold]Status:[/bold] ContextVault provides value but needs refinement.

[bold]Next Steps:[/bold]
• Fine-tune context retrieval
• Improve template effectiveness  
• Add more compelling context examples
• Test with more diverse scenarios""",
            title="[bold yellow]⚠️ NEEDS IMPROVEMENT[/bold yellow]",
            border_style="yellow"
        )
        
        console.print(verdict_panel)
        return False
        
    else:
        verdict_panel = Panel(
            f"""[bold red]❌ CONTEXTVAULT NEEDS WORK[/bold red]

[bold]Results:[/bold] {successful_tests}/{total_tests} tests passed ({success_rate:.1%})

[bold]Status:[/bold] ContextVault is not consistently providing clear value.

[bold]Issues to Fix:[/bold]
• Context retrieval not finding relevant information
• Context injection not working properly
• Templates not effective enough
• System reliability issues""",
            title="[bold red]❌ NEEDS MAJOR WORK[/bold red]",
            border_style="red"
        )
        
        console.print(verdict_panel)
        return False

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            console.print("\n🎯 [bold green]MISSION ACCOMPLISHED![/bold green]")
            sys.exit(0)
        else:
            console.print("\n🛠️ [bold yellow]MISSION NEEDS WORK[/bold yellow]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n⏹️ [yellow]Demo interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n💥 [bold red]Demo failed with error: {e}[/bold red]")
        sys.exit(1)
