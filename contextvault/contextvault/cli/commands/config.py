"""Configuration management commands for ContextVault CLI."""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

@click.group(name="config")
def config_group():
    """Configuration management commands."""
    pass

@config_group.command()
def show():
    """Show current configuration."""
    console.print("⚙️ [bold blue]ContextVault Configuration[/bold blue]")
    console.print("=" * 40)
    
    config_file = Path.home() / ".contextvault" / "config.yaml"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Display configuration in a nice format
            table = Table(title="Current Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")
            
            def add_config_section(section: Dict[str, Any], prefix: str = ""):
                for key, value in section.items():
                    if isinstance(value, dict):
                        add_config_section(value, f"{prefix}{key}.")
                    else:
                        table.add_row(f"{prefix}{key}", str(value))
            
            add_config_section(config)
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ [red]Error reading configuration: {e}[/red]")
    else:
        console.print("⚠️ [yellow]No configuration file found[/yellow]")
        console.print(f"   Expected location: {config_file}")
        console.print("   Run 'python -m contextvault.cli config init' to create one")

@config_group.command()
def init():
    """Initialize configuration file with defaults."""
    console.print("🔧 [bold blue]Initializing ContextVault Configuration[/bold blue]")
    
    config_dir = Path.home() / ".contextvault"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.yaml"
    
    default_config = {
        "server": {
            "host": "127.0.0.1",
            "port": 11435,
            "debug": False
        },
        "ollama": {
            "host": "127.0.0.1",
            "port": 11434
        },
        "database": {
            "url": "sqlite:///contextvault.db",
            "echo": False
        },
        "semantic_search": {
            "model": "all-MiniLM-L6-v2",
            "fallback_threshold": 0.15,
            "max_results": 50
        },
        "context": {
            "max_length": 2000,
            "max_entries": 10,
            "default_template": "direct_instruction"
        },
        "logging": {
            "level": "INFO",
            "file": "contextvault.log"
        }
    }
    
    try:
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        console.print(f"✅ [green]Configuration initialized[/green]")
        console.print(f"   Location: {config_file}")
        console.print("   Edit the file to customize settings")
        
    except Exception as e:
        console.print(f"❌ [red]Error creating configuration: {e}[/red]")

@config_group.command()
@click.argument('key')
@click.argument('value')
def set(key: str, value: str):
    """Set a configuration value."""
    console.print(f"🔧 [bold blue]Setting {key} = {value}[/bold blue]")
    
    config_dir = Path.home() / ".contextvault"
    config_file = config_dir / "config.yaml"
    
    if not config_file.exists():
        console.print("❌ [red]No configuration file found[/red]")
        console.print("   Run 'python -m contextvault.cli config init' first")
        return
    
    try:
        # Load current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Parse key path (e.g., "server.port")
        keys = key.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value (convert string to appropriate type)
        target_key = keys[-1]
        
        # Try to convert value to appropriate type
        if value.lower() in ('true', 'false'):
            current[target_key] = value.lower() == 'true'
        elif value.isdigit():
            current[target_key] = int(value)
        elif value.replace('.', '').isdigit():
            current[target_key] = float(value)
        else:
            current[target_key] = value
        
        # Save updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        console.print(f"✅ [green]Configuration updated[/green]")
        console.print(f"   {key} = {current[target_key]}")
        
    except Exception as e:
        console.print(f"❌ [red]Error updating configuration: {e}[/red]")

@config_group.command()
@click.argument('key')
def get(key: str):
    """Get a configuration value."""
    config_dir = Path.home() / ".contextvault"
    config_file = config_dir / "config.yaml"
    
    if not config_file.exists():
        console.print("❌ [red]No configuration file found[/red]")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Parse key path
        keys = key.split('.')
        current = config
        
        for k in keys:
            if k not in current:
                console.print(f"❌ [red]Configuration key '{key}' not found[/red]")
                return
            current = current[k]
        
        console.print(f"{key} = {current}")
        
    except Exception as e:
        console.print(f"❌ [red]Error reading configuration: {e}[/red]")

@config_group.command()
def validate():
    """Validate configuration file."""
    console.print("✅ [bold blue]Validating Configuration[/bold blue]")
    
    config_dir = Path.home() / ".contextvault"
    config_file = config_dir / "config.yaml"
    
    if not config_file.exists():
        console.print("❌ [red]Configuration file not found[/red]")
        return
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['server', 'ollama', 'database', 'context']
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            console.print(f"❌ [red]Missing required sections: {', '.join(missing_sections)}[/red]")
            return
        
        # Check required values
        required_values = [
            'server.port',
            'ollama.port',
            'database.url',
            'context.max_length'
        ]
        
        missing_values = []
        for value_path in required_values:
            keys = value_path.split('.')
            current = config
            try:
                for k in keys:
                    current = current[k]
            except (KeyError, TypeError):
                missing_values.append(value_path)
        
        if missing_values:
            console.print(f"❌ [red]Missing required values: {', '.join(missing_values)}[/red]")
            return
        
        console.print("✅ [green]Configuration is valid[/green]")
        
    except yaml.YAMLError as e:
        console.print(f"❌ [red]Invalid YAML syntax: {e}[/red]")
    except Exception as e:
        console.print(f"❌ [red]Error validating configuration: {e}[/red]")

@config_group.command()
def reset():
    """Reset configuration to defaults."""
    console.print("🔄 [bold blue]Resetting Configuration to Defaults[/bold blue]")
    
    if click.confirm("Are you sure you want to reset the configuration?"):
        config_file = Path.home() / ".contextvault" / "config.yaml"
        
        try:
            if config_file.exists():
                config_file.unlink()
            
            # Re-initialize
            init()
            
        except Exception as e:
            console.print(f"❌ [red]Error resetting configuration: {e}[/red]")
    else:
        console.print("❌ [yellow]Configuration reset cancelled[/yellow]")
