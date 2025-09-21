"""Conversation learning management commands for ContextVault CLI."""

import asyncio
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

console = Console()

@click.group(name="learning")
def learning_group():
    """Conversation learning management commands."""
    pass

@learning_group.command()
def stats():
    """Show conversation learning statistics."""
    console.print("🧠 [bold blue]Conversation Learning Statistics[/bold blue]")
    
    try:
        from contextvault.services.conversation_learning import conversation_learning_service
        
        async def get_stats():
            return await conversation_learning_service.get_learning_stats()
        
        stats = asyncio.run(get_stats())
        
        if 'error' in stats:
            console.print(f"❌ [red]Error getting stats: {stats['error']}[/red]")
            return
        
        panel_content = f"""[bold]Total Learned Entries:[/bold] {stats.get('total_learned', 0)}
[bold]Recent Learning (24h):[/bold] {stats.get('recent_learning', 0)}

[bold]By Source:[/bold]
{chr(10).join([f"  • {source}: {count}" for source, count in stats.get('by_source', {}).items()])}

[bold]By Context Type:[/bold]
{chr(10).join([f"  • {context_type}: {count}" for context_type, count in stats.get('by_context_type', {}).items()])}"""
        
        panel = Panel(
            panel_content,
            title="Learning Statistics",
            border_style="blue"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"❌ [red]Error getting learning stats: {e}[/red]")

@learning_group.command()
@click.option('--limit', default=10, help='Number of recent learned entries to show')
@click.option('--source', help='Filter by source (user_prompt, ai_response)')
def list(limit: int, source: Optional[str]):
    """List recently learned context entries."""
    console.print("📚 [bold blue]Recently Learned Context[/bold blue]")
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models import ContextEntry
        
        with get_db_context() as db:
            # Build query
            query = db.query(ContextEntry).filter(
                ContextEntry.source.in_(['user_prompt', 'ai_response'])
            ).order_by(ContextEntry.created_at.desc())
            
            if source:
                query = query.filter(ContextEntry.source == source)
            
            entries = query.limit(limit).all()
            
            if entries:
                table = Table(title=f"Recent Learned Context ({len(entries)} entries)")
                table.add_column("ID", style="cyan", width=8)
                table.add_column("Source", style="blue", width=12)
                table.add_column("Type", style="green", width=10)
                table.add_column("Content", style="white", max_width=50)
                table.add_column("Tags", style="yellow", width=20)
                table.add_column("Created", style="magenta", width=12)
                
                for entry in entries:
                    # Truncate content for display
                    content = entry.content
                    if len(content) > 47:
                        content = content[:47] + "..."
                    
                    tags_str = ", ".join(entry.tags or [])[:17] + "..." if entry.tags and len(", ".join(entry.tags)) > 17 else ", ".join(entry.tags or [])
                    
                    created_str = entry.created_at.strftime('%m-%d %H:%M') if entry.created_at else "Unknown"
                    
                    table.add_row(
                        entry.id[:8],
                        entry.source or "Unknown",
                        entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type),
                        content,
                        tags_str,
                        created_str
                    )
                
                console.print(table)
            else:
                console.print("ℹ️ [yellow]No learned context entries found[/yellow]")
            
    except Exception as e:
        console.print(f"❌ [red]Error listing learned context: {e}[/red]")

@learning_group.command()
@click.argument('entry_id')
def show(entry_id: str):
    """Show details of a specific learned context entry."""
    console.print(f"🔍 [bold blue]Context Entry Details: {entry_id}[/bold blue]")
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models import ContextEntry
        
        with get_db_context() as db:
            entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
            
            if not entry:
                console.print("❌ [red]Context entry not found[/red]")
                return
            
            panel_content = f"""[bold]ID:[/bold] {entry.id}
[bold]Content:[/bold] {entry.content}
[bold]Type:[/bold] {entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)}
[bold]Source:[/bold] {entry.source or 'Unknown'}
[bold]Tags:[/bold] {', '.join(entry.tags or [])}
[bold]Created:[/bold] {entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else 'Unknown'}

[bold]Metadata:[/bold]
{chr(10).join([f"  • {key}: {value}" for key, value in (entry.entry_metadata or {}).items()])}"""
            
            panel = Panel(
                panel_content,
                title="Context Entry Details",
                border_style="blue"
            )
            console.print(panel)
        
    except Exception as e:
        console.print(f"❌ [red]Error showing context entry: {e}[/red]")

@learning_group.command()
@click.argument('entry_id')
@click.confirmation_option(prompt="Are you sure you want to delete this learned context entry?")
def delete(entry_id: str):
    """Delete a learned context entry."""
    console.print(f"🗑️ [bold blue]Deleting Context Entry: {entry_id}[/bold blue]")
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models import ContextEntry
        
        with get_db_context() as db:
            entry = db.query(ContextEntry).filter(ContextEntry.id == entry_id).first()
            
            if not entry:
                console.print("❌ [red]Context entry not found[/red]")
                return
            
            # Check if it's a learned entry
            if entry.source not in ['user_prompt', 'ai_response']:
                console.print("❌ [red]This is not a learned context entry[/red]")
                return
            
            db.delete(entry)
            db.commit()
            
            console.print("✅ [green]Context entry deleted successfully[/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Error deleting context entry: {e}[/red]")

