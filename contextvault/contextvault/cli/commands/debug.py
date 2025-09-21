"""
Debug CLI Commands for ContextVault
Provides debugging tools for context injection and system troubleshooting
"""

import click
import json
import time
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from ...services.injection_debugger import injection_debugger
from ...services.injection_monitor import injection_monitor
from ...models.context import ContextEntry
from ...database import get_db_context

console = Console()


@click.group()
def debug_group():
    """Debug tools for ContextVault."""
    pass


@debug_group.command()
@click.argument("prompt", type=str)
@click.option("--model", default="mistral:latest", help="Model to test with")
def injection(prompt: str, model: str):
    """Debug context injection pipeline for a specific prompt."""
    console.print(f"[bold blue]🔍 Debugging Context Injection[/bold blue]")
    console.print(f"Prompt: [italic]{prompt}[/italic]")
    console.print(f"Model: [italic]{model}[/italic]")
    console.print()
    
    # Start injection debug
    injection_id = injection_debugger.start_injection_debug(model, prompt)
    console.print(f"Injection ID: [green]{injection_id}[/green]")
    
    # Simulate the injection pipeline
    try:
        # Step 1: Context Retrieval
        console.print("[yellow]Step 1: Context Retrieval[/yellow]")
        with get_db_context() as db:
            from ...services.context_retrieval import ContextRetrievalService
            retrieval_service = ContextRetrievalService(db_session=db)
            context_result = retrieval_service.get_context_for_prompt(
                model_id=model,
                user_prompt=prompt,
                max_context_length=1000
            )
        
        if context_result.get("error"):
            console.print(f"[red]❌ Context retrieval failed: {context_result['error']}[/red]")
            injection_debugger.complete_injection_debug(False, context_result['error'])
            return
        
        context_entries = context_result.get("context_entries", [])
        relevance_scores = context_result.get("relevance_scores", {})
        
        console.print(f"Found [green]{len(context_entries)}[/green] relevant context entries")
        
        if context_entries:
            # Show context entries
            table = Table(title="Retrieved Context Entries")
            table.add_column("ID", style="cyan")
            table.add_column("Content", style="white")
            table.add_column("Type", style="green")
            table.add_column("Relevance", style="yellow")
            
            for entry in context_entries:
                entry_id = entry.get('id', 'unknown') if isinstance(entry, dict) else getattr(entry, 'id', 'unknown')
                content = entry.get('content', str(entry)) if isinstance(entry, dict) else (entry.content if hasattr(entry, 'content') else str(entry))
                ctx_type = entry.get('type', 'unknown') if isinstance(entry, dict) else str(entry.context_type)
                relevance = relevance_scores.get(entry_id, 0.0)
                
                table.add_row(
                    str(entry_id)[:8] + "...",
                    content[:50] + "..." if len(content) > 50 else content,
                    ctx_type,
                    f"{relevance:.2f}"
                )
            
            console.print(table)
            
            # Step 2: Template Selection
            console.print("\n[yellow]Step 2: Template Selection[/yellow]")
            from ...services.templates import template_manager
            current_template = template_manager.get_current_template()
            template_name = current_template.template_key if current_template else "default"
            template_content = current_template.template if current_template else "No template"
            
            console.print(f"Using template: [green]{template_name}[/green]")
            
            # Step 3: Context Formatting
            console.print("\n[yellow]Step 3: Context Formatting[/yellow]")
            context_strings = [entry.get('content', str(entry)) if isinstance(entry, dict) else (entry.content if hasattr(entry, 'content') else str(entry)) for entry in context_entries]
            
            # Format using the template
            formatted_context = template_manager.format_context_with_template(
                context_entries=context_strings,
                template_key=None  # Use current template
            )
            
            console.print(f"Formatted context ({len(formatted_context)} chars):")
            console.print(Panel(formatted_context, title="Formatted Context"))
            
            # Step 4: Prompt Assembly
            console.print("\n[yellow]Step 4: Prompt Assembly[/yellow]")
            final_prompt = f"{formatted_context}\n\nUser: {prompt}"
            
            console.print("Original prompt:")
            console.print(Panel(prompt, title="Original Prompt"))
            console.print("Final prompt with context:")
            console.print(Panel(final_prompt, title="Final Prompt"))
            
            console.print(f"\n[green]✅ Context injection pipeline completed successfully[/green]")
            console.print(f"Prompt length increased from [yellow]{len(prompt)}[/yellow] to [yellow]{len(final_prompt)}[/yellow] characters")
            
            # Complete debugging
            injection_debugger.log_context_retrieval(context_entries, relevance_scores)
            injection_debugger.log_template_selection(template_name, template_content)
            injection_debugger.log_context_formatting(formatted_context, context_entries)
            injection_debugger.log_prompt_assembly(final_prompt)
            injection_debugger.complete_injection_debug(True)
            
        else:
            console.print("[yellow]⚠️ No relevant context found[/yellow]")
            injection_debugger.complete_injection_debug(True, "No context found")
    
    except Exception as e:
        console.print(f"[red]❌ Debug failed: {e}[/red]")
        injection_debugger.complete_injection_debug(False, str(e))


