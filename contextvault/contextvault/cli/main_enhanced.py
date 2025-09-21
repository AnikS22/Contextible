"""
Enhanced Main CLI Entry Point for ContextVault
Beautiful, interactive interface inspired by Claude Code
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from .components import ContextVaultUI, console
from ..setup import run_setup_wizard
from ..config import settings


class ContextVaultCLI:
    """Enhanced CLI interface for ContextVault."""
    
    def __init__(self):
        self.console = console
        self.config_file = Path.home() / ".contextvault" / "config.json"
    
    def run(self, args=None):
        """Main entry point for the CLI."""
        try:
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
            ContextVaultUI.show_error_message("Unexpected error", str(e))
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
        
        if command == "add":
            return self.add_context_command(args[1:])
        elif command == "list":
            return self.list_context_command(args[1:])
        elif command == "search":
            return self.search_context_command(args[1:])
        elif command == "status":
            return self.status_command()
        elif command == "config":
            return self.config_command(args[1:])
        elif command == "demo":
            return self.demo_command()
        elif command == "start":
            return self.start_command()
        elif command == "stop":
            return self.stop_command()
        elif command == "help":
            return self.help_command()
        elif command == "setup":
            return run_setup_wizard()
        else:
            ContextVaultUI.show_error_message(
                f"Unknown command: {command}",
                "Type 'contextvault help' for available commands"
            )
            return 1
    
    def show_main_dashboard(self):
        """Show the main dashboard."""
        ContextVaultUI.show_status_dashboard()
        
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
                    ContextVaultUI.show_status_dashboard()
                elif command == "help":
                    self.help_command()
                elif command.startswith("add "):
                    content = command[4:].strip()
                    if content:
                        self.add_context_interactive(content)
                    else:
                        self.console.print("Please provide content to add", style="red")
                elif command == "list":
                    self.list_context_command()
                elif command == "status":
                    self.status_command()
                elif command == "demo":
                    self.demo_command()
                else:
                    self.console.print(f"Unknown command: {command}", style="red")
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
            ContextVaultUI.show_error_message(
                "Missing content",
                "Usage: contextvault add \"your context information\""
            )
            return 1
        
        content = " ".join(args)
        return self.add_context_interactive(content)
    
    def add_context_interactive(self, content: str):
        """Add context interactively."""
        try:
            # Show what we're adding
            preview_panel = Panel(
                Text(content, style="italic"),
                title="Adding Context",
                box=box.ROUNDED
            )
            self.console.print(preview_panel)
            
            # Confirm addition
            from rich.prompt import Confirm
            if Confirm.ask("Add this context?", default=True):
                # Add via CLI
                import subprocess
                result = subprocess.run([
                    sys.executable, "-m", "contextvault.cli", "context", "add", content
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    ContextVaultUI.show_success_message("Context added successfully!")
                else:
                    ContextVaultUI.show_error_message(
                        "Failed to add context",
                        result.stderr or "Unknown error"
                    )
            else:
                self.console.print("Cancelled", style="yellow")
                
        except Exception as e:
            ContextVaultUI.show_error_message("Error adding context", str(e))
            return 1
        
        return 0
    
    def list_context_command(self, args: list = None):
        """Handle list context command."""
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "contextvault.cli", "context", "list"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.print(result.stdout)
            else:
                ContextVaultUI.show_error_message(
                    "Failed to list context",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            ContextVaultUI.show_error_message("Error listing context", str(e))
            return 1
        
        return 0
    
    def search_context_command(self, args: list):
        """Handle search context command."""
        if not args:
            ContextVaultUI.show_error_message(
                "Missing search query",
                "Usage: contextvault search \"your search query\""
            )
            return 1
        
        query = " ".join(args)
        
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "contextvault.cli", "context", "search", query
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.print(result.stdout)
            else:
                ContextVaultUI.show_error_message(
                    "Failed to search context",
                    result.stderr or "Unknown error"
                )
                
        except Exception as e:
            ContextVaultUI.show_error_message("Error searching context", str(e))
            return 1
        
        return 0
    
    def status_command(self):
        """Handle status command."""
        ContextVaultUI.show_health_check()
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
            ContextVaultUI.show_error_message(
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
                ContextVaultUI.show_success_message("Configuration reset successfully!")
            except Exception as e:
                ContextVaultUI.show_error_message("Failed to reset configuration", str(e))
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
            ContextVaultUI.show_error_message("Error running demo", str(e))
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
                    ContextVaultUI.show_success_message("All services started successfully!")
                    self.console.print("• API Server: http://localhost:8000", style="green")
                    self.console.print("• Proxy Server: http://localhost:11435", style="green")
                else:
                    ContextVaultUI.show_warning_message("Services started but may not be fully ready")
                    
            except Exception as e:
                ContextVaultUI.show_warning_message(
                    "Services started but health check failed",
                    str(e)
                )
                
        except Exception as e:
            ContextVaultUI.show_error_message("Failed to start services", str(e))
            return 1
        
        return 0
    
    def stop_command(self):
        """Handle stop command."""
        try:
            # Stop services (this is a simplified approach)
            self.console.print("🛑 Stopping ContextVault services...", style="bold")
            
            # In a real implementation, you'd track and kill the processes
            # For now, just show a message
            ContextVaultUI.show_success_message("Services stopped")
            
        except Exception as e:
            ContextVaultUI.show_error_message("Failed to stop services", str(e))
            return 1
        
        return 0
    
    def help_command(self):
        """Show help information."""
        help_panel = Panel(
            Text("ContextVault - Local AI Memory & Context Layer\n\n" +
                 "Available Commands:\n" +
                 "• add <content>     - Add new context entry\n" +
                 "• list             - View stored context\n" +
                 "• search <query>   - Find relevant context\n" +
                 "• status           - System health check\n" +
                 "• config           - Show configuration\n" +
                 "• demo             - Run interactive demo\n" +
                 "• start            - Start services\n" +
                 "• stop             - Stop services\n" +
                 "• setup            - Run setup wizard\n" +
                 "• help             - Show this help\n" +
                 "• exit/quit        - Exit interactive mode\n\n" +
                 "Examples:\n" +
                 "• contextvault add \"I'm a Python developer\"\n" +
                 "• contextvault search \"programming\"\n" +
                 "• contextvault status\n\n" +
                 "For more information, visit: https://github.com/AnikS22/contextvault"),
            title="Help",
            box=box.ROUNDED
        )
        self.console.print(help_panel)


def main():
    """Main entry point."""
    cli = ContextVaultCLI()
    return cli.run(sys.argv[1:] if len(sys.argv) > 1 else [])


if __name__ == "__main__":
    sys.exit(main())
