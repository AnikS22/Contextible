"""MCP (Model Context Protocol) management commands for ContextVault CLI."""

import requests
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@click.group(name="mcp")
def mcp_group():
    """MCP (Model Context Protocol) management commands."""
    pass

@mcp_group.command()
def list():
    """List all MCP connections."""
    console.print("🔗 [bold blue]MCP Connections[/bold blue]")
    
    try:
        response = requests.get('http://localhost:8000/api/mcp/connections')
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                table = Table(title="MCP Connections")
                table.add_column("ID", style="cyan", width=8)
                table.add_column("Name", style="blue", width=20)
                table.add_column("Provider Type", style="green", width=15)
                table.add_column("Status", style="yellow", width=10)
                table.add_column("Endpoint", style="white", width=30)
                
                for connection in data:
                    status_color = "green" if connection.get('status') == 'active' else "red"
                    table.add_row(
                        connection['id'][:8],
                        connection['name'],
                        connection['provider_type'],
                        f"[{status_color}]{connection.get('status', 'unknown')}[/{status_color}]",
                        connection.get('endpoint', 'N/A')
                    )
                
                console.print(table)
            else:
                console.print("ℹ️ [yellow]No MCP connections configured[/yellow]")
        else:
            console.print(f"❌ [red]Failed to list connections: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error listing connections: {e}[/red]")

@mcp_group.command()
@click.argument('name')
@click.argument('provider_type')
@click.argument('endpoint')
@click.option('--config', help='Configuration JSON string')
def add(name: str, provider_type: str, endpoint: str, config: Optional[str]):
    """Add a new MCP connection."""
    console.print(f"➕ [bold blue]Adding MCP Connection: {name}[/bold blue]")
    
    # Parse config if provided
    config_data = {}
    if config:
        try:
            import json
            config_data = json.loads(config)
        except json.JSONDecodeError:
            console.print("❌ [red]Invalid JSON configuration[/red]")
            return
    
    try:
        response = requests.post('http://localhost:8000/api/mcp/connections', json={
            'name': name,
            'provider_type': provider_type,
            'endpoint': endpoint,
            'config': config_data
        })
        
        if response.status_code == 200:
            result = response.json()
            console.print("✅ [green]MCP connection added successfully[/green]")
            console.print(f"   ID: {result.get('data', {}).get('id', 'unknown')}")
        else:
            console.print(f"❌ [red]Failed to add connection: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error adding connection: {e}[/red]")

@mcp_group.command()
@click.argument('connection_id')
def delete(connection_id: str):
    """Delete an MCP connection."""
    console.print(f"🗑️ [bold blue]Deleting MCP Connection: {connection_id}[/bold blue]")
    
    if not click.confirm("Are you sure you want to delete this MCP connection?"):
        console.print("❌ [yellow]Deletion cancelled[/yellow]")
        return
    
    try:
        response = requests.delete(f'http://localhost:8000/api/mcp/connections/{connection_id}')
        
        if response.status_code == 200:
            console.print("✅ [green]MCP connection deleted successfully[/green]")
        elif response.status_code == 404:
            console.print("❌ [red]MCP connection not found[/red]")
        else:
            console.print(f"❌ [red]Failed to delete connection: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error deleting connection: {e}[/red]")

@mcp_group.command()
def providers():
    """List MCP providers for models."""
    console.print("🔌 [bold blue]MCP Providers[/bold blue]")
    
    try:
        response = requests.get('http://localhost:8000/api/mcp/providers')
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                table = Table(title="MCP Providers")
                table.add_column("Model ID", style="cyan", width=20)
                table.add_column("Connection", style="blue", width=20)
                table.add_column("Enabled", style="green", width=8)
                table.add_column("Scopes", style="yellow", width=30)
                
                for provider in data:
                    enabled_str = "✅ Yes" if provider.get('enabled', False) else "❌ No"
                    scopes_str = ', '.join(provider.get('scopes', []))
                    
                    table.add_row(
                        provider['model_id'],
                        provider.get('connection_name', 'Unknown'),
                        enabled_str,
                        scopes_str
                    )
                
                console.print(table)
            else:
                console.print("ℹ️ [yellow]No MCP providers configured[/yellow]")
        else:
            console.print(f"❌ [red]Failed to list providers: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error listing providers: {e}[/red]")

