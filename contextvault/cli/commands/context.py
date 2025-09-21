"""Context management commands for ContextVault CLI."""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextvault.services.vault import VaultService
from contextvault.services.semantic_search import get_semantic_search_service
from contextvault.services.feedback import get_feedback_service
from contextvault.models import ContextType
from contextvault.database import get_db_context

console = Console()


@click.group(name="context")
def context_group():
    """Manage context entries."""
    pass


@context_group.command()
@click.argument('content')
@click.option('--type', 'context_type', 
              type=click.Choice(['text', 'file', 'event', 'preference', 'note']),
              default='text', help='Type of context entry')
@click.option('--source', help='Source of the context')
@click.option('--tags', help='Comma-separated list of tags')
@click.option('--metadata', help='JSON metadata for the entry')
def add(content, context_type, source, tags, metadata):
    """Add a new context entry."""
    try:
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Parse metadata
        metadata_dict = {}
        if metadata:
            import json
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError as e:
                console.print(f"❌ [bold red]Invalid JSON metadata:[/bold red] {e}")
                sys.exit(1)
        
        # Create context entry with proper session management
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            entry = vault_service.save_context(
                content=content,
                context_type=ContextType(context_type),
                source=source,
                tags=tag_list,
                metadata=metadata_dict,
            )
            db.commit()  # Commit the transaction
            # Access attributes while in session to avoid detached instance errors
            entry_id = entry.id
            entry_content = entry.content
        
        console.print(f"✅ [bold green]Context entry created:[/bold green] {entry_id}")
        console.print(f"   Content: {entry_content[:100]}{'...' if len(entry_content) > 100 else ''}")
        console.print(f"   Type: {context_type}")
        if tag_list:
            console.print(f"   Tags: {', '.join(tag_list)}")
        if source:
            console.print(f"   Source: {source}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to add context:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--tags', help='Filter by tags (comma-separated)')
@click.option('--type', 'context_types', multiple=True,
              type=click.Choice(['text', 'file', 'event', 'preference', 'note']),
              help='Filter by context types')
@click.option('--source', help='Filter by source pattern')
@click.option('--limit', default=20, type=int, help='Maximum number of entries to show')
@click.option('--format', type=click.Choice(['table', 'json', 'brief']), default='table',
              help='Output format')
@click.option('--search', help='Search in content')
def list(tags, context_types, source, limit, format, search):
    """List context entries."""
    try:
        # Build filters
        filters = {}
        
        if tags:
            filters['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        if context_types:
            filters['context_types'] = [ContextType(ct) for ct in context_types]
        
        if source:
            filters['source'] = source
        
        if search:
            filters['search'] = search
        
        # Get entries with proper session management
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            entries, total = vault_service.get_context(
                filters=filters,
                limit=limit,
                order_by="created_at",
                order_desc=True,
            )
            
            # Extract data while still in session to avoid detached instance errors
            entry_data = []
            for entry in entries:
                entry_data.append({
                    'id': entry.id,
                    'content': entry.content,
                    'context_type': entry.context_type,
                    'source': entry.source,
                    'tags': entry.tags,
                    'created_at': entry.created_at,
                    'updated_at': entry.updated_at,
                    'access_count': entry.access_count,
                })
        
        if not entry_data:
            console.print("📭 [yellow]No context entries found[/yellow]")
            return
        
        if format == 'json':
            import json
            console.print(json.dumps(entry_data, indent=2, default=str))
            
        elif format == 'brief':
            console.print(f"📋 [bold]Found {len(entry_data)} entries (showing {len(entry_data)}/{total}):[/bold]\n")
            for entry in entry_data:
                content_preview = entry['content'][:80] + "..." if len(entry['content']) > 80 else entry['content']
                tags_str = f" [{', '.join(entry['tags'])}]" if entry['tags'] else ""
                console.print(f"• {entry['id'][:8]}... [{entry['context_type']}]{tags_str}")
                console.print(f"  {content_preview}")
                console.print()
                
        else:  # table format
            console.print(f"📋 [bold]Context Entries ({len(entry_data)}/{total}):[/bold]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=12)
            table.add_column("Type", style="blue", width=10)
            table.add_column("Content", style="white", width=50)
            table.add_column("Tags", style="green", width=20)
            table.add_column("Created", style="yellow", width=12)
            
            for entry in entry_data:
                content_preview = entry['content'][:47] + "..." if len(entry['content']) > 50 else entry['content']
                tags_str = ", ".join(entry['tags']) if entry['tags'] else ""
                created_str = entry['created_at'].strftime("%m-%d %H:%M") if entry['created_at'] else ""
                
                table.add_row(
                    entry['id'][:8] + "...",
                    entry['context_type'],
                    content_preview,
                    tags_str,
                    created_str
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to list context:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('query')
@click.option('--limit', default=10, type=int, help='Maximum number of results')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def search(query, limit, format):
    """Search context entries by content."""
    try:
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            entries, total = vault_service.search_context(
                query=query,
                limit=limit,
            )
            
            # Extract data while still in session to avoid detached instance errors
            entry_data = []
            for entry in entries:
                entry_data.append({
                    'id': entry.id,
                    'content': entry.content,
                    'context_type': entry.context_type,
                    'source': entry.source,
                    'tags': entry.tags,
                    'created_at': entry.created_at,
                    'updated_at': entry.updated_at,
                    'access_count': entry.access_count,
                })
        
        if not entry_data:
            console.print(f"🔍 [yellow]No results found for '{query}'[/yellow]")
            return
        
        if format == 'json':
            import json
            console.print(json.dumps(entry_data, indent=2, default=str))
        else:
            console.print(f"🔍 [bold]Search results for '{query}' ({len(entry_data)}/{total}):[/bold]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", width=12)
            table.add_column("Type", style="blue", width=10)
            table.add_column("Content", style="white", width=60)
            table.add_column("Access", style="yellow", width=8)
            
            for entry in entry_data:
                content_preview = entry['content'][:57] + "..." if len(entry['content']) > 60 else entry['content']
                
                table.add_row(
                    entry['id'][:8] + "...",
                    entry['context_type'],
                    content_preview,
                    str(entry['access_count'] or 0)
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Search failed:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('entry_id')
@click.option('--format', type=click.Choice(['detailed', 'json']), default='detailed',
              help='Output format')
def show(entry_id, format):
    """Show detailed information about a context entry."""
    try:
        # Find entry by full ID or partial ID
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            filters = {}
            entries, _ = vault_service.get_context(filters=filters, limit=1000)
            
            # Extract data while still in session to avoid detached instance errors
            entry = None
            for e in entries:
                if e.id == entry_id or e.id.startswith(entry_id):
                    entry = {
                        'id': e.id,
                        'content': e.content,
                        'context_type': e.context_type,
                        'source': e.source,
                        'tags': e.tags,
                        'entry_metadata': e.entry_metadata,
                        'user_id': e.user_id,
                        'session_id': e.session_id,
                        'created_at': e.created_at,
                        'updated_at': e.updated_at,
                        'access_count': e.access_count,
                        'last_accessed_at': e.last_accessed_at,
                    }
                    break
        
        if not entry:
            console.print(f"❌ [bold red]Context entry not found:[/bold red] {entry_id}")
            sys.exit(1)
        
        if format == 'json':
            import json
            console.print(json.dumps(entry, indent=2, default=str))
        else:
            # Detailed format
            console.print(Panel.fit(f"📄 [bold]Context Entry: {entry['id']}[/bold]"))
            
            console.print(f"[bold cyan]Content:[/bold cyan]")
            console.print(entry['content'])
            console.print()
            
            console.print(f"[bold cyan]Metadata:[/bold cyan]")
            console.print(f"  Type: {entry['context_type']}")
            console.print(f"  Created: {entry['created_at']}")
            console.print(f"  Updated: {entry['updated_at']}")
            console.print(f"  Access Count: {entry['access_count'] or 0}")
            
            if entry['last_accessed_at']:
                console.print(f"  Last Accessed: {entry['last_accessed_at']}")
            
            if entry['source']:
                console.print(f"  Source: {entry['source']}")
            
            if entry['tags']:
                console.print(f"  Tags: {', '.join(entry['tags'])}")
            
            if entry['user_id']:
                console.print(f"  User ID: {entry['user_id']}")
            
            if entry['session_id']:
                console.print(f"  Session ID: {entry['session_id']}")
            
            if entry['entry_metadata']:
                console.print(f"  Metadata: {entry['entry_metadata']}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to show context entry:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('entry_id')
@click.option('--content', help='New content')
@click.option('--tags', help='New tags (comma-separated)')
@click.option('--type', 'context_type',
              type=click.Choice(['text', 'file', 'event', 'preference', 'note']),
              help='New context type')
@click.option('--source', help='New source')
def update(entry_id, content, tags, context_type, source):
    """Update a context entry."""
    try:
        # Build updates
        updates = {}
        
        if content:
            updates['content'] = content
        
        if tags is not None:
            updates['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        if context_type:
            updates['context_type'] = ContextType(context_type)
        
        if source is not None:
            updates['source'] = source
        
        if not updates:
            console.print("❌ [bold red]No updates specified[/bold red]")
            sys.exit(1)
        
        # Update entry
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            entry = vault_service.update_context(entry_id, updates)
        
        if not entry:
            console.print(f"❌ [bold red]Context entry not found:[/bold red] {entry_id}")
            sys.exit(1)
        
        console.print(f"✅ [bold green]Context entry updated:[/bold green] {entry.id}")
        
        # Show what was updated
        for field, value in updates.items():
            console.print(f"   {field.title()}: {value}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to update context entry:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('entry_id')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def delete(entry_id, force):
    """Delete a context entry."""
    try:
        if not force:
            if not click.confirm(f"Are you sure you want to delete context entry {entry_id}?"):
                console.print("❌ [yellow]Deletion cancelled[/yellow]")
                return
        
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            success = vault_service.delete_context(entry_id)
        
        if success:
            console.print(f"✅ [bold green]Context entry deleted:[/bold green] {entry_id}")
        else:
            console.print(f"❌ [bold red]Context entry not found:[/bold red] {entry_id}")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to delete context entry:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def stats(format):
    """Show context statistics."""
    try:
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            stats_data = vault_service.get_context_stats()
        
        if format == 'json':
            import json
            console.print(json.dumps(stats_data, indent=2, default=str))
        else:
            console.print(Panel.fit("📊 [bold]Context Statistics[/bold]"))
            
            # Basic stats
            console.print(f"Total Entries: [cyan]{stats_data['total_entries']}[/cyan]")
            console.print(f"Total Characters: [cyan]{stats_data['total_content_length']:,}[/cyan]")
            console.print(f"Average Length: [cyan]{stats_data['average_content_length']:.1f}[/cyan]")
            
            # Date range
            if stats_data['date_range']['oldest']:
                console.print(f"Oldest Entry: [cyan]{stats_data['date_range']['oldest']}[/cyan]")
            if stats_data['date_range']['newest']:
                console.print(f"Newest Entry: [cyan]{stats_data['date_range']['newest']}[/cyan]")
            
            # Entries by type
            if stats_data['entries_by_type']:
                console.print("\n[bold]Entries by Type:[/bold]")
                for entry_type, count in stats_data['entries_by_type'].items():
                    console.print(f"  {entry_type}: [green]{count}[/green]")
            
            # Most accessed
            if stats_data['most_accessed']:
                console.print("\n[bold]Most Accessed:[/bold]")
                for entry in stats_data['most_accessed']:
                    console.print(f"  {entry['id'][:8]}... [{entry['context_type']}] ({entry['access_count']} times)")
                    console.print(f"    {entry['content_preview']}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to get statistics:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--days', default=90, type=int, help='Days to keep (older entries will be deleted)')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def cleanup(days, force):
    """Clean up old context entries."""
    try:
        if not force:
            if not click.confirm(f"Delete all context entries older than {days} days?"):
                console.print("❌ [yellow]Cleanup cancelled[/yellow]")
                return
        
        with get_db_context() as db:
            vault_service = VaultService(db_session=db)
            deleted_count = vault_service.cleanup_old_entries(retention_days=days)
        
        if deleted_count > 0:
            console.print(f"✅ [bold green]Cleaned up {deleted_count} old entries[/bold green]")
        else:
            console.print("ℹ️  [blue]No old entries found to clean up[/blue]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Cleanup failed:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('query')
@click.option('--max-results', default=10, type=int, help='Maximum number of results to return')
@click.option('--show-scores', is_flag=True, help='Show similarity scores in results')
@click.option('--model', default='test-model', help='Model ID to use for permission checking')
def test_search(query, max_results, show_scores, model):
    """Test semantic search with a query."""
    try:
        semantic_service = get_semantic_search_service()
        
        if not semantic_service.is_available():
            console.print("❌ [bold red]Semantic search not available[/bold red]")
            console.print("   Install dependencies: pip install sentence-transformers torch")
            sys.exit(1)
        
        console.print(f"🔍 [bold blue]Searching for:[/bold blue] '{query}'")
        console.print(f"📊 [blue]Max results:[/blue] {max_results}")
        console.print()
        
        with get_db_context() as db:
            # Perform semantic search
            results = semantic_service.search_with_hybrid_scoring(
                query=query,
                db_session=db,
                max_results=max_results
            )
            
            # Extract data while session is active to avoid detached instance errors
            results_data = []
            for entry, total_score, score_breakdown in results:
                results_data.append((
                    {
                        'id': entry.id,
                        'content': entry.content,
                        'context_type': entry.context_type,
                        'tags': entry.tags,
                        'created_at': entry.created_at,
                        'access_count': entry.access_count
                    },
                    total_score,
                    score_breakdown
                ))
            results = results_data
        
        if not results:
            console.print("ℹ️  [yellow]No relevant context found[/yellow]")
            return
        
        # Display results
        table = Table(title="Semantic Search Results")
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Content", style="white", max_width=60)
        table.add_column("Type", style="green", width=12)
        table.add_column("Tags", style="blue", width=20)
        
        if show_scores:
            table.add_column("Semantic", style="yellow", width=10)
            table.add_column("Recency", style="yellow", width=10)
            table.add_column("Frequency", style="yellow", width=10)
            table.add_column("Total", style="bold yellow", width=10)
        
        for i, (entry_data, total_score, score_breakdown) in enumerate(results, 1):
            # Truncate content for display
            content = entry_data['content'][:100] + "..." if len(entry_data['content']) > 100 else entry_data['content']
            tags = ", ".join(entry_data['tags'][:3]) if entry_data['tags'] else "None"
            
            row = [
                str(i),
                content,
                entry_data['context_type'] if isinstance(entry_data['context_type'], str) else entry_data['context_type'].value,
                tags
            ]
            
            if show_scores:
                row.extend([
                    f"{score_breakdown['semantic']:.3f}",
                    f"{score_breakdown['recency']:.3f}",
                    f"{score_breakdown['frequency']:.3f}",
                    f"{score_breakdown['total']:.3f}"
                ])
            
            table.add_row(*row)
        
        console.print(table)
        
        # Show cache stats
        cache_stats = semantic_service.get_cache_stats()
        console.print(f"\n📈 [blue]Cache stats:[/blue] {cache_stats['cached_embeddings']} embeddings cached")
        
    except Exception as e:
        console.print(f"❌ [bold red]Search failed:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--force', is_flag=True, help='Force regeneration of all embeddings')
def reindex(force):
    """Regenerate all semantic embeddings."""
    try:
        semantic_service = get_semantic_search_service()
        
        if not semantic_service.is_available():
            console.print("❌ [bold red]Semantic search not available[/bold red]")
            console.print("   Install dependencies: pip install sentence-transformers torch")
            sys.exit(1)
        
        console.print("🔄 [bold blue]Regenerating semantic embeddings...[/bold blue]")
        
        if force:
            console.print("⚠️  [yellow]Force mode: clearing existing cache[/yellow]")
            semantic_service.clear_cache()
        
        with get_db_context() as db:
            updated_count = semantic_service.update_context_embeddings(db, force_update=force)
        
        console.print(f"✅ [bold green]Successfully updated {updated_count} embeddings[/bold green]")
        
        # Show final cache stats
        cache_stats = semantic_service.get_cache_stats()
        console.print(f"📊 [blue]Total cached embeddings:[/blue] {cache_stats['cached_embeddings']}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Reindexing failed:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
def semantic_status():
    """Show semantic search system status."""
    try:
        semantic_service = get_semantic_search_service()
        
        console.print("🤖 [bold blue]Semantic Search Status[/bold blue]")
        console.print()
        
        # Check availability
        cache_stats = semantic_service.get_cache_stats()
        
        if semantic_service.is_available():
            if cache_stats.get('fallback_mode'):
                console.print("✅ [bold green]Semantic search is available (TF-IDF fallback)[/bold green]")
                console.print("⚠️  [yellow]Using TF-IDF fallback instead of sentence transformers[/yellow]")
            else:
                console.print("✅ [bold green]Semantic search is available[/bold green]")
                console.print(f"📦 [blue]Model:[/blue] {semantic_service.model_name}")
            
            console.print(f"🎯 [blue]Similarity threshold:[/blue] {semantic_service.similarity_threshold}")
            console.print(f"📊 [blue]Max results:[/blue] {semantic_service.max_results}")
        else:
            console.print("❌ [bold red]Semantic search is not available[/bold red]")
            console.print("   Install dependencies: pip install sentence-transformers torch")
            sys.exit(1)
        
        # Show cache stats
        cache_stats = semantic_service.get_cache_stats()
        
        console.print("\n📈 [bold blue]Cache Statistics[/bold blue]")
        console.print(f"   Cached embeddings: {cache_stats['cached_embeddings']}")
        console.print(f"   Cache file exists: {cache_stats['cache_file_exists']}")
        console.print(f"   Last update: {cache_stats['last_update'] or 'Never'}")
        
        # Test embedding generation
        console.print("\n🧪 [bold blue]Testing Search Functionality[/bold blue]")
        test_query = "programming languages"
        
        if cache_stats.get('fallback_mode'):
            console.print("🔍 [blue]Testing TF-IDF search...[/blue]")
            # Test TF-IDF search
            try:
                from contextvault.database import get_db_context
                with get_db_context() as db:
                    results = semantic_service.search_similar_contexts(test_query, db, max_results=3)
                
                if results:
                    console.print(f"✅ [green]TF-IDF search working - found {len(results)} results[/green]")
                    for i, (entry, score) in enumerate(results[:2], 1):
                        console.print(f"   {i}. {entry.content[:50]}... (score: {score:.3f})")
                else:
                    console.print("ℹ️  [yellow]TF-IDF search working but no results found[/yellow]")
            except Exception as e:
                console.print(f"❌ [red]TF-IDF search failed: {e}[/red]")
        else:
            console.print("🔍 [blue]Testing embedding generation...[/blue]")
            test_text = "This is a test sentence for embedding generation."
            embedding = semantic_service.generate_embedding(test_text)
            
            if embedding is not None:
                console.print(f"✅ [green]Embedding generated successfully[/green]")
                console.print(f"   Dimension: {len(embedding)}")
                console.print(f"   Sample values: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
            else:
                console.print("❌ [red]Failed to generate embedding[/red]")
        
    except Exception as e:
        console.print(f"❌ [bold red]Status check failed:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.argument('session_id')
@click.argument('rating', type=int)
@click.option('--feedback-text', help='Optional feedback text')
@click.option('--model-id', default='unknown', help='Model ID that generated the response')
@click.option('--user-prompt', help='User prompt that was sent')
@click.option('--ai-response', help='AI response that was received')
def rate_response(session_id, rating, feedback_text, model_id, user_prompt, ai_response):
    """Rate an AI response to help improve ContextVault."""
    try:
        feedback_service = get_feedback_service()
        
        if not 1 <= rating <= 5:
            console.print("❌ [red]Rating must be between 1 and 5[/red]")
            sys.exit(1)
        
        # For CLI usage, we'll use placeholder data if not provided
        if not user_prompt:
            user_prompt = "CLI rating - prompt not provided"
        if not ai_response:
            ai_response = "CLI rating - response not provided"
        
        success = feedback_service.submit_feedback(
            session_id=session_id,
            model_id=model_id,
            user_prompt=user_prompt,
            ai_response=ai_response,
            context_used=[],  # Empty for CLI ratings
            rating=rating,
            feedback_text=feedback_text
        )
        
        if success:
            console.print(f"✅ [green]Feedback submitted successfully[/green]")
            console.print(f"   Session ID: {session_id}")
            console.print(f"   Rating: {rating}/5")
            if feedback_text:
                console.print(f"   Feedback: {feedback_text}")
        else:
            console.print("❌ [red]Failed to submit feedback[/red]")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to submit feedback:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--days', default=30, type=int, help='Number of days to analyze')
def feedback_analytics(days):
    """Show feedback analytics and improvement recommendations."""
    try:
        feedback_service = get_feedback_service()
        analytics = feedback_service.calculate_analytics(days=days)
        
        console.print("📊 [bold blue]User Feedback Analytics[/bold blue]")
        console.print("=" * 50)
        
        # Basic statistics
        console.print(f"\n📈 [blue]Basic Statistics (last {days} days):[/blue]")
        console.print(f"   Total feedback entries: {analytics.total_feedback_count}")
        console.print(f"   Average rating: {analytics.average_rating:.2f}/5.0")
        
        # Rating distribution
        if analytics.rating_distribution:
            console.print(f"\n⭐ [blue]Rating Distribution:[/blue]")
            for rating in range(5, 0, -1):
                count = analytics.rating_distribution.get(rating, 0)
                bar = "█" * (count // 2) if count > 0 else ""
                console.print(f"   {rating} stars: {count:3d} {bar}")
        
        # Context type effectiveness
        if analytics.context_type_effectiveness:
            console.print(f"\n🎯 [blue]Context Type Effectiveness:[/blue]")
            for ctx_type, effectiveness in sorted(analytics.context_type_effectiveness.items(), key=lambda x: x[1], reverse=True):
                status = "✅" if effectiveness >= 4.0 else "⚠️" if effectiveness >= 3.0 else "❌"
                console.print(f"   {status} {ctx_type}: {effectiveness:.2f}/5.0")
        
        # Most helpful context entries
        if analytics.most_helpful_context_entries:
            console.print(f"\n🏆 [blue]Most Helpful Context Entries:[/blue]")
            for i, entry in enumerate(analytics.most_helpful_context_entries, 1):
                console.print(f"   {i}. [{entry['context_type']}] {entry['content_preview']}...")
                console.print(f"      Rating: {entry['average_rating']:.2f} ({entry['rating_count']} ratings)")
        
        # Improvement suggestions
        if analytics.improvement_suggestions:
            console.print(f"\n💡 [blue]Improvement Suggestions:[/blue]")
            for i, suggestion in enumerate(analytics.improvement_suggestions, 1):
                console.print(f"   {i}. {suggestion}")
        
        # Learning recommendations
        recommendations = feedback_service.get_learning_recommendations()
        if recommendations:
            console.print(f"\n🔧 [blue]Learning Recommendations:[/blue]")
            console.print(f"   Priority: {recommendations['priority'].upper()}")
            
            if recommendations['context_retrieval']:
                console.print(f"   Context Retrieval:")
                for rec in recommendations['context_retrieval']:
                    console.print(f"     • {rec}")
            
            if recommendations['template_improvements']:
                console.print(f"   Template Improvements:")
                for rec in recommendations['template_improvements']:
                    console.print(f"     • {rec}")
            
            if recommendations['system_optimization']:
                console.print(f"   System Optimization:")
                for rec in recommendations['system_optimization']:
                    console.print(f"     • {rec}")
        
        console.print(f"\n📅 [blue]Last updated:[/blue] {analytics.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to get feedback analytics:[/bold red] {e}")
        sys.exit(1)


@context_group.command()
@click.option('--limit', default=10, type=int, help='Number of recent feedback entries to show')
def feedback_history(limit):
    """Show recent feedback history."""
    try:
        feedback_service = get_feedback_service()
        recent_feedback = feedback_service.get_recent_feedback(limit)
        
        if not recent_feedback:
            console.print("ℹ️  [yellow]No feedback history available[/yellow]")
            return
        
        console.print(f"📋 [bold blue]Recent Feedback History (last {limit} entries)[/bold blue]")
        
        table = Table(title="Feedback History")
        table.add_column("Session ID", style="cyan", width=12)
        table.add_column("Rating", style="green", width=8)
        table.add_column("Model", style="blue", width=12)
        table.add_column("Prompt Preview", style="white", max_width=40)
        table.add_column("Timestamp", style="yellow", width=16)
        
        for feedback in recent_feedback:
            prompt_preview = feedback.user_prompt[:35] + "..." if len(feedback.user_prompt) > 35 else feedback.user_prompt
            rating_display = "⭐" * feedback.rating + "☆" * (5 - feedback.rating)
            
            table.add_row(
                feedback.session_id[:12],
                rating_display,
                feedback.model_id[:12],
                prompt_preview,
                feedback.timestamp.strftime("%m-%d %H:%M")
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to get feedback history:[/bold red] {e}")
        sys.exit(1)
