"""Testing commands for ContextVault CLI."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()

@click.group(name="test")
def test_group():
    """Testing and validation commands."""
    pass

@test_group.command()
def quick():
    """Run quick ContextVault test."""
    console.print("⚡ [bold blue]Quick ContextVault Test[/bold blue]")
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "quick_test.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("✅ [green]Quick test passed![/green]")
            console.print(result.stdout)
        else:
            console.print("❌ [red]Quick test failed![/red]")
            console.print(result.stderr)
            
    except Exception as e:
        console.print(f"❌ [red]Error running quick test: {e}[/red]")

@test_group.command()
def bulletproof():
    """Run comprehensive bulletproof test suite."""
    console.print("🛡️ [bold blue]Bulletproof Test Suite[/bold blue]")
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "bulletproof_test.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False)
        
        if result.returncode == 0:
            console.print("\n🎉 [bold green]All tests passed! ContextVault is bulletproof![/bold green]")
        else:
            console.print("\n❌ [red]Some tests failed. Check the output above.[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error running bulletproof test: {e}[/red]")

@test_group.command()
def validate():
    """Run system validation."""
    console.print("🔍 [bold blue]System Validation[/bold blue]")
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "validate_system.py"
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], capture_output=False)
        
        if result.returncode == 0:
            console.print("\n✅ [bold green]System validation passed![/bold green]")
        else:
            console.print("\n❌ [red]System validation failed. Check the output above.[/red]")
            
    except Exception as e:
        console.print(f"❌ [red]Error running validation: {e}[/red]")

@test_group.command()
@click.option('--count', default=5, help='Number of requests to send')
def performance(count: int):
    """Run performance test."""
    console.print(f"⚡ [bold blue]Performance Test ({count} requests)[/bold blue]")
    
    import requests
    import time
    
    test_queries = [
        "What programming languages do I like?",
        "What pets do I have?",
        "What car do I drive?",
        "Tell me about my preferences",
        "What do I do for work?"
    ]
    
    successful_requests = 0
    total_time = 0
    
    for i in range(count):
        query = test_queries[i % len(test_queries)]
        
        payload = {
            "model": "mistral:latest",
            "prompt": query,
            "stream": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:11435/api/generate",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                successful_requests += 1
                request_time = end_time - start_time
                total_time += request_time
                console.print(f"✅ Request {i+1}: {request_time:.2f}s")
            else:
                console.print(f"❌ Request {i+1}: Failed ({response.status_code})")
                
        except Exception as e:
            console.print(f"❌ Request {i+1}: Error - {e}")
    
    if successful_requests > 0:
        success_rate = successful_requests / count
        avg_time = total_time / successful_requests
        
        console.print(f"\n📊 [bold]Performance Results:[/bold]")
        console.print(f"   Success Rate: {success_rate:.1%}")
        console.print(f"   Average Response Time: {avg_time:.2f}s")
        console.print(f"   Total Time: {total_time:.2f}s")
        
        if success_rate >= 0.8 and avg_time < 5:
            console.print("🎉 [bold green]Performance is excellent![/bold green]")
        elif success_rate >= 0.6:
            console.print("✅ [green]Performance is acceptable[/green]")
        else:
            console.print("⚠️ [yellow]Performance needs improvement[/yellow]")
    else:
        console.print("❌ [red]All requests failed[/red]")

# Alias for quick test
@test_group.command()
def run():
    """Run quick test (alias for 'quick')."""
    quick()
