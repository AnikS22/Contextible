"""Diagnostic commands for ContextVault CLI."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group(name="diagnose")
def diagnose_group():
    """Diagnostic and troubleshooting commands."""
    pass

@diagnose_group.command()
def run():
    """Run comprehensive diagnostics."""
    console.print("🔍 [bold blue]ContextVault Diagnostics[/bold blue]")
    
    try:
        from contextvault.services.troubleshooting import get_troubleshooting_agent
        
        troubleshooter = get_troubleshooting_agent()
        diagnostics = troubleshooter.run_full_diagnostics()
        
        # Display overall health
        health = diagnostics.get("overall_health", "unknown")
        health_color = {
            "healthy": "green",
            "degraded": "yellow", 
            "unhealthy": "red"
        }.get(health, "white")
        
        console.print(f"\n🏥 [bold {health_color}]Overall Health: {health.upper()}[/bold {health_color}]")
        
        # Display component status
        components = diagnostics.get("components", {})
        
        table = Table(title="Component Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        for component_name, component_data in components.items():
            status = component_data.get("status", "unknown")
            details = component_data.get("details", {})
            
            status_icon = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌"
            }.get(status, "❓")
            
            # Format details
            detail_str = ", ".join([f"{k}: {v}" for k, v in details.items()])
            
            table.add_row(
                component_name.replace("_", " ").title(),
                f"{status_icon} {status.title()}",
                detail_str
            )
        
        console.print(table)
        
        # Display issues
        issues = diagnostics.get("issues", [])
        if issues:
            console.print("\n⚠️ [yellow]Issues Found:[/yellow]")
            for issue in issues:
                console.print(f"   • {issue}")
        
        # Display fixes applied
        fixes = diagnostics.get("fixes_applied", [])
        if fixes:
            console.print("\n🔧 [green]Auto-fixes Applied:[/green]")
            for fix in fixes:
                console.print(f"   • {fix}")
        
        # Recommendations
        if health == "unhealthy":
            console.print("\n🛠️ [red]Recommendations:[/red]")
            console.print("   1. Check that Ollama is running: ollama serve")
            console.print("   2. Verify ContextVault proxy: python -m contextvault.cli start")
            console.print("   3. Check database: python -m contextvault.cli context list")
            console.print("   4. Run auto-fix: python -m contextvault.cli fix")
        elif health == "degraded":
            console.print("\n⚠️ [yellow]Recommendations:[/yellow]")
            console.print("   1. Install sentence-transformers for better semantic search")
            console.print("   2. Add more context entries for better personalization")
            console.print("   3. Check permissions: python -m contextvault.cli permissions list")
        else:
            console.print("\n🎉 [green]System is healthy![/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Error running diagnostics: {e}[/red]")

@diagnose_group.command()
def fix():
    """Attempt to auto-fix common issues."""
    console.print("🔧 [bold blue]Auto-fixing ContextVault Issues[/bold blue]")
    
    try:
        from contextvault.services.troubleshooting import get_troubleshooting_agent
        
        troubleshooter = get_troubleshooting_agent()
        
        # Run diagnostics first
        console.print("🔍 Running diagnostics...")
        diagnostics = troubleshooter.run_full_diagnostics()
        
        # Apply fixes
        console.print("🔧 Applying auto-fixes...")
        fixes_applied = troubleshooter._apply_automatic_fixes(diagnostics)
        
        if fixes_applied:
            console.print("✅ [green]Auto-fixes applied:[/green]")
            for fix in fixes_applied:
                console.print(f"   • {fix}")
        else:
            console.print("ℹ️ [blue]No auto-fixes needed or available[/blue]")
        
        # Re-run diagnostics
        console.print("\n🔍 Re-running diagnostics...")
        new_diagnostics = troubleshooter.run_full_diagnostics()
        new_health = new_diagnostics.get("overall_health", "unknown")
        
        if new_health == "healthy":
            console.print("🎉 [bold green]All issues resolved![/bold green]")
        elif new_health == "degraded":
            console.print("⚠️ [yellow]Some issues remain but system is functional[/yellow]")
        else:
            console.print("❌ [red]Some issues could not be auto-fixed[/red]")
            console.print("   Manual intervention may be required")
        
    except Exception as e:
        console.print(f"❌ [red]Error during auto-fix: {e}[/red]")

@diagnose_group.command()
def ollama():
    """Check Ollama connectivity and status."""
    console.print("🤖 [bold blue]Ollama Diagnostics[/bold blue]")
    
    import requests
    
    try:
        # Check Ollama API
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            console.print("✅ [green]Ollama is running[/green]")
            
            models_data = response.json()
            models = models_data.get("models", [])
            
            if models:
                console.print(f"📦 [blue]Available models:[/blue]")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0)
                    size_gb = size / (1024**3) if size > 0 else 0
                    console.print(f"   • {name} ({size_gb:.1f} GB)")
            else:
                console.print("⚠️ [yellow]No models found[/yellow]")
                console.print("   Install a model: ollama pull mistral:latest")
        else:
            console.print(f"❌ [red]Ollama API error: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]Cannot connect to Ollama[/red]")
        console.print("   Make sure Ollama is running: ollama serve")
    except Exception as e:
        console.print(f"❌ [red]Ollama check failed: {e}[/red]")

@diagnose_group.command()
def database():
    """Check database status and integrity."""
    console.print("🗄️ [bold blue]Database Diagnostics[/bold blue]")
    
    try:
        from contextvault.database import get_db_context, engine
        from contextvault.models.context import ContextEntry
        from contextvault.models.permissions import Permission
        
        # Test connection
        with get_db_context() as db:
            # Check tables
            inspector = engine.inspect()
            tables = inspector.get_table_names()
            
            console.print(f"📋 [blue]Database tables:[/blue]")
            for table in tables:
                console.print(f"   • {table}")
            
            # Check context entries
            context_count = db.query(ContextEntry).count()
            console.print(f"\n📝 [blue]Context entries:[/blue] {context_count}")
            
            if context_count > 0:
                # Show recent entries
                recent_entries = db.query(ContextEntry).order_by(
                    ContextEntry.created_at.desc()
                ).limit(3).all()
                
                console.print("   Recent entries:")
                for entry in recent_entries:
                    preview = entry.content[:50] + "..." if len(entry.content) > 50 else entry.content
                    console.print(f"     • [{entry.context_type}] {preview}")
            
            # Check permissions
            permission_count = db.query(Permission).count()
            console.print(f"\n🔐 [blue]Permissions:[/blue] {permission_count}")
            
            if permission_count > 0:
                permissions = db.query(Permission).all()
                for perm in permissions:
                    scopes = perm.get_allowed_scopes()
                    console.print(f"   • {perm.model_id}: {', '.join(scopes)}")
            
            console.print("\n✅ [green]Database is healthy[/green]")
            
    except Exception as e:
        console.print(f"❌ [red]Database check failed: {e}[/red]")

@diagnose_group.command()
def proxy():
    """Check ContextVault proxy status."""
    console.print("🚀 [bold blue]Proxy Diagnostics[/bold blue]")
    
    import requests
    
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        
        if response.status_code == 200:
            console.print("✅ [green]ContextVault proxy is running[/green]")
            
            health_data = response.json()
            
            # Check components
            components = {
                "Proxy": health_data.get("proxy", {}).get("healthy", False),
                "Ollama": health_data.get("ollama", {}).get("status") == "healthy",
                "Database": health_data.get("database", {}).get("healthy", False),
                "Context Injection": health_data.get("context_injection") == "enabled"
            }
            
            console.print("\n📊 [blue]Component Status:[/blue]")
            for component, healthy in components.items():
                status = "✅ Healthy" if healthy else "❌ Failed"
                console.print(f"   • {component}: {status}")
            
            # Check uptime
            uptime = health_data.get("uptime", "Unknown")
            console.print(f"\n⏱️ [blue]Uptime:[/blue] {uptime}")
            
        else:
            console.print(f"❌ [red]Proxy health check failed: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Proxy check failed: {e}[/red]")

@diagnose_group.command()
def semantic():
    """Check semantic search status."""
    console.print("🧠 [bold blue]Semantic Search Diagnostics[/bold blue]")
    
    try:
        from contextvault.services.semantic_search import get_semantic_search_service
        
        semantic_service = get_semantic_search_service()
        
        if semantic_service.is_available():
            console.print("✅ [green]Semantic search is available[/green]")
            
            cache_stats = semantic_service.get_cache_stats()
            
            if cache_stats.get("fallback_mode"):
                console.print("⚠️ [yellow]Using TF-IDF fallback mode[/yellow]")
                console.print("   For better results, install: pip install sentence-transformers")
            else:
                console.print("✅ [green]Using sentence-transformers[/green]")
            
            console.print(f"\n📊 [blue]Cache Stats:[/blue]")
            for key, value in cache_stats.items():
                console.print(f"   • {key}: {value}")
                
        else:
            console.print("❌ [red]Semantic search not available[/red]")
            console.print("   Install dependencies: pip install sentence-transformers scikit-learn")
            
    except Exception as e:
        console.print(f"❌ [red]Semantic search check failed: {e}[/red]")