@mcp_group.command()
@click.argument('model_id')
@click.argument('connection_id')
@click.argument('scopes')
@click.option('--enabled/--disabled', default=True, help='Enable or disable the provider')
def enable(model_id: str, connection_id: str, scopes: str, enabled: bool):
    """Enable MCP provider for a model."""
    action = "enable" if enabled else "disable"
    console.print(f"🔌 [bold blue]{action.title()}ing MCP Provider for {model_id}[/bold blue]")
    
    # Parse scopes
    scope_list = [scope.strip() for scope in scopes.split(',')]
    
    try:
        response = requests.post('http://localhost:8000/api/mcp/providers', json={
            'model_id': model_id,
            'connection_id': connection_id,
            'enabled': enabled,
            'scopes': scope_list
        })
        
        if response.status_code == 200:
            console.print(f"✅ [green]MCP provider {action}d successfully[/green]")
            console.print(f"   Model: {model_id}")
            console.print(f"   Scopes: {', '.join(scope_list)}")
        else:
            console.print(f"❌ [red]Failed to {action} provider: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error {action}ing provider: {e}[/red]")

@mcp_group.command()
@click.argument('model_id')
@click.argument('query')
@click.option('--limit', default=5, help='Number of results to show')
def search(model_id: str, query: str, limit: int):
    """Search MCP data for a model."""
    console.print(f"🔍 [bold blue]Searching MCP Data for {model_id}[/bold blue]")
    console.print(f"   Query: '{query}'")
    
    try:
        response = requests.get('http://localhost:8000/api/mcp/search', params={
            'model_id': model_id,
            'query': query,
            'limit': limit
        })
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                for i, result in enumerate(data, 1):
                    panel_content = f"""[bold]Title:[/bold] {result.get('title', 'N/A')}
[bold]Source:[/bold] {result.get('source', 'N/A')}
[bold]Content:[/bold] {result.get('content', 'N/A')[:200]}{'...' if len(result.get('content', '')) > 200 else ''}
[bold]Date:[/bold] {result.get('date', 'N/A')}"""
                    
                    panel = Panel(
                        panel_content,
                        title=f"Result {i}",
                        border_style="blue"
                    )
                    console.print(panel)
            else:
                console.print("ℹ️ [yellow]No MCP data found for query[/yellow]")
        else:
            console.print(f"❌ [red]Search failed: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error searching MCP data: {e}[/red]")

@mcp_group.command()
def status():
    """Show MCP system status."""
    console.print("📊 [bold blue]MCP System Status[/bold blue]")
    
    try:
        # Get connections
        connections_response = requests.get('http://localhost:8000/api/mcp/connections')
        connections_data = connections_response.json().get('data', []) if connections_response.status_code == 200 else []
        
        # Get providers
        providers_response = requests.get('http://localhost:8000/api/mcp/providers')
        providers_data = providers_response.json().get('data', []) if providers_response.status_code == 200 else []
        
        # Calculate statistics
        total_connections = len(connections_data)
        active_connections = len([c for c in connections_data if c.get('status') == 'active'])
        total_providers = len(providers_data)
        enabled_providers = len([p for p in providers_data if p.get('enabled', False)])
        
        # Provider types
        provider_types = {}
        for connection in connections_data:
            provider_type = connection.get('provider_type', 'unknown')
            provider_types[provider_type] = provider_types.get(provider_type, 0) + 1
        
        panel_content = f"""[bold]Connections:[/bold] {active_connections}/{total_connections} active
[bold]Providers:[/bold] {enabled_providers}/{total_providers} enabled

[bold]Provider Types:[/bold]
{chr(10).join([f"  • {ptype}: {count}" for ptype, count in provider_types.items()])}

[bold]Models with MCP Access:[/bold]
{chr(10).join([f"  • {provider['model_id']}: {', '.join(provider.get('scopes', []))}" for provider in providers_data if provider.get('enabled', False)])}"""
        
        panel = Panel(
            panel_content,
            title="MCP System Status",
            border_style="blue"
        )
        console.print(panel)
        
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error getting MCP status: {e}[/red]")

@mcp_group.command()
def demo():
    """Run MCP integration demo."""
    console.print("🎯 [bold blue]Running MCP Integration Demo[/bold blue]")
    
    import subprocess
    import sys
    from pathlib import Path
    
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "mcp_calendar_demo.py"
    
    try:
        subprocess.run([
            sys.executable, str(script_path)
        ])
    except Exception as e:
        console.print(f"❌ [red]Error running demo: {e}[/red]")
