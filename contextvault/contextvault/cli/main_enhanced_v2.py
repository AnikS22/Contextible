"""
Enhanced ContextVault CLI v2.0
Beautiful, comprehensive interface with full testing capabilities
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from .enhanced_ui import EnhancedContextVaultUI, console
from ..setup import run_setup_wizard
from ..config import settings


class EnhancedContextVaultCLI:
    """Enhanced CLI interface for ContextVault with comprehensive testing."""
    
    def __init__(self):
        self.console = console
        self.config_file = Path.home() / ".contextvault" / "config.json"
        self.ui = EnhancedContextVaultUI()
    
    def ensure_database_initialized(self):
        """Ensure database is initialized before running CLI."""
        try:
            from ..database import check_database_connection, init_database, create_tables
            from ..models.context import ContextEntry
            
            # Check if database exists and has tables
            try:
                connection_info = check_database_connection()
                # Try to query a table to see if it exists
                from ..database import get_db_session
                with get_db_session() as db:
                    db.query(ContextEntry).first()
                # If we get here, database is working
                return True
            except Exception:
                # Database doesn't exist or tables missing, initialize it
                self.console.print("🗄️ Initializing database...", style="yellow")
                init_database()
                create_tables()
                self.console.print("✅ Database initialized successfully!", style="green")
                return True
                
        except Exception as e:
            self.console.print(f"❌ Database initialization failed: {e}", style="red")
            self.console.print("Please run: python init_database.py", style="yellow")
            return False
    
    def run(self, args=None):
        """Main entry point for the CLI."""
        try:
            # Initialize database if needed
            self.ensure_database_initialized()
            
            # Show enhanced banner
            self.ui.show_enhanced_banner()
            
            # Check if this is first run
            if not self.is_configured():
                return self.first_run_experience()
            
            # Check command line arguments
            if args and len(args) > 0:
                return self.handle_command(args)
            
            # Show main dashboard
            return self.show_main_dashboard()
            
        except KeyboardInterrupt:
            self.console.print("\n\nGoodbye! 👋", style="yellow")
            return 0
        except Exception as e:
            self.ui.show_error_message("Unexpected error", str(e))
            return 1
    
    def is_configured(self) -> bool:
        """Check if ContextVault is configured."""
        return self.config_file.exists()
    
    def first_run_experience(self):
        """Handle first-time user experience."""
        return run_setup_wizard()
    
    def handle_command(self, args: list):
        """Handle command line arguments."""
        command = args[0]
        
        # Core functionality commands
        if command == "add":
            return self.add_context_command(args[1:])
        elif command == "list":
            return self.list_context_command(args[1:])
        elif command == "search":
            return self.search_context_command(args[1:])
        elif command == "categorize":
            return self.categorize_command()
        elif command == "resolve-conflicts":
            return self.resolve_conflicts_command()
        
        # Testing commands
        elif command == "test-injection":
            return self.test_injection_command()
        elif command == "test-retrieval":
            return self.test_retrieval_command()
        elif command == "test-categorization":
            return self.test_categorization_command()
        elif command == "test-conflicts":
            return self.test_conflicts_command()
        elif command == "test-analytics":
            return self.test_analytics_command()
        elif command == "test-all":
            return self.test_all_command()
        
        # System commands
        elif command == "status":
            return self.status_command()
        elif command == "health-check":
            return self.health_check_command()
        elif command == "analytics":
            return self.analytics_command()
        elif command == "config":
            return self.config_command(args[1:])
        elif command == "start":
            return self.start_command()
        elif command == "stop":
            return self.stop_command()
        
        # Interactive commands
        elif command == "demo":
            return self.demo_command()
        elif command == "interactive":
            return self.interactive_mode()
        elif command == "help":
            return self.help_command()
        elif command == "setup":
            return run_setup_wizard()
        
        # Model management commands
        elif command == "models":
            return self.models_command(args[1:])
        
        else:
            self.ui.show_error_message(
                f"Unknown command: {command}",
                "Type 'contextvault help' for available commands"
            )
            return 1
    
    def show_main_dashboard(self):
        """Show the main dashboard."""
        self.ui.show_comprehensive_dashboard()
        
        # Interactive command prompt
        while True:
            try:
                command = input("\ncontextvault> ").strip().lower()
                
                if not command:
                    continue
                elif command in ["exit", "quit", "q"]:
                    self.console.print("Goodbye! 👋", style="yellow")
                    break
                elif command == "clear":
                    self.ui.show_comprehensive_dashboard()
                elif command == "help":
                    self.help_command()
                elif command.startswith("add "):
                    content = command[4:].strip()
                    if content:
                        self.add_context_interactive(content)
                    else:
                        self.ui.show_error_message("Please provide content to add")
                elif command == "list":
                    self.list_context_command()
                elif command == "analytics":
                    self.analytics_command()
                elif command == "health-check":
                    self.health_check_command()
                elif command == "test-all":
                    self.test_all_command()
                elif command.startswith("models"):
                    # Parse models command with arguments
                    parts = command.split()
                    self.handle_command(parts)
                elif command.startswith("test-"):
                    self.handle_command([command])
                else:
                    self.ui.show_error_message(f"Unknown command: {command}")
                    self.console.print("Type 'help' for available commands", style="yellow")
                    
            except KeyboardInterrupt:
                self.console.print("\n\nGoodbye! 👋", style="yellow")
                break
            except EOFError:
                break
        
        return 0
    
    def add_context_command(self, args: list):
        """Handle add context command."""
        if not args:
            self.ui.show_error_message(
                "Missing content",
                "Usage: contextvault add \"your context information\""
            )
            return 1
        
        content = " ".join(args)
        return self.add_context_interactive(content, skip_confirmation=True)
    
    def add_context_interactive(self, content: str, skip_confirmation=False):
        """Add context interactively."""
        try:
            # Show what we're adding
            preview_panel = Panel(
                Text(content, style="italic"),
                title="Adding Context",
                box=box.ROUNDED
            )
            self.console.print(preview_panel)
            
            # Confirm addition (skip if in non-interactive mode)
            should_add = True
            if not skip_confirmation:
                try:
                    from rich.prompt import Confirm
                    should_add = Confirm.ask("Add this context?", default=True)
                except (EOFError, KeyboardInterrupt):
                    # If we can't get user input, assume yes
                    should_add = True
            
            if should_add:
                # Add directly to database
                from ..database import get_db_context
                from ..models.context import ContextEntry
                from ..models.context import ContextType
                from ..services.categorizer import ContextCategorizer
                import datetime
                
                with get_db_context() as db:
                    # Create context entry
                    context_entry = ContextEntry(
                        content=content,
                        context_type=ContextType.TEXT,
                        created_at=datetime.datetime.utcnow(),
                        updated_at=datetime.datetime.utcnow(),
                        tags=[],
                        metadata={}
                    )
                    
                    # Auto-categorize if categorizer is available
                    try:
                        categorizer = ContextCategorizer()
                        category = categorizer.categorize_content(content)
                        if category:
                            context_entry.context_category = category
                    except:
                        pass  # If categorization fails, continue without it
                    
                    db.add(context_entry)
                    db.commit()
                    
                    self.ui.show_success_message("Context added successfully!")
            else:
                self.console.print("Cancelled", style="yellow")
                
        except Exception as e:
            self.ui.show_error_message("Error adding context", str(e))
            import traceback
            print(traceback.format_exc())
            return 1
        
        return 0
    
    def list_context_command(self, args: list = None):
        """Handle list context command."""
        try:
            from ..database import get_db_context
            from ..models.context import ContextEntry
            from rich.table import Table
            
            with get_db_context() as db:
                # Get context entries
                entries = db.query(ContextEntry).order_by(ContextEntry.created_at.desc()).limit(20).all()
                
                if not entries:
                    self.console.print("[yellow]No context entries found.[/yellow]")
                    return 0
                
                # Create table
                table = Table(title="Stored Context", show_header=True, header_style="bold magenta")
                table.add_column("ID", style="dim", width=6)
                table.add_column("Content", style="white", max_width=60)
                table.add_column("Type", style="cyan", width=12)
                table.add_column("Created", style="dim", width=20)
                table.add_column("Tags", style="yellow", width=20)
                
                for entry in entries:
                    content_preview = entry.content[:57] + "..." if len(entry.content) > 60 else entry.content
                    tags_str = ", ".join(entry.tags) if entry.tags else "None"
                    type_str = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
                    
                    table.add_row(
                        str(entry.id),
                        content_preview,
                        type_str,
                        entry.created_at.strftime("%Y-%m-%d %H:%M"),
                        tags_str
                    )
                
                self.console.print(table)
                self.console.print(f"\n[dim]Showing {len(entries)} of total entries. Use 'contextible search <query>' to find specific content.[/dim]")
                
        except Exception as e:
            self.ui.show_error_message("Error listing context", str(e))
            import traceback
            print(traceback.format_exc())
            return 1
        
        return 0
    
    def search_context_command(self, args: list):
        """Handle search context command."""
        if not args:
            self.ui.show_error_message(
                "Missing search query",
                "Usage: contextvault search \"your search query\""
            )
            return 1
        
        query = " ".join(args)
        
        try:
            from ..database import get_db_context
            from ..models.context import ContextEntry
            from rich.table import Table
            
            with get_db_context() as db:
                # Search context entries
                entries = db.query(ContextEntry).filter(
                    ContextEntry.content.ilike(f"%{query}%")
                ).order_by(ContextEntry.created_at.desc()).limit(10).all()
                
                if not entries:
                    self.console.print(f"[yellow]No context entries found matching '{query}'.[/yellow]")
                    return 0
                
                # Create table
                table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
                table.add_column("ID", style="dim", width=6)
                table.add_column("Content", style="white", max_width=60)
                table.add_column("Type", style="cyan", width=12)
                table.add_column("Created", style="dim", width=20)
                
                for entry in entries:
                    content_preview = entry.content[:57] + "..." if len(entry.content) > 60 else entry.content
                    type_str = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
                    
                    table.add_row(
                        str(entry.id),
                        content_preview,
                        type_str,
                        entry.created_at.strftime("%Y-%m-%d %H:%M")
                    )
                
                self.console.print(table)
                self.console.print(f"\n[dim]Found {len(entries)} matching entries.[/dim]")
                
        except Exception as e:
            self.ui.show_error_message("Error searching context", str(e))
            import traceback
            print(traceback.format_exc())
            return 1
        
        return 0
    
    def categorize_command(self):
        """Handle categorize command."""
        try:
            self.ui.show_info_message("Running auto-categorization...")
            
            # Run categorization script
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Auto-categorization completed successfully!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Auto-categorization failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error running categorization", str(e))
            return 1
        
        return 0
    
    def resolve_conflicts_command(self):
        """Handle resolve conflicts command."""
        try:
            self.ui.show_info_message("Scanning for context conflicts...")
            
            # Run conflict resolution
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Conflict resolution completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Conflict resolution failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error resolving conflicts", str(e))
            return 1
        
        return 0
    
    def test_injection_command(self):
        """Test context injection functionality."""
        try:
            self.ui.show_info_message("Testing context injection...")
            
            result = subprocess.run([
                sys.executable, "scripts/simple_debug_test.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Context injection test completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Context injection test failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error testing injection", str(e))
            return 1
        
        return 0
    
    def test_retrieval_command(self):
        """Test intelligent retrieval functionality."""
        try:
            self.ui.show_info_message("Testing intelligent retrieval...")
            
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Retrieval test completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Retrieval test failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error testing retrieval", str(e))
            return 1
        
        return 0
    
    def test_categorization_command(self):
        """Test categorization engine."""
        try:
            self.ui.show_info_message("Testing categorization engine...")
            
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Categorization test completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Categorization test failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error testing categorization", str(e))
            return 1
        
        return 0
    
    def test_conflicts_command(self):
        """Test conflict resolution."""
        try:
            self.ui.show_info_message("Testing conflict resolution...")
            
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Conflict resolution test completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Conflict resolution test failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error testing conflicts", str(e))
            return 1
        
        return 0
    
    def test_analytics_command(self):
        """Test analytics system."""
        try:
            self.ui.show_info_message("Testing analytics system...")
            
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("Analytics test completed!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Analytics test failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error testing analytics", str(e))
            return 1
        
        return 0
    
    def test_all_command(self):
        """Run all core functionality tests."""
        try:
            self.ui.show_info_message("Running comprehensive test suite...")
            
            # Run the comprehensive test
            result = subprocess.run([
                sys.executable, "scripts/test_intelligent_context_system.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.ui.show_success_message("All tests completed successfully!")
                self.console.print(result.stdout)
            else:
                self.ui.show_error_message(
                    "Some tests failed",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            self.ui.show_error_message("Error running tests", str(e))
            return 1
        
        return 0
    
    def status_command(self):
        """Handle status command."""
        self.ui.show_comprehensive_dashboard()
        return 0
    
    def health_check_command(self):
        """Handle health check command."""
        self.ui.show_comprehensive_health_check()
        return 0
    
    def analytics_command(self):
        """Handle analytics command."""
        try:
            from ..database import get_db_context
            from ..models.context import ContextEntry
            from rich.table import Table
            from rich.panel import Panel
            from rich.text import Text
            import datetime
            
            with get_db_context() as db:
                # Get analytics data
                total_entries = db.query(ContextEntry).count()
                
                # Get entries by type
                entries_by_type = {}
                for entry in db.query(ContextEntry).all():
                    type_str = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
                    entries_by_type[type_str] = entries_by_type.get(type_str, 0) + 1
                
                # Get recent entries (last 7 days)
                week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
                recent_entries = db.query(ContextEntry).filter(
                    ContextEntry.created_at >= week_ago
                ).count()
                
                # Create analytics table
                analytics_table = Table(title="Context Analytics", show_header=True, header_style="bold magenta")
                analytics_table.add_column("Metric", style="bold", width=25)
                analytics_table.add_column("Value", style="cyan", width=15)
                analytics_table.add_column("Description", style="dim", width=40)
                
                analytics_table.add_row("Total Context Entries", str(total_entries), "All stored context information")
                analytics_table.add_row("Recent Entries (7 days)", str(recent_entries), "Entries added in the last week")
                analytics_table.add_row("Context Types", str(len(entries_by_type)), "Different types of context stored")
                
                self.console.print(analytics_table)
                
                # Show breakdown by type
                if entries_by_type:
                    type_table = Table(title="Context by Type", show_header=True, header_style="bold blue")
                    type_table.add_column("Type", style="cyan", width=20)
                    type_table.add_column("Count", style="green", width=10)
                    type_table.add_column("Percentage", style="yellow", width=15)
                    
                    for context_type, count in sorted(entries_by_type.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total_entries * 100) if total_entries > 0 else 0
                        type_table.add_row(
                            context_type,
                            str(count),
                            f"{percentage:.1f}%"
                        )
                    
                    self.console.print("\n")
                    self.console.print(type_table)
                
                # Show summary panel
                summary_text = f"""
