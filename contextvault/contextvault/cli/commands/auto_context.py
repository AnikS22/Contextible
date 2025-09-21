"""Auto context extraction commands for ContextVault CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

@click.group(name="auto-context")
def auto_context():
    """Automatic context extraction commands."""
    pass

@auto_context.command()
def status():
    """Show status of automatic context extraction."""
    try:
        from contextvault.services.conversation_logger import conversation_logger
        from contextvault.database import get_db_context
        from contextvault.services.vault import vault_service
        
        stats = conversation_logger.get_conversation_stats()
        
        # Get auto-extracted context count
        with get_db_context() as db:
            auto_extracted_count = db.query(vault_service.ContextEntry).filter(
                vault_service.ContextEntry.metadata.contains('auto_extracted')
            ).count()
        
        console.print(Panel.fit("🤖 Automatic Context Extraction Status", style="bold blue"))
        
        table = Table(title="Extraction Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Active Conversations", str(stats['active_conversations']))
        table.add_row("Total Conversations", str(stats['total_conversations']))
        table.add_row("Auto-Extracted Context Entries", str(auto_extracted_count))
        table.add_row("Extraction Status", "🟢 Active" if stats['active_conversations'] > 0 else "🟡 Idle")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}")

@auto_context.command()
@click.option("--limit", "-l", default=10, help="Number of recent conversations to show")
def conversations(limit):
    """Show recent conversations."""
    try:
        from contextvault.services.conversation_logger import conversation_logger
        
        conversations = conversation_logger.get_recent_conversations(limit)
        
        if not conversations:
            console.print("📝 No recent conversations found.")
            return
        
        console.print(Panel.fit(f"💬 Recent Conversations (Last {limit})", style="bold blue"))
        
        for conv in conversations:
            console.print(f"\n🔹 [bold]{conv.conversation_id}[/bold]")
            console.print(f"   Model: {conv.model_id}")
            console.print(f"   Messages: {len(conv.messages)}")
            console.print(f"   Duration: {conv.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {conv.end_time.strftime('%Y-%m-%d %H:%M:%S') if conv.end_time else 'Active'}")
            
            # Show message preview
            if conv.messages:
                user_msg = next((msg for msg in conv.messages if msg.role == 'user'), None)
                if user_msg:
                    preview = user_msg.content[:100] + "..." if len(user_msg.content) > 100 else user_msg.content
                    console.print(f"   Preview: {preview}")
        
    except Exception as e:
        console.print(f"❌ Error getting conversations: {e}")

@auto_context.command()
@click.option("--limit", "-l", default=10, help="Number of entries to show")
@click.option("--confidence", "-c", type=float, help="Minimum confidence score")
def extracted(limit, confidence):
    """Show auto-extracted context entries."""
    try:
        from contextvault.database import get_db_context
        from contextvault.services.vault import vault_service
        from contextvault.models import ContextEntry
        
        with get_db_context() as db:
            query = db.query(ContextEntry).filter(
                ContextEntry.metadata.contains('auto_extracted')
            ).order_by(ContextEntry.created_at.desc())
            
            if confidence:
                # Filter by confidence score
                query = query.filter(
                    ContextEntry.metadata.contains(f'"extraction_confidence": {confidence}')
                )
            
            entries = query.limit(limit).all()
        
        if not entries:
            console.print("📝 No auto-extracted context entries found.")
            return
        
        console.print(Panel.fit(f"🤖 Auto-Extracted Context Entries (Last {limit})", style="bold blue"))
        
        table = Table(title="Extracted Context")
        table.add_column("Type", style="cyan", width=12)
        table.add_column("Content", style="white", max_width=50)
        table.add_column("Confidence", style="green", width=10)
        table.add_column("Source", style="blue", width=12)
        table.add_column("Created", style="yellow", width=12)
        
        for entry in entries:
            confidence_score = entry.metadata.get('extraction_confidence', 0) if entry.metadata else 0
            source = entry.source or 'unknown'
            created = entry.created_at.strftime('%m-%d %H:%M')
            
            content_preview = entry.content[:47] + "..." if len(entry.content) > 50 else entry.content
            
            confidence_color = "green" if confidence_score > 0.7 else "yellow" if confidence_score > 0.4 else "red"
            
            table.add_row(
                entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type),
                content_preview,
                f"[{confidence_color}]{confidence_score:.2f}[/{confidence_color}]",
                source,
                created
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error getting extracted entries: {e}")

@auto_context.command()
@click.option("--conversation-id", "-c", help="Specific conversation ID")
def extract_from_conversation(conversation_id):
    """Manually extract context from a specific conversation."""
    try:
        from contextvault.services.conversation_logger import conversation_logger
        from contextvault.services.context_extractor import context_extractor
        from contextvault.services.deduplication import context_deduplicator
        from contextvault.services.validation import context_validator
        from contextvault.services.vault import vault_service
        from contextvault.database import get_db_context
        
        if conversation_id:
            conversation = conversation_logger.get_conversation(conversation_id)
            if not conversation:
                console.print(f"❌ Conversation {conversation_id} not found.")
                return
            conversations = [conversation]
        else:
            conversations = conversation_logger.get_recent_conversations(5)
        
        if not conversations:
            console.print("📝 No conversations found.")
            return
        
        total_extracted = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting context...", total=len(conversations))
            
            for conversation in conversations:
                # Extract context
                extracted_contexts = context_extractor.extract_from_conversation(
                    conversation.conversation_id, conversation.messages
                )
                
                if extracted_contexts:
                    # Get existing contexts for deduplication
                    with get_db_context() as db:
                        existing_contexts = db.query(vault_service.ContextEntry).all()
                    
                    # Deduplicate
                    deduplicated_contexts = context_deduplicator.deduplicate_extracted_context(
                        extracted_contexts, existing_contexts
                    )
                    
                    # Validate
                    validation_results = context_validator.validate_context_batch(deduplicated_contexts)
                    
                    # Save valid contexts
                    for i, context in enumerate(deduplicated_contexts):
                        validation_result = validation_results[i]
                        
                        if validation_result.status.value in ['valid', 'needs_review']:
                            with get_db_context() as db:
                                context_entry = vault_service.ContextEntry(
                                    content=context.content,
                                    context_type=context.context_type,
                                    source=context.source,
                                    tags=', '.join(context.tags),
                                    metadata={
                                        'conversation_id': context.conversation_id,
                                        'extraction_confidence': context.confidence,
                                        'validation_status': validation_result.status.value,
                                        'validation_confidence': validation_result.confidence,
                                        'auto_extracted': True,
                                        'manual_extraction': True,
                                        **context.metadata
                                    }
                                )
                                db.add(context_entry)
                                db.commit()
                                total_extracted += 1
                
                progress.advance(task)
        
        console.print(f"✅ Successfully extracted {total_extracted} context entries.")
        
    except Exception as e:
        console.print(f"❌ Error extracting context: {e}")

@auto_context.command()
def settings():
    """Show automatic context extraction settings."""
    try:
        from contextvault.services.context_extractor import context_extractor
        from contextvault.services.deduplication import context_deduplicator
        from contextvault.services.validation import context_validator
        
        console.print(Panel.fit("⚙️ Automatic Context Extraction Settings", style="bold blue"))
        
        # Extraction patterns
        console.print("\n📝 [bold]Extraction Patterns:[/bold]")
        for context_type, patterns in context_extractor.extraction_patterns.items():
            console.print(f"  • {context_type}: {len(patterns)} patterns")
        
        # Deduplication settings
        console.print(f"\n🔄 [bold]Deduplication:[/bold]")
        console.print(f"  • Similarity threshold: {context_deduplicator.similarity_threshold}")
        
        # Validation settings
        console.print(f"\n✅ [bold]Validation:[/bold]")
        console.print(f"  • Min confidence: {context_validator.min_confidence_threshold}")
        console.print(f"  • Review threshold: {context_validator.review_threshold}")
        console.print(f"  • Valid threshold: {context_validator.valid_threshold}")
        
    except Exception as e:
        console.print(f"❌ Error getting settings: {e}")
