"""Model Management Commands for Contextible."""

import asyncio
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich import box

from ..services.model_detector import model_detector
from ..services.permissions import permission_service
from ..models.permissions import Permission


console = Console()


@click.group()
def models():
    """Manage AI models and their context injection settings."""
    pass


@models.command()
@click.option('--refresh', is_flag=True, help='Refresh model detection')
def list(refresh: bool):
    """List all detected AI models."""
    console.print("\n[bold blue]🔍 Detecting AI Models...[/bold blue]")
    
    if refresh:
        asyncio.run(model_detector.detect_all_models())
    
    models = list(model_detector.detected_models.values())
    
    if not models:
        console.print("[yellow]⚠️  No AI models detected[/yellow]")
        console.print("Make sure your AI services (Ollama, LM Studio, etc.) are running")
        return
    
    # Create models table
    table = Table(title="Detected AI Models", box=box.ROUNDED)
    table.add_column("Model Name", style="cyan", width=20)
    table.add_column("Provider", style="magenta", width=12)
    table.add_column("Endpoint", style="green", width=25)
    table.add_column("Status", style="yellow", width=10)
    table.add_column("Context Injection", style="blue", width=18)
    
    for model in models:
        status_icon = "🟢 Running" if model.status == "running" else "🔴 Stopped"
        injection_status = "✅ Enabled" if model.context_injection_enabled else "❌ Disabled"
        
        table.add_row(
            model.name,
            model.provider,
            model.endpoint,
            status_icon,
            injection_status
        )
    
    console.print(table)
    
    # Show summary
    summary = model_detector.get_models_summary()
    console.print(f"\n[bold]Summary:[/bold] {summary['total_models']} models detected, "
                  f"{summary['running_models']} running, "
                  f"{summary['injection_enabled']} with context injection enabled")


@models.command()
@click.argument('model_name')
@click.option('--enable', is_flag=True, help='Enable context injection')
@click.option('--disable', is_flag=True, help='Disable context injection')
def configure(model_name: str, enable: bool, disable: bool):
    """Configure context injection for a specific model."""
    
    # Find the model
    model = model_detector.get_model_status(model_name)
    if not model:
        console.print(f"[red]❌ Model '{model_name}' not found[/red]")
        console.print("Use 'contextible models list' to see available models")
        return
    
    console.print(f"\n[bold]Configuring model: {model.name}[/bold]")
    console.print(f"Provider: {model.provider}")
    console.print(f"Endpoint: {model.endpoint}")
    console.print(f"Current context injection: {'✅ Enabled' if model.context_injection_enabled else '❌ Disabled'}")
    
    if enable and disable:
        console.print("[red]❌ Cannot both enable and disable at the same time[/red]")
        return
    
    if enable:
        new_setting = True
        action = "enable"
    elif disable:
        new_setting = False
        action = "disable"
    else:
        # Interactive mode
        new_setting = Confirm.ask(
            f"{'Enable' if not model.context_injection_enabled else 'Disable'} context injection for {model.name}?"
        )
        action = "enable" if new_setting else "disable"
    
    # Update the setting
    success = model_detector.update_model_config(model_name, new_setting)
    
    if success:
        console.print(f"[green]✅ Context injection {action}d for {model.name}[/green]")
        
        # Update permissions in database
        _update_model_permissions(model_name, new_setting)
    else:
        console.print(f"[red]❌ Failed to {action} context injection for {model.name}[/red]")


