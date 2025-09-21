"""
Beautiful CLI Components for ContextVault
Inspired by Claude Code's elegant terminal interface
"""

import sys
from typing import Any, Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.status import Status
from rich.syntax import Syntax
from rich import box
from rich.color import Color
from rich.style import Style

# ContextVault Brand Colors
BRAND_PURPLE = "#A892F5"
BRAND_BACKGROUND = "#FAFAFA"
BRAND_DARK_TEXT = "#000000"
BRAND_SECONDARY_TEXT = "#555555"
BRAND_SUCCESS = "#48BB78"
BRAND_WARNING = "#ED8936"
BRAND_ERROR = "#F56565"

# Create console instance
console = Console()

class ContextVaultUI:
    """Beautiful UI components for ContextVault CLI."""
    
    @staticmethod
    def show_welcome_banner():
        """Display the ContextVault welcome banner with ASCII art."""
        console.print("\n")
        
        # ASCII Art Logo
        logo = """
┌─────────────────────────────────────────────────────────┐
│                                                         │
│    ╔══════════════════════════════════════════════╗     │
│    ║                                              ║     │
│    ║   ██████╗ ██████╗ ███╗   ██╗████████╗███████╗║     │
│    ║  ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝║     │
│    ║  ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ║     │
│    ║  ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ║     │
│    ║  ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗║     │
│    ║   ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝║     │
│    ║                                              ║     │
│    ║  ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗   ║     │
│    ║  ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝   ║     │
│    ║  ██║   ██║███████║██║   ██║██║     ██║      ║     │
│    ║  ╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║      ║     │
│    ║   ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║      ║     │
│    ║    ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝      ║     │
│    ║                                              ║     │
│    ╚══════════════════════════════════════════════╝     │
│                                                         │
└─────────────────────────────────────────────────────────┘
        """
        
        # Welcome Panel
        welcome_text = Text("Welcome to ContextVault", style="bold " + BRAND_PURPLE)
        subtitle_text = Text("Local AI Memory & Context Layer", style=BRAND_SECONDARY_TEXT)
        
        console.print(Align.center(Text(logo, style=BRAND_PURPLE)))
        console.print("\n")
        console.print(Align.center(welcome_text))
        console.print(Align.center(subtitle_text))
        console.print("\n")
    
    @staticmethod
    def show_setup_options() -> str:
        """Show interactive setup options."""
        console.print("Let's get started.\n", style="bold")
        
        options = [
            ("1", "Quick setup (recommended)", "Automatically configure everything"),
            ("2", "Advanced configuration", "Customize settings and permissions"),
            ("3", "Import existing context", "Load context from files or other sources"),
            ("4", "Skip setup", "Use default settings")
        ]
        
        # Create options table
        table = Table(show_header=False, box=box.MINIMAL, padding=(0, 1))
        table.add_column("Option", style=BRAND_PURPLE, width=8)
        table.add_column("Description", style="bold", width=25)
        table.add_column("Details", style=BRAND_SECONDARY_TEXT, width=40)
        
        for option, desc, details in options:
            table.add_row(option, desc, details)
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "Choose your setup preference",
            choices=["1", "2", "3", "4"],
            default="1",
            show_choices=False
        )
        
        return choice
    
    @staticmethod
    def show_progress_step(step: str, description: str, status: str = "working"):
        """Show a progress step with appropriate styling."""
        if status == "working":
            icon = "⏳"
            style = BRAND_WARNING
        elif status == "success":
            icon = "✅"
            style = BRAND_SUCCESS
        elif status == "error":
            icon = "❌"
            style = BRAND_ERROR
        else:
            icon = "ℹ️"
            style = BRAND_PURPLE
        
        console.print(f"{icon} {step}: {description}", style=style)
    
    @staticmethod
    def show_status_dashboard():
        """Show the main status dashboard."""
        console.clear()
        
        # Header
        header = Panel(
            Text("ContextVault - Local AI Memory", style="bold " + BRAND_PURPLE),
            box=box.DOUBLE,
            style=BRAND_PURPLE
        )
        console.print(header)
        console.print()
        
        # Status indicators
        status_table = Table(show_header=False, box=box.MINIMAL)
        status_table.add_column("Service", style="bold", width=15)
        status_table.add_column("Status", width=10)
        status_table.add_column("Details", style=BRAND_SECONDARY_TEXT, width=30)
        
        # Mock status data - in real implementation, this would be dynamic
        status_table.add_row("API Server", "✅ Running", "Port 8000")
        status_table.add_row("Proxy", "✅ Running", "Port 11435")
        status_table.add_row("Ollama", "✅ Connected", "Port 11434")
        status_table.add_row("Database", "✅ Healthy", "170 entries")
        
        console.print(status_table)
        console.print()
        
        # Quick stats
        stats_panel = Panel(
            Text("Context entries: 170 | Models configured: 4", style=BRAND_SECONDARY_TEXT),
            title="Quick Stats",
            box=box.ROUNDED
        )
        console.print(stats_panel)
        console.print()
        
        # Main commands
        commands_table = Table(show_header=False, box=box.MINIMAL)
        commands_table.add_column("Command", style=BRAND_PURPLE, width=12)
        commands_table.add_column("Description", width=40)
        
        commands = [
            ("add", "Add new context entry"),
            ("list", "View stored context"),
            ("search", "Find relevant context"),
            ("config", "Manage settings"),
            ("status", "System health check"),
            ("demo", "Run interactive demo")
        ]
        
        for cmd, desc in commands:
            commands_table.add_row(cmd, desc)
        
        console.print("Commands:", style="bold")
        console.print(commands_table)
        console.print()
        console.print("Type 'contextvault help' for full command list.", style=BRAND_SECONDARY_TEXT)
    
    @staticmethod
    def show_health_check():
        """Show comprehensive health check results."""
        console.print("🔍 System Health Check", style="bold " + BRAND_PURPLE)
        console.print()
        
        # Create health check table
        health_table = Table(show_header=True, header_style="bold " + BRAND_PURPLE)
        health_table.add_column("Component", style="bold", width=20)
        health_table.add_column("Status", width=12)
        health_table.add_column("Details", width=40)
        health_table.add_column("Response Time", width=15)
        
        # Mock health data - in real implementation, this would be dynamic
        health_data = [
            ("API Server", "✅ Healthy", "Responding on port 8000", "12ms"),
            ("Ollama Proxy", "✅ Healthy", "Forwarding requests", "8ms"),
            ("Ollama Core", "✅ Healthy", "Models loaded", "45ms"),
            ("Database", "✅ Healthy", "170 entries, 0 errors", "3ms"),
            ("Context Retrieval", "✅ Healthy", "5 entries retrieved", "25ms"),
            ("Template System", "✅ Healthy", "8 templates available", "1ms"),
            ("MCP Integration", "⚠️ Partial", "Calendar connected, Drive pending", "N/A"),
        ]
        
        for component, status, details, response_time in health_data:
            health_table.add_row(component, status, details, response_time)
        
        console.print(health_table)
        console.print()
        
        # Overall status
        overall_panel = Panel(
            Text("Overall System Status: ✅ HEALTHY", style="bold " + BRAND_SUCCESS),
            title="Summary",
            box=box.ROUNDED
        )
        console.print(overall_panel)
    
    @staticmethod
    def show_context_preview(context_entries: List[Dict[str, Any]], limit: int = 5):
        """Show a preview of context entries."""
        console.print(f"📚 Context Preview (showing {min(limit, len(context_entries))} of {len(context_entries)})", style="bold " + BRAND_PURPLE)
        console.print()
        
        for i, entry in enumerate(context_entries[:limit]):
            # Create entry panel
            content_preview = entry.get('content', '')[:100] + "..." if len(entry.get('content', '')) > 100 else entry.get('content', '')
            
            entry_panel = Panel(
                Text(content_preview, style=BRAND_SECONDARY_TEXT),
                title=f"[{entry.get('context_type', 'unknown')}] Entry {i+1}",
                subtitle=f"Created: {entry.get('created_at', 'Unknown')}",
                box=box.ROUNDED
            )
            console.print(entry_panel)
            console.print()
    
    @staticmethod
    def show_success_message(message: str, details: Optional[str] = None):
        """Show a success message with styling."""
        success_panel = Panel(
            Text(message, style="bold " + BRAND_SUCCESS),
            subtitle=details if details else None,
            box=box.DOUBLE,
            style=BRAND_SUCCESS
        )
        console.print(success_panel)
    
    @staticmethod
    def show_error_message(message: str, details: Optional[str] = None):
        """Show an error message with styling."""
        error_panel = Panel(
            Text(message, style="bold " + BRAND_ERROR),
            subtitle=details if details else None,
            box=box.DOUBLE,
            style=BRAND_ERROR
        )
        console.print(error_panel)
    
    @staticmethod
    def show_warning_message(message: str, details: Optional[str] = None):
        """Show a warning message with styling."""
        warning_panel = Panel(
            Text(message, style="bold " + BRAND_WARNING),
            subtitle=details if details else None,
            box=box.DOUBLE,
            style=BRAND_WARNING
        )
        console.print(warning_panel)
    
    @staticmethod
    def show_loading_spinner(message: str):
        """Show a loading spinner."""
        with Status(message, spinner="dots"):
            return True
    
    @staticmethod
    def show_progress_bar(total: int, description: str = "Processing"):
        """Show a progress bar."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(description, total=total)
            return progress, task


def get_terminal_width() -> int:
    """Get the current terminal width."""
    try:
        return console.size.width
    except:
        return 80


def clear_screen():
    """Clear the terminal screen."""
    console.clear()


def pause_for_user():
    """Pause and wait for user input."""
    console.print("\nPress Enter to continue...", style=BRAND_SECONDARY_TEXT)
    input()


def show_brand_colors():
    """Display the ContextVault brand color palette."""
    console.print("🎨 ContextVault Brand Colors", style="bold " + BRAND_PURPLE)
    console.print()
    
    colors_table = Table(show_header=True, header_style="bold " + BRAND_PURPLE)
    colors_table.add_column("Color", width=15)
    colors_table.add_column("Hex", width=10)
    colors_table.add_column("Usage", width=30)
    colors_table.add_column("Sample", width=20)
    
    color_samples = [
        ("Primary Purple", BRAND_PURPLE, "Brand accent, highlights", "██████████"),
        ("Background", BRAND_BACKGROUND, "Main background", "██████████"),
        ("Dark Text", BRAND_DARK_TEXT, "Primary text", "██████████"),
        ("Secondary Text", BRAND_SECONDARY_TEXT, "Secondary text", "██████████"),
        ("Success", BRAND_SUCCESS, "Success states", "██████████"),
        ("Warning", BRAND_WARNING, "Warning states", "██████████"),
        ("Error", BRAND_ERROR, "Error states", "██████████"),
    ]
    
    for name, hex_color, usage, sample in color_samples:
        colors_table.add_row(
            name,
            hex_color,
            usage,
            Text(sample, style=hex_color)
        )
    
    console.print(colors_table)