@debug_group.command()
def last_request():
    """Show details of the last proxy request."""
    console.print("[bold blue]📋 Last Request Details[/bold blue]")
    
    recent_logs = injection_debugger.get_recent_injections(1)
    if not recent_logs:
        console.print("[yellow]No recent injection logs found[/yellow]")
        return
    
    log = recent_logs[0]
    
    # Show basic info
    console.print(f"Injection ID: [green]{log.injection_id}[/green]")
    console.print(f"Model: [green]{log.model_id}[/green]")
    console.print(f"Timestamp: [green]{time.ctime(log.timestamp)}[/green]")
    console.print(f"Success: [green]{'Yes' if log.injection_successful else 'No'}[/green]")
    console.print()
    
    # Show original vs final prompt
    console.print("[bold]Original Prompt:[/bold]")
    console.print(Panel(log.original_prompt, title="Original"))
    console.print()
    
    if log.final_prompt:
        console.print("[bold]Final Prompt:[/bold]")
        console.print(Panel(log.final_prompt, title="Final (with context)"))
        console.print()
    
    # Show context entries
    if log.context_entries_injected:
        console.print(f"[bold]Injected Context ({len(log.context_entries_injected)} entries):[/bold]")
        for i, entry in enumerate(log.context_entries_injected, 1):
            console.print(f"{i}. {entry.get('content', 'No content')}")
        console.print()
    
    # Show AI response if available
    if log.ai_response:
        console.print("[bold]AI Response:[/bold]")
        console.print(Panel(log.ai_response, title="Response"))
        console.print()
    
    # Show response analysis if available
    if log.response_analysis:
        analysis = log.response_analysis
        console.print("[bold]Response Analysis:[/bold]")
        console.print(f"Personalization Score: [yellow]{analysis.get('personalization_score', 0):.2f}[/yellow]")
        console.print(f"Mentions User Info: [yellow]{'Yes' if analysis.get('mentions_user_info') else 'No'}[/yellow]")
        console.print(f"Mentions Specific Details: [yellow]{'Yes' if analysis.get('mentions_specific_details') else 'No'}[/yellow]")


@debug_group.command()
@click.argument("query", type=str)
def context_match(query: str):
    """Show which context would be retrieved for a query."""
    console.print(f"[bold blue]🔍 Context Matching for Query[/bold blue]")
    console.print(f"Query: [italic]{query}[/italic]")
    console.print()
    
    try:
        with get_db_context() as db:
            from ...services.context_retrieval import ContextRetrievalService
            retrieval_service = ContextRetrievalService(db_session=db)
            context_result = retrieval_service.get_context_for_prompt(
                model_id="debug_model",
                user_prompt=query,
                max_context_length=1000
            )
        
        if context_result.get("error"):
            console.print(f"[red]❌ Context retrieval failed: {context_result['error']}[/red]")
            return
        
        context_entries = context_result.get("context_entries", [])
        relevance_scores = context_result.get("relevance_scores", {})
        
        console.print(f"Found [green]{len(context_entries)}[/green] matching context entries")
        console.print()
        
        if context_entries:
            # Show matching context
            table = Table(title="Matching Context Entries")
            table.add_column("Rank", style="cyan")
            table.add_column("Content", style="white")
            table.add_column("Type", style="green")
            table.add_column("Source", style="blue")
            table.add_column("Relevance", style="yellow")
            
            for i, entry in enumerate(context_entries, 1):
                entry_id = entry.get('id', 'unknown') if isinstance(entry, dict) else getattr(entry, 'id', 'unknown')
                content = entry.get('content', str(entry)) if isinstance(entry, dict) else (entry.content if hasattr(entry, 'content') else str(entry))
                ctx_type = entry.get('type', 'unknown') if isinstance(entry, dict) else str(entry.context_type)
                source = entry.get('source', 'unknown') if isinstance(entry, dict) else (entry.source if hasattr(entry, 'source') else 'unknown')
                relevance = relevance_scores.get(entry_id, 0.0)
                
                table.add_row(
                    str(i),
                    content[:60] + "..." if len(content) > 60 else content,
                    ctx_type,
                    source,
                    f"{relevance:.2f}"
                )
            
            console.print(table)
        else:
            console.print("[yellow]No matching context found[/yellow]")
    
    except Exception as e:
        console.print(f"[red]❌ Context matching failed: {e}[/red]")


