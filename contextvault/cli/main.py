#!/usr/bin/env python3
"""ContextVault CLI - Command-line interface for ContextVault."""

import sys
import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.config import settings, validate_environment
from contextvault.database import check_database_connection, init_database

# Import commands using relative paths since we're running this directly
sys.path.insert(0, str(Path(__file__).parent))
from commands import context, permissions, templates

console = Console()


class ContextVaultCLI:
    """Main CLI class for ContextVault."""
    
    def __init__(self):
        self.console = console


# Create CLI group
@click.group(name="contextvault")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-file', type=click.Path(exists=True), help='Path to configuration file')
@click.pass_context
def cli(ctx, verbose, config_file):
    """
    ContextVault - Local-first context management for AI models.
    
    ContextVault gives your local AI models persistent memory while keeping
    you in complete control of your data.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store configuration
    ctx.obj['verbose'] = verbose
    ctx.obj['config_file'] = config_file
    
    # Setup logging level based on verbose flag
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize ContextVault database and configuration."""
    console.print("🚀 [bold blue]Initializing ContextVault...[/bold blue]")
    
    try:
        # Validate environment
        console.print("1. Validating environment...")
        env_status = validate_environment()
        
        if env_status["issues"]:
            console.print("❌ [bold red]Environment validation failed:[/bold red]")
            for issue in env_status["issues"]:
                console.print(f"   • {issue}")
            sys.exit(1)
        
        if env_status["warnings"]:
            console.print("⚠️  [yellow]Environment warnings:[/yellow]")
            for warning in env_status["warnings"]:
                console.print(f"   • {warning}")
        
        console.print("✅ Environment validation passed\n")
        
        # Check database connection
        console.print("2. Testing database connection...")
        if not check_database_connection():
            console.print("❌ [bold red]Cannot connect to database[/bold red]")
            console.print("   Check your DATABASE_URL configuration in .env")
            sys.exit(1)
        
        console.print("✅ Database connection successful\n")
        
        # Initialize database
        console.print("3. Creating database tables...")
        init_database()
        console.print("✅ Database tables created\n")
        
        console.print("🎉 [bold green]ContextVault initialized successfully![/bold green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  • Start the API server: [cyan]contextvault serve[/cyan]")
        console.print("  • Add context: [cyan]contextvault context add 'Your first context'[/cyan]")
        console.print("  • Set permissions: [cyan]contextvault permissions add llama2 --scope=preferences[/cyan]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Initialization failed:[/bold red] {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--host', default=None, help='Host to bind to')
@click.option('--port', default=None, type=int, help='Port to bind to')
@click.option('--workers', default=None, type=int, help='Number of worker processes')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.pass_context
def serve(ctx, host, port, workers, reload):
    """Start the ContextVault API server."""
    console.print("🌐 [bold blue]Starting ContextVault API server...[/bold blue]")
    
    # Use provided values or fall back to settings
    host = host or settings.api_host
    port = port or settings.api_port
    workers = workers or settings.api_workers
    
    try:
        # Check database connection
        if not check_database_connection():
            console.print("❌ [bold red]Cannot connect to database[/bold red]")
            console.print("   Run: [cyan]contextvault init[/cyan]")
            sys.exit(1)
        
        console.print(f"📡 Starting server at [cyan]http://{host}:{port}[/cyan]")
        console.print(f"📚 API docs at [cyan]http://{host}:{port}/docs[/cyan]")
        console.print("Press Ctrl+C to stop\n")
        
        # Import and run uvicorn
        import uvicorn
        uvicorn.run(
            "contextvault.main:app",
            host=host,
            port=port,
            workers=workers if not reload else 1,
            reload=reload,
            log_level=settings.log_level.lower(),
            access_log=True,
        )
        
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]ContextVault server stopped[/yellow]")
    except Exception as e:
        console.print(f"❌ [bold red]Server failed to start:[/bold red] {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--host', default=None, help='Host to bind to')
@click.option('--port', default=None, type=int, help='Port to bind to')
@click.pass_context
def proxy(ctx, host, port):
    """Start the Ollama proxy server with context injection."""
    console.print("🔗 [bold blue]Starting ContextVault Ollama Proxy...[/bold blue]")
    
    # Use provided values or fall back to settings
    host = host or settings.api_host
    port = port or settings.proxy_port
    
    try:
        # Check database connection
        if not check_database_connection():
            console.print("❌ [bold red]Cannot connect to database[/bold red]")
            console.print("   Run: [cyan]contextvault init[/cyan]")
            sys.exit(1)
        
        console.print(f"🔗 Proxy server at [cyan]http://{host}:{port}[/cyan]")
        console.print(f"📡 Upstream Ollama at [cyan]http://{settings.ollama_host}:{settings.ollama_port}[/cyan]")
        console.print(f"📚 Proxy docs at [cyan]http://{host}:{port}/docs[/cyan]")
        console.print("Press Ctrl+C to stop\n")
        
        # Import and run the proxy
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from ollama_proxy import app
        import uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=settings.log_level.lower(),
            access_log=True,
        )
        
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]ContextVault proxy stopped[/yellow]")
    except Exception as e:
        console.print(f"❌ [bold red]Proxy failed to start:[/bold red] {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table', help='Output format')
def status(format):
    """Show ContextVault status and configuration."""
    try:
        # Check database connection
        db_healthy = check_database_connection()
        
        # Validate environment
        env_status = validate_environment()
        
        if format == 'json':
            import json
            status_data = {
                "database": {"healthy": db_healthy},
                "environment": env_status,
                "configuration": {
                    "api_host": settings.api_host,
                    "api_port": settings.api_port,
                    "proxy_port": settings.proxy_port,
                    "ollama_host": settings.ollama_host,
                    "ollama_port": settings.ollama_port,
                    "max_context_entries": settings.max_context_entries,
                    "max_context_length": settings.max_context_length,
                }
            }
            console.print(json.dumps(status_data, indent=2))
        else:
            # Table format
            console.print(Panel.fit("🏥 [bold]ContextVault Status[/bold]"))
            
            # Database status
            db_status = "✅ Healthy" if db_healthy else "❌ Unhealthy"
            console.print(f"Database: {db_status}")
            
            # Environment status
            env_emoji = "✅" if env_status["status"] == "healthy" else "❌"
            console.print(f"Environment: {env_emoji} {env_status['status'].title()}")
            
            if env_status["warnings"]:
                console.print("⚠️  [yellow]Warnings:[/yellow]")
                for warning in env_status["warnings"]:
                    console.print(f"   • {warning}")
            
            if env_status["issues"]:
                console.print("❌ [red]Issues:[/red]")
                for issue in env_status["issues"]:
                    console.print(f"   • {issue}")
            
            # Configuration table
            console.print("\n📋 [bold]Configuration[/bold]")
            config_table = Table(show_header=True, header_style="bold magenta")
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="green")
            
            config_table.add_row("API Host", f"{settings.api_host}:{settings.api_port}")
            config_table.add_row("Proxy Port", str(settings.proxy_port))
            config_table.add_row("Ollama", f"{settings.ollama_host}:{settings.ollama_port}")
            config_table.add_row("Max Context Entries", str(settings.max_context_entries))
            config_table.add_row("Max Context Length", str(settings.max_context_length))
            config_table.add_row("Log Level", settings.log_level)
            
            console.print(config_table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to get status:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file for export')
@click.option('--format', type=click.Choice(['json']), default='json', help='Export format')
def export(output, format):
    """Export all context data."""
    try:
        from contextvault.services import vault_service
        
        console.print("📤 [bold blue]Exporting context data...[/bold blue]")
        
        # Export data
        export_data = vault_service.export_context(format=format)
        
        # Determine output destination
        if output:
            output_path = Path(output)
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"contextvault_export_{timestamp}.{format}")
        
        # Write export file
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        total_entries = export_data["metadata"]["total_entries"]
        console.print(f"✅ Exported {total_entries} entries to [cyan]{output_path}[/cyan]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Export failed:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def import_data(file_path):
    """Import context data from file."""
    try:
        from contextvault.services import vault_service
        import json
        
        console.print(f"📥 [bold blue]Importing context data from {file_path}...[/bold blue]")
        
        # Read import file
        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        # Validate import data structure
        if "entries" not in import_data:
            console.print("❌ [bold red]Invalid import file format[/bold red]")
            sys.exit(1)
        
        entries = import_data["entries"]
        imported_count = 0
        
        # Import each entry
        for entry_data in entries:
            try:
                vault_service.save_context(
                    content=entry_data["content"],
                    context_type=entry_data.get("context_type", "text"),
                    source=entry_data.get("source"),
                    tags=entry_data.get("tags"),
                    metadata=entry_data.get("metadata"),
                    user_id=entry_data.get("user_id"),
                )
                imported_count += 1
            except Exception as e:
                console.print(f"⚠️  [yellow]Skipped entry:[/yellow] {e}")
        
        console.print(f"✅ Imported {imported_count}/{len(entries)} entries")
        
    except Exception as e:
        console.print(f"❌ [bold red]Import failed:[/bold red] {e}")
        sys.exit(1)


# Add command groups
cli.add_command(context.context_group)
cli.add_command(permissions.permissions_group)
cli.add_command(templates.templates)


if __name__ == "__main__":
    cli()
