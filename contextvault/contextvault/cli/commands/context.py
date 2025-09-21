"""Context management commands for ContextVault CLI."""

import requests
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@click.group(name="context")
def context_group():
    """Context management commands."""
    pass

@context_group.command()
@click.argument('content')
@click.option('--type', 'context_type', default='note', help='Context type (note, preference, etc.)')
@click.option('--source', default='cli', help='Source of the context')
@click.option('--tags', help='Comma-separated tags')
def add(content: str, context_type: str, source: str, tags: Optional[str]):
    """Add a new context entry."""
    console.print("📝 [bold blue]Adding Context Entry[/bold blue]")
    
    try:
        # Prepare tags
        tag_list = [tag.strip() for tag in tags.split(',')] if tags else []
        
        # Add context via API
        response = requests.post('http://localhost:8000/api/context/', json={
            'content': content,
            'context_type': context_type,
            'source': source,
            'tags': tag_list
        })
        
        if response.status_code == 200:
            result = response.json()
            console.print(f"✅ [green]Context added successfully[/green]")
            console.print(f"   ID: {result.get('data', {}).get('id', 'unknown')}")
        else:
            console.print(f"❌ [red]Failed to add context: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error adding context: {e}[/red]")

@context_group.command()
@click.option('--limit', default=10, help='Number of entries to show')
@click.option('--type', 'context_type', help='Filter by context type')
def list(limit: int, context_type: Optional[str]):
    """List context entries."""
    console.print("📋 [bold blue]Context Entries[/bold blue]")
    
    try:
        # Build query parameters
        params = {'limit': limit}
        if context_type:
            params['context_type'] = context_type
        
        response = requests.get('http://localhost:8000/api/context/', params=params)
        
        if response.status_code == 200:
            data = response.json().get('entries', [])
            
            if data:
                table = Table(title="Context Entries")
                table.add_column("ID", style="cyan", width=8)
                table.add_column("Type", style="blue", width=12)
                table.add_column("Content", style="white", max_width=50)
                table.add_column("Source", style="yellow", width=12)
                table.add_column("Tags", style="green", width=20)
                
                for entry in data:
                    content_preview = entry['content'][:47] + "..." if len(entry['content']) > 50 else entry['content']
                    tags_str = ', '.join(entry.get('tags', []))[:17] + "..." if len(', '.join(entry.get('tags', []))) > 20 else ', '.join(entry.get('tags', []))
                    
                    table.add_row(
                        entry['id'][:8],
                        entry['context_type'],
                        content_preview,
                        entry['source'],
                        tags_str
                    )
                
                console.print(table)
            else:
                console.print("ℹ️ [yellow]No context entries found[/yellow]")
        else:
            console.print(f"❌ [red]Failed to list context: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error listing context: {e}[/red]")

@context_group.command()
@click.argument('query')
@click.option('--limit', default=5, help='Number of results to show')
@click.option('--show-scores', is_flag=True, help='Show similarity scores')
def search(query: str, limit: int, show_scores: bool):
    """Search context entries."""
    console.print(f"🔍 [bold blue]Searching: '{query}'[/bold blue]")
    
    try:
        response = requests.get('http://localhost:11435/api/context/search', params={
            'query': query,
            'limit': limit
        })
        
        if response.status_code == 200:
            data = response.json().get('entries', [])
            
            if data:
                for i, entry in enumerate(data, 1):
                    panel_content = f"""[bold]Content:[/bold] {entry['content']}
[bold]Type:[/bold] {entry['context_type']}
[bold]Source:[/bold] {entry['source']}
[bold]Tags:[/bold] {', '.join(entry.get('tags', []))}"""
                    
                    if show_scores and 'similarity_score' in entry:
                        panel_content += f"\n[bold]Similarity:[/bold] {entry['similarity_score']:.3f}"
                    
                    panel = Panel(
                        panel_content,
                        title=f"Result {i}",
                        border_style="blue"
                    )
                    console.print(panel)
            else:
                console.print("ℹ️ [yellow]No matching context found[/yellow]")
        else:
            console.print(f"❌ [red]Search failed: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error searching context: {e}[/red]")

@context_group.command()
@click.argument('context_id')
def delete(context_id: str):
    """Delete a context entry."""
    console.print(f"🗑️ [bold blue]Deleting Context Entry: {context_id}[/bold blue]")
    
    if not click.confirm("Are you sure you want to delete this context entry?"):
        console.print("❌ [yellow]Deletion cancelled[/yellow]")
        return
    
    try:
        response = requests.delete(f'http://localhost:11435/api/context/{context_id}')
        
        if response.status_code == 200:
            console.print("✅ [green]Context deleted successfully[/green]")
        elif response.status_code == 404:
            console.print("❌ [red]Context entry not found[/red]")
        else:
            console.print(f"❌ [red]Failed to delete context: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error deleting context: {e}[/red]")

@context_group.command()
def stats():
    """Show context statistics."""
    console.print("📊 [bold blue]Context Statistics[/bold blue]")
    
    try:
        # Get all context entries
        response = requests.get('http://localhost:11435/api/context/list', params={'limit': 1000})
        
        if response.status_code == 200:
            data = response.json().get('entries', [])
            
            # Calculate statistics
            total_entries = len(data)
            context_types = {}
            sources = {}
            total_tags = set()
            
            for entry in data:
                # Count by type
                ctx_type = entry['context_type']
                context_types[ctx_type] = context_types.get(ctx_type, 0) + 1
                
                # Count by source
                source = entry['source']
                sources[source] = sources.get(source, 0) + 1
                
                # Collect tags
                total_tags.update(entry.get('tags', []))
            
            # Display statistics
            stats_panel = Panel(
                f"""[bold]Total Entries:[/bold] {total_entries}
[bold]Unique Tags:[/bold] {len(total_tags)}
[bold]Context Types:[/bold] {len(context_types)}
[bold]Sources:[/bold] {len(sources)}

[bold]By Type:[/bold]
{chr(10).join([f"  • {ctx_type}: {count}" for ctx_type, count in context_types.items()])}

[bold]By Source:[/bold]
{chr(10).join([f"  • {source}: {count}" for source, count in sources.items()])}

[bold]Most Common Tags:[/bold]
{chr(10).join([f"  • {tag}" for tag in sorted(total_tags)[:10]])}""",
                title="Context Statistics",
                border_style="blue"
            )
            
            console.print(stats_panel)
        else:
            console.print(f"❌ [red]Failed to get statistics: {response.status_code}[/red]")
            
    except requests.exceptions.ConnectionError:
        console.print("❌ [red]ContextVault proxy not running[/red]")
        console.print("   Start it with: python -m contextvault.cli start")
    except Exception as e:
        console.print(f"❌ [red]Error getting statistics: {e}[/red]")