@debug_group.command()
def effectiveness():
    """Show context usage statistics and effectiveness."""
    console.print("[bold blue]📊 Context Effectiveness Analysis[/bold blue]")
    console.print()
    
    # Get injection stats
    stats = injection_debugger.get_injection_stats()
    
    console.print("[bold]Injection Statistics:[/bold]")
    console.print(f"Total Injections: [green]{stats['total_injections']}[/green]")
    console.print(f"Successful Injections: [green]{stats['successful_injections']}[/green]")
    console.print(f"Success Rate: [yellow]{stats['success_rate']:.1%}[/yellow]")
    console.print(f"Average Context Entries: [yellow]{stats['average_context_entries']:.1f}[/yellow]")
    console.print()
    
    # Show template usage
    if stats['templates_used']:
        console.print("[bold]Template Usage:[/bold]")
        for template, count in stats['templates_used'].items():
            console.print(f"  {template}: [green]{count}[/green] times")
        console.print()
    
    # Get monitoring stats
    monitor_stats = injection_monitor.get_monitoring_stats()
    console.print("[bold]Monitoring Statistics:[/bold]")
    console.print(f"Total Events: [green]{monitor_stats['total_events']}[/green]")
    console.print(f"Active Injections: [green]{monitor_stats['active_injections']}[/green]")
    console.print()
    
    # Show recent activity
    recent_activity = monitor_stats['recent_activity']
    if recent_activity.get('event_counts'):
        console.print("[bold]Recent Activity:[/bold]")
        for event_type, count in recent_activity['event_counts'].items():
            console.print(f"  {event_type}: [green]{count}[/green] times")
        console.print()


@debug_group.command()
def monitor():
    """Show real-time injection monitoring dashboard."""
    console.print("[bold blue]📡 Real-time Injection Monitor[/bold blue]")
    console.print("Press Ctrl+C to stop monitoring")
    console.print()
    
    try:
        while True:
            # Clear screen
            console.clear()
            
            # Get dashboard data
            dashboard_data = injection_monitor.get_live_dashboard_data()
            
            console.print(f"[bold]ContextVault Injection Monitor - {time.strftime('%H:%M:%S')}[/bold]")
            console.print()
            
            # Show stats
            stats = dashboard_data['stats']
            console.print(f"Total Injections: [green]{stats['total_injections']}[/green]")
            console.print(f"Success Rate: [yellow]{stats['success_rate']:.1%}[/yellow]")
            console.print(f"Active Injections: [green]{dashboard_data['active_injections']}[/green]")
            console.print()
            
            # Show recent events
            console.print("[bold]Recent Events:[/bold]")
            for event in dashboard_data['recent_events'][-5:]:
                console.print(f"[{event['time']}] [cyan]{event['type']}[/cyan] - {event['model']}")
            
            console.print()
            console.print("[dim]Press Ctrl+C to stop...[/dim]")
            
            time.sleep(2)  # Update every 2 seconds
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


@debug_group.command()
@click.option("--limit", default=10, help="Number of recent logs to show")
def logs(limit: int):
    """Show recent injection debug logs."""
    console.print(f"[bold blue]📋 Recent Injection Logs (last {limit})[/bold blue]")
    console.print()
    
    recent_logs = injection_debugger.get_recent_injections(limit)
    
    if not recent_logs:
        console.print("[yellow]No injection logs found[/yellow]")
        return
    
    for i, log in enumerate(recent_logs, 1):
        status = "✅" if log.injection_successful else "❌"
        console.print(f"{i}. {status} [green]{log.injection_id}[/green] - {time.ctime(log.timestamp)}")
        console.print(f"   Model: [cyan]{log.model_id}[/cyan]")
        console.print(f"   Context Entries: [yellow]{len(log.context_entries_injected)}[/yellow]")
        console.print(f"   Prompt Length: [yellow]{len(log.original_prompt)}[/yellow] → [yellow]{len(log.final_prompt)}[/yellow]")
        if log.ai_response:
            console.print(f"   Response: [italic]{log.ai_response[:100]}...[/italic]")
        console.print()


# Add the debug group to the main CLI
def register_debug_commands(cli):
    """Register debug commands with the main CLI."""
    cli.add_command(debug_group, name="debug")