@models.command()
@click.option('--auto-detect', is_flag=True, help='Auto-detect and configure all models')
def setup(auto_detect: bool):
    """Setup context injection for all detected models."""
    
    console.print("\n[bold blue]🚀 Setting up AI models...[/bold blue]")
    
    # Detect models
    models = asyncio.run(model_detector.detect_all_models())
    
    if not models:
        console.print("[yellow]⚠️  No AI models detected[/yellow]")
        return
    
    console.print(f"Found {len(models)} AI models:")
    
    # Show models and get user preferences
    for model in models:
        console.print(f"  • {model.name} ({model.provider}) - {model.endpoint}")
    
    if auto_detect:
        # Auto-enable for all models
        for model in models:
            model.context_injection_enabled = True
            _update_model_permissions(model.name, True)
        
        console.print("[green]✅ Auto-configured all models with context injection[/green]")
    else:
        # Interactive setup
        console.print("\n[bold]Configure context injection for each model:[/bold]")
        
        for model in models:
            enable = Confirm.ask(
                f"Enable context injection for {model.name}?",
                default=True
            )
            
            model.context_injection_enabled = enable
            _update_model_permissions(model.name, enable)
            
            status = "✅ Enabled" if enable else "❌ Disabled"
            console.print(f"  {model.name}: {status}")
    
    console.print("\n[bold green]🎉 Model setup complete![/bold green]")


@models.command()
@click.argument('model_name')
def permissions(model_name: str):
    """Show and manage permissions for a specific model."""
    
    model = model_detector.get_model_status(model_name)
    if not model:
        console.print(f"[red]❌ Model '{model_name}' not found[/red]")
        return
    
    console.print(f"\n[bold]Permissions for {model.name}[/bold]")
    
    try:
        # Get permissions from database
        with permission_service._get_session() as db:
            permissions = db.query(Permission).filter(
                Permission.model_id == model_name,
                Permission.is_active == True
            ).all()
        
        if not permissions:
            console.print("[yellow]No specific permissions configured[/yellow]")
            console.print("This model uses default permissions")
            return
        
        # Show permissions table
        table = Table(title=f"Permissions for {model.name}", box=box.ROUNDED)
        table.add_column("Permission ID", style="cyan", width=20)
        table.add_column("Scope", style="green", width=20)
        table.add_column("Allow All", style="yellow", width=10)
        table.add_column("Deny All", style="red", width=10)
        table.add_column("Active", style="blue", width=10)
        
        for perm in permissions:
            table.add_row(
                perm.id[:8] + "...",
                perm.scope or "default",
                "✅" if perm.allow_all else "❌",
                "✅" if perm.deny_all else "❌",
                "✅" if perm.is_active else "❌"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error fetching permissions: {e}[/red]")


@models.command()
def dashboard():
    """Open the interactive model dashboard."""
    console.print("\n[bold blue]📊 Model Dashboard[/bold blue]")
    console.print("Interactive dashboard coming soon!")
    
    # For now, show a summary
    summary = model_detector.get_models_summary()
    
    info_panel = Panel(
        f"""[bold]Total Models:[/bold] {summary['total_models']}
[bold]Running:[/bold] {summary['running_models']}
[bold]Context Injection Enabled:[/bold] {summary['injection_enabled']}

[bold]Providers:[/bold]
""".strip() + "\n".join([f"  • {provider}: {count}" for provider, count in summary['providers'].items()]),
        title="Model Summary",
        border_style="blue"
    )
    
    console.print(info_panel)


def _update_model_permissions(model_name: str, enable_context: bool):
    """Update model permissions in the database."""
    try:
        with permission_service._get_session() as db:
            # Check if permission already exists
            existing = db.query(Permission).filter(
                Permission.model_id == model_name,
                Permission.is_active == True
            ).first()
            
            if enable_context:
                if not existing:
                    # Create new permission
                    permission = Permission(
                        model_id=model_name,
                        scope="personal,work,preferences,notes",
                        allow_all=False,
                        deny_all=False,
                        is_active=True
                    )
                    db.add(permission)
                else:
                    # Update existing permission
                    existing.scope = "personal,work,preferences,notes"
                    existing.allow_all = False
                    existing.deny_all = False
            else:
                if existing:
                    # Disable the permission
                    existing.is_active = False
            
            db.commit()
            
    except Exception as e:
        console.print(f"[yellow]⚠️  Warning: Could not update permissions: {e}[/yellow]")


if __name__ == "__main__":
    models()