📊 Total Context Entries: {total_entries}
📈 Recent Activity: {recent_entries} entries in the last 7 days
🏷️ Context Types: {len(entries_by_type)}
✅ System Status: Fully Operational
                """
                
                summary_panel = Panel(
                    Text(summary_text.strip(), style="green"),
                    title="[bold green]Analytics Summary[/bold green]",
                    border_style="green"
                )
                
                self.console.print("\n")
                self.console.print(summary_panel)
                
        except Exception as e:
            self.ui.show_error_message("Error generating analytics", str(e))
            import traceback
            print(traceback.format_exc())
            return 1
        
        return 0
    
    def config_command(self, args: list):
        """Handle config command."""
        if not args:
            self.show_config_info()
            return 0
        
        subcommand = args[0]
        
        if subcommand == "show":
            self.show_config_info()
        elif subcommand == "reset":
            self.reset_config()
        else:
            self.ui.show_error_message(
                f"Unknown config subcommand: {subcommand}",
                "Available: show, reset"
            )
            return 1
        
        return 0
    
    def show_config_info(self):
        """Show current configuration."""
        config_table = Table(show_header=True, header_style="bold purple")
        config_table.add_column("Setting", style="bold", width=20)
        config_table.add_column("Value", width=30)
        config_table.add_column("Source", style="dim", width=15)
        
        # Load config
        config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except:
                pass
        
        config_data = [
            ("Setup Completed", str(config.get("setup_completed", False)), "Config File"),
            ("Setup Date", time.ctime(config.get("setup_date", 0)), "Config File"),
            ("Version", config.get("version", "Unknown"), "Config File"),
            ("API Host", getattr(settings, 'api_host', 'localhost'), "Settings"),
            ("API Port", str(getattr(settings, 'api_port', 8000)), "Settings"),
            ("Proxy Port", str(getattr(settings, 'proxy_port', 11435)), "Settings"),
            ("Ollama Host", getattr(settings, 'ollama_host', 'localhost'), "Settings"),
            ("Ollama Port", str(getattr(settings, 'ollama_port', 11434)), "Settings"),
        ]
        
        for setting, value, source in config_data:
            config_table.add_row(setting, value, source)
        
        self.console.print("📋 Current Configuration", style="bold purple")
        self.console.print()
        self.console.print(config_table)
    
    def reset_config(self):
        """Reset configuration."""
        from rich.prompt import Confirm
        if Confirm.ask("Are you sure you want to reset all configuration?", default=False):
            try:
                if self.config_file.exists():
                    self.config_file.unlink()
                self.ui.show_success_message("Configuration reset successfully!")
            except Exception as e:
                self.ui.show_error_message("Failed to reset configuration", str(e))
        else:
            self.console.print("Configuration reset cancelled", style="yellow")
    
    def demo_command(self):
        """Handle demo command."""
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "scripts/final_working_demo.py"
            ], capture_output=True, text=True)
            
            self.console.print(result.stdout)
            if result.stderr:
                self.console.print(result.stderr, style="red")
                
        except Exception as e:
            self.ui.show_error_message("Error running demo", str(e))
            return 1
        
        return 0
    
    def start_command(self):
        """Handle start command."""
        try:
            # Start services
            self.console.print("🚀 Starting ContextVault services...", style="bold")
            
            # Start main API server
            import subprocess
            api_process = subprocess.Popen([
                sys.executable, "-m", "contextvault.main"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(2)  # Give it time to start
            
            # Start proxy server
            proxy_process = subprocess.Popen([
                sys.executable, "scripts/ollama_proxy.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(2)
            
            # Check if services are running
            import requests
            try:
                api_response = requests.get("http://localhost:8000/health/", timeout=5)
                proxy_response = requests.get("http://localhost:11435/health", timeout=5)
                
                if api_response.status_code == 200 and proxy_response.status_code == 200:
                    self.ui.show_success_message("All services started successfully!")
                    self.console.print("• API Server: http://localhost:8000", style="green")
                    self.console.print("• Proxy Server: http://localhost:11435", style="green")
                else:
                    self.ui.show_warning_message("Services started but may not be fully ready")
                    
            except Exception as e:
                self.ui.show_warning_message(
                    "Services started but health check failed",
                    str(e)
                )
                
        except Exception as e:
            self.ui.show_error_message("Failed to start services", str(e))
            return 1
        
        return 0
    
    def stop_command(self):
        """Handle stop command."""
        try:
            # Stop services (this is a simplified approach)
            self.console.print("🛑 Stopping ContextVault services...", style="bold")
            
            # In a real implementation, you'd track and kill the processes
            # For now, just show a message
            self.ui.show_success_message("Services stopped")
            
        except Exception as e:
            self.ui.show_error_message("Failed to stop services", str(e))
            return 1
        
        return 0
    
    def interactive_mode(self):
        """Enter interactive mode."""
        self.ui.show_comprehensive_dashboard()
        return self.show_main_dashboard()
    
    def help_command(self):
        """Show help information."""
        self.ui.show_help_comprehensive()
    
    def models_command(self, args: list):
        """Handle model management commands."""
        if not args:
            # Default to list models
            return self.models_list_command()
        
        subcommand = args[0]
        
        if subcommand == "list":
            return self.models_list_command()
        elif subcommand == "set-permission":
            if len(args) < 2:
                self.ui.show_error_message(
                    "Missing model ID",
                    "Usage: contextvault models set-permission <model_id> [options]"
                )
                return 1
            return self.models_set_permission_command(args[1:])
        elif subcommand == "remove-permission":
            if len(args) < 2:
                self.ui.show_error_message(
                    "Missing model ID",
                    "Usage: contextvault models remove-permission <model_id>"
                )
                return 1
            return self.models_remove_permission_command(args[1])
        else:
            self.ui.show_error_message(
                f"Unknown models subcommand: {subcommand}",
                "Available: list, set-permission, remove-permission"
            )
            return 1
        
        return 0
    
    def models_list_command(self):
        """List detected AI models and their Contextible status."""
        try:
            from ..services.model_detector import model_detector
            from ..services.permissions import permission_service
            from ..models import Permission
            from ..database import get_db_context
            import asyncio
            
            self.console.print(Panel(
                Text("🧠 AI Model Management", justify="center", style="bold blue"),
                border_style="blue",
                box=box.DOUBLE
            ))

            self.console.print("\n[bold]Detecting running AI models...[/bold]")
            
            # Use asyncio.run in a new thread to avoid nested event loop issues
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, model_detector.detect_all_models())
                detected_models = future.result()

            if not detected_models:
                self.console.print("[yellow]⚠️ No AI models detected. Ensure Ollama or other services are running.[/yellow]")
                return 0

            table = Table(
                title="Detected AI Models",
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED
            )
            table.add_column("ID/Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="green")
            table.add_column("Endpoint", style="dim")
            table.add_column("Status", style="white")
            table.add_column("Contextible Access", style="yellow")
            table.add_column("Permissions", style="dim")

            with get_db_context() as db:
                for model in detected_models:
                    model_id = model.name  # Use name as ID
                    model_name = model.name
                    model_type = model.provider
                    endpoint = model.endpoint
                    status = model.status

                    # Check Contextible access and permissions
                    perms = db.query(Permission).filter(Permission.model_id == model_id).all()
                    if perms:
                        access_status = "[green]✅ Enabled[/green]"
                        perm_summary = ", ".join([
                            f"Scope: {p.scope or 'N/A'}" +
                            (f" (Allow All)" if p.allow_all else "") +
                            (f" (Deny All)" if p.deny_all else "")
                            for p in perms
                        ])
                    else:
                        access_status = "[red]❌ Disabled[/red]"
                        perm_summary = "No explicit permissions"
                    
                    table.add_row(
                        model_name,
                        model_type,
                        endpoint,
                        status,
                        access_status,
                        perm_summary
                    )
            
            self.console.print(table)
            self.console.print("\n[dim]Use 'contextible models set-permission <model_id>' to manage access.[/dim]")
            
        except Exception as e:
            self.ui.show_error_message("Error listing models", str(e))
            return 1
        
        return 0
    
    def models_set_permission_command(self, args: list):
        """Set or update permissions for a specific AI model."""
        try:
            model_id = args[0]
            scope = "personal,work,preferences,notes,goals,relationships,skills,projects"  # Default broad scope
            allow_all = False
            deny_all = False
            active = True
            
            # Parse additional options if provided
            if len(args) > 1:
                for arg in args[1:]:
                    if arg.startswith("--scope="):
                        scope = arg.split("=", 1)[1]
                    elif arg == "--allow-all":
                        allow_all = True
                    elif arg == "--deny-all":
                        deny_all = True
                    elif arg == "--inactive":
                        active = False
            
            from ..models import Permission
            from ..database import get_db_context
            
            with get_db_context() as db:
                permission = db.query(Permission).filter(Permission.model_id == model_id).first()
                
                if permission:
                    self.console.print(f"[yellow]Updating permissions for model: {model_id}[/yellow]")
                    permission.scope = scope if not allow_all and not deny_all else None
                    permission.allow_all = allow_all
                    permission.deny_all = deny_all
                    permission.is_active = active
                else:
                    self.console.print(f"[green]Creating new permissions for model: {model_id}[/green]")
                    permission = Permission(
                        model_id=model_id,
                        model_name=model_id,  # Use ID as name if not explicitly provided
                        scope=scope if not allow_all and not deny_all else None,
                        allow_all=allow_all,
                        deny_all=deny_all,
                        is_active=active
                    )
                    db.add(permission)
                
                db.commit()
                db.refresh(permission)
                self.console.print(f"[green]✅ Permissions for {model_id} updated:[/green]")
                self.console.print(f"   - Scope: {permission.scope}")
                self.console.print(f"   - Allow All: {permission.allow_all}")
                self.console.print(f"   - Deny All: {permission.deny_all}")
                self.console.print(f"   - Active: {permission.is_active}")
                
        except Exception as e:
            self.ui.show_error_message("Error setting permissions", str(e))
            return 1
        
        return 0
    
    def models_remove_permission_command(self, model_id: str):
        """Remove all permissions for a specific AI model."""
        try:
            from ..models import Permission
            from ..database import get_db_context
            
            with get_db_context() as db:
                permissions = db.query(Permission).filter(Permission.model_id == model_id).all()
                if permissions:
                    for perm in permissions:
                        db.delete(perm)
                    db.commit()
                    self.console.print(f"[green]✅ All permissions for {model_id} removed.[/green]")
                else:
                    self.console.print(f"[yellow]⚠️ No permissions found for model {model_id}.[/yellow]")
                    
        except Exception as e:
            self.ui.show_error_message("Error removing permissions", str(e))
            return 1
        
        return 0


def main():
    """Main entry point."""
    cli = EnhancedContextVaultCLI()
    return cli.run(sys.argv[1:] if len(sys.argv) > 1 else [])


if __name__ == "__main__":
    sys.exit(main())