@learning_group.command()
@click.option('--days', default=7, help='Number of days to analyze')
def analyze(days: int):
    """Analyze learning patterns and effectiveness."""
    console.print(f"📊 [bold blue]Learning Analysis (Last {days} days)[/bold blue]")
    
    try:
        from contextvault.database import get_db_context
        from contextvault.models import ContextEntry
        from datetime import datetime, timedelta
        
        with get_db_context() as db:
            # Get entries from the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            entries = db.query(ContextEntry).filter(
                ContextEntry.source.in_(['user_prompt', 'ai_response']),
                ContextEntry.created_at >= cutoff_date
            ).all()
            
            if not entries:
                console.print("ℹ️ [yellow]No learned entries found in the specified period[/yellow]")
                return
            
            # Analyze patterns
            total_entries = len(entries)
            by_source = {}
            by_type = {}
            by_category = {}
            
            for entry in entries:
                # Count by source
                source = entry.source or 'unknown'
                by_source[source] = by_source.get(source, 0) + 1
                
                # Count by type
                context_type = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
                by_type[context_type] = by_type.get(context_type, 0) + 1
                
                # Count by category (from tags)
                if entry.tags:
                    for tag in entry.tags:
                        if tag in ['personal_facts', 'goals_projects', 'preferences', 'relationships', 'skills_expertise', 'schedule_time']:
                            by_category[tag] = by_category.get(tag, 0) + 1
        
        # Create analysis panels
        panels = []
        
        # Overview
        overview_content = f"""[bold]Total Learned:[/bold] {total_entries}
[bold]Learning Rate:[/bold] {total_entries / days:.1f} entries/day
[bold]Period:[/bold] Last {days} days"""
        panels.append(Panel(overview_content, title="Overview", border_style="green"))
        
        # By source
        source_content = "\n".join([f"• {source}: {count}" for source, count in by_source.items()])
        panels.append(Panel(source_content, title="By Source", border_style="blue"))
        
        # By type
        type_content = "\n".join([f"• {context_type}: {count}" for context_type, count in by_type.items()])
        panels.append(Panel(type_content, title="By Context Type", border_style="yellow"))
        
        # By category
        if by_category:
            category_content = "\n".join([f"• {category}: {count}" for category, count in by_category.items()])
            panels.append(Panel(category_content, title="By Category", border_style="magenta"))
        
        console.print(Columns(panels))
        
    except Exception as e:
        console.print(f"❌ [red]Error analyzing learning patterns: {e}[/red]")

@learning_group.command()
@click.option('--enable/--disable', default=None, help='Enable or disable conversation learning')
def toggle(enable: Optional[bool]):
    """Enable or disable conversation learning."""
    console.print("⚙️ [bold blue]Conversation Learning Settings[/bold blue]")
    
    # For now, learning is always enabled
    # In the future, this could be a configuration setting
    
    if enable is None:
        console.print("ℹ️ [yellow]Conversation learning is currently enabled[/yellow]")
        console.print("   ContextVault automatically learns from all conversations")
        console.print("   Use --enable or --disable to change this setting")
    elif enable:
        console.print("✅ [green]Conversation learning enabled[/green]")
        console.print("   ContextVault will now learn from conversations")
    else:
        console.print("❌ [red]Conversation learning disabled[/red]")
        console.print("   ContextVault will not learn from conversations")
    
    console.print("\n[bold]Note:[/bold] This feature is always active in the current version")
    console.print("   Future versions will support toggling this feature")

@learning_group.command()
def demo():
    """Demonstrate conversation learning with sample data."""
    console.print("🎯 [bold blue]Conversation Learning Demo[/bold blue]")
    
    try:
        from contextvault.services.conversation_learning import conversation_learning_service
        
        # Sample conversation
        sample_prompt = "I'm working on a React app with TypeScript. I prefer Python over JavaScript for backend work. I live in San Francisco and I have two cats named Luna and Pixel."
        sample_response = "Based on your preferences, I can see you're a full-stack developer who prefers Python for backend development and is working on a React TypeScript project. Since you're in San Francisco, you have access to great tech resources, and having cats Luna and Pixel must be nice company while coding!"
        
        console.print("📝 [bold]Sample Conversation:[/bold]")
        console.print(f"[bold]User:[/bold] {sample_prompt}")
        console.print(f"[bold]AI:[/bold] {sample_response}")
        
        console.print("\n🧠 [bold]Learning from conversation...[/bold]")
        
        async def demo_learning():
            learned_entries = await conversation_learning_service.learn_from_conversation(
                user_prompt=sample_prompt,
                ai_response=sample_response,
                model_id="demo_model",
                session_id="demo_session",
                user_id="demo_user"
            )
            return learned_entries
        
        learned_entries = asyncio.run(demo_learning())
        
        if learned_entries:
            console.print(f"✅ [green]Successfully learned {len(learned_entries)} context entries![/green]")
            
            table = Table(title="Learned Context Entries")
            table.add_column("Content", style="white", max_width=40)
            table.add_column("Type", style="green", width=12)
            table.add_column("Source", style="blue", width=12)
            table.add_column("Tags", style="yellow", width=20)
            
            for entry in learned_entries:
                content = entry.content
                if len(content) > 37:
                    content = content[:37] + "..."
                
                tags_str = ", ".join(entry.tags or [])[:17] + "..." if entry.tags and len(", ".join(entry.tags)) > 17 else ", ".join(entry.tags or [])
                
                table.add_row(
                    content,
                    entry.context_type.value,
                    entry.source or "Unknown",
                    tags_str
                )
            
            console.print(table)
        else:
            console.print("ℹ️ [yellow]No new context was learned from this conversation[/yellow]")
            console.print("   This might happen if the content was too generic or already exists")
        
    except Exception as e:
        console.print(f"❌ [red]Demo failed: {e}[/red]")
