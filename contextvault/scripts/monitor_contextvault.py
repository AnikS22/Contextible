#!/usr/bin/env python3
"""
Real-time ContextVault monitoring script
Shows what's being stored as you chat with AI models
"""

import time
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

def get_context_stats():
    """Get current context statistics"""
    try:
        response = requests.get("http://localhost:8000/api/context/stats/summary")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"total_entries": 0, "recent_entries": 0}

def get_recent_entries():
    """Get recent context entries"""
    try:
        response = requests.get("http://localhost:8000/api/context/?limit=5")
        if response.status_code == 200:
            return response.json().get("entries", [])
    except:
        pass
    return []

def create_monitor_table():
    """Create the monitoring table"""
    stats = get_context_stats()
    recent = get_recent_entries()
    
    table = Table(title="🔍 ContextVault Real-Time Monitor")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Context Entries", str(stats.get("total_entries", 0)))
    table.add_row("Recent Entries (24h)", str(stats.get("recent_entries", 0)))
    table.add_row("ContextVault Status", "🟢 Running" if stats.get("total_entries", 0) > 0 else "🔴 Not Connected")
    
    if recent:
        table.add_row("", "")
        table.add_row("📝 Recent Context:", "")
        for entry in recent[:3]:
            content = entry.get("content", "")[:50] + "..." if len(entry.get("content", "")) > 50 else entry.get("content", "")
            source = entry.get("source", "unknown")
            table.add_row(f"  • {source}", content)
    
    return table

def main():
    """Main monitoring loop"""
    console.print(Panel.fit("🔍 ContextVault Real-Time Monitor", style="bold blue"))
    console.print("This will show what ContextVault is learning as you chat with AI models.")
    console.print("Press Ctrl+C to stop monitoring.\n")
    
    try:
        with Live(create_monitor_table(), refresh_per_second=2, console=console) as live:
            while True:
                live.update(create_monitor_table())
                time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n👋 Monitoring stopped.")

if __name__ == "__main__":
    main()
