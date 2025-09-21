"""Demo commands for ContextVault CLI."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()

@click.group(name="demo")
def demo_group():
    """Demo and showcase commands."""
    pass

@demo_group.command()
def bulletproof():
    """Run the bulletproof demo."""
    console.print("🛡️ [bold blue]ContextVault Bulletproof Demo[/bold blue]")
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "bulletproof_demo.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False)
        
        if result.returncode == 0:
            console.print("\n🎉 [bold green]Demo completed successfully![/bold green]")
        else:
            console.print("\n❌ [red]Demo had issues. Check the output above.[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error running demo: {e}[/red]")

@demo_group.command()
def compelling():
    """Run the compelling demo."""
    console.print("🎯 [bold blue]ContextVault Compelling Demo[/bold blue]")
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "compelling_demo.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False)
        
        if result.returncode == 0:
            console.print("\n🎉 [bold green]Demo completed successfully![/bold green]")
        else:
            console.print("\n❌ [red]Demo had issues. Check the output above.[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error running demo: {e}[/red]")

@demo_group.command()
def interactive():
    """Run interactive demo."""
    console.print("🎮 [bold blue]Interactive ContextVault Demo[/bold blue]")
    
    import requests
    
    # Check if ContextVault is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=2)
        if response.status_code != 200:
            console.print("❌ [red]ContextVault must be running first[/red]")
            console.print("   Run: python -m contextvault.cli start")
            return
    except:
        console.print("❌ [red]ContextVault must be running first[/red]")
        console.print("   Run: python -m contextvault.cli start")
        return
    
    console.print("✅ [green]ContextVault is running![/green]")
    console.print("\n🎯 [bold]Interactive Demo[/bold]")
    console.print("Ask ContextVault questions and see how it personalizes responses!")
    console.print("Type 'quit' to exit.\n")
    
    while True:
        try:
            prompt = click.prompt("You", type=str)
            
            if prompt.lower() in ['quit', 'exit', 'q']:
                console.print("👋 [yellow]Goodbye![/yellow]")
                break
            
            payload = {
                "model": "mistral:latest",
                "prompt": prompt,
                "stream": False
            }
            
            console.print("🤖 [blue]ContextVault:[/blue]", end=" ")
            
            response = requests.post(
                "http://localhost:11435/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                console.print(ai_response)
            else:
                console.print(f"❌ Error: {response.status_code}")
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n👋 [yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"❌ [red]Error: {e}[/red]")

@demo_group.command()
def compare():
    """Compare responses with and without ContextVault."""
    console.print("⚖️ [bold blue]ContextVault Comparison Demo[/bold blue]")
    
    import requests
    
    # Check services
    try:
        ollama_response = requests.get("http://localhost:11434/api/tags", timeout=2)
        contextvault_response = requests.get("http://localhost:11435/health", timeout=2)
        
        if ollama_response.status_code != 200:
            console.print("❌ [red]Ollama must be running[/red]")
            return
            
        if contextvault_response.status_code != 200:
            console.print("❌ [red]ContextVault must be running[/red]")
            console.print("   Run: python -m contextvault.cli start")
            return
            
    except Exception as e:
        console.print(f"❌ [red]Error checking services: {e}[/red]")
        return
    
    console.print("✅ [green]Both services are running![/green]")
    
    # Get user prompt
    prompt = click.prompt("Enter a question to compare responses", type=str)
    
    payload = {
        "model": "mistral:latest",
        "prompt": prompt,
        "stream": False
    }
    
    console.print("\n⏳ [blue]Getting responses...[/blue]")
    
    # Get response without ContextVault
    try:
        direct_response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if direct_response.status_code == 200:
            direct_text = direct_response.json().get("response", "").strip()
        else:
            direct_text = f"Error: {direct_response.status_code}"
    except Exception as e:
        direct_text = f"Error: {e}"
    
    # Get response with ContextVault
    try:
        contextvault_response = requests.post(
            "http://localhost:11435/api/generate",
            json=payload,
            timeout=30
        )
        
        if contextvault_response.status_code == 200:
            contextvault_text = contextvault_response.json().get("response", "").strip()
        else:
            contextvault_text = f"Error: {contextvault_response.status_code}"
    except Exception as e:
        contextvault_text = f"Error: {e}"
    
    # Display comparison
    from rich.panel import Panel
    from rich.columns import Columns
    
    direct_panel = Panel(
        direct_text,
        title="[red]❌ WITHOUT ContextVault[/red]",
        border_style="red",
        subtitle="Generic, impersonal response"
    )
    
    contextvault_panel = Panel(
        contextvault_text,
        title="[green]✅ WITH ContextVault[/green]",
        border_style="green",
        subtitle="Personalized, contextual response"
    )
    
    console.print(Columns([direct_panel, contextvault_panel], equal=True))
    
    console.print("\n🎯 [bold]Analysis:[/bold]")
    console.print("Compare the responses above. Notice how ContextVault provides")
    console.print("personalized, specific information while the direct response is generic.")

# Alias for bulletproof demo
@demo_group.command()
def run():
    """Run bulletproof demo (alias for 'bulletproof')."""
    bulletproof()
