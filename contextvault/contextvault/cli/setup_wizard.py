"""Interactive Setup Wizard for ContextVault."""

import sys
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.text import Text
from rich import box

from ..services.model_detector import model_detector
from ..database import init_database
from ..config import settings


class SetupWizard:
    """Interactive setup wizard for first-time users."""
    
    def __init__(self):
        self.console = Console()
        self.setup_config = {}
        
    def show_welcome(self):
        """Show welcome screen with ASCII art."""
        welcome_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██████╗ ██████╗ ███╗   ██╗████████╗███████╗██╗   ██╗████████╗██╗██████╗ ██╗     ║
║ ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝██║   ██║╚══██╔══╝██║██╔══██╗██║     ║
║ ██║     ██║   ██║██╔██╗ ██║   ██║   █████╗  ██║   ██║   ██║   ██║██████╔╝██║     ║
║ ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══╝  ╚██╗ ██╔╝   ██║   ██║██╔══██╗██║     ║
║ ╚██████╗╚██████╔╝██║ ╚████║   ██║   ███████╗ ╚████╔╝    ██║   ██║██║  ██║███████╗║
║  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝  ╚═══╝     ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝║
║                                                                              ║
║                    🧠 AI Memory & Context Layer 🧠                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        
        self.console.print(Panel(
            welcome_text,
            title="[bold blue]Welcome to Contextible![/bold blue]",
            subtitle="[dim]Transform your AI models with persistent memory[/dim]",
            border_style="blue",
            padding=(1, 2)
        ))
        
        self.console.print("\n[bold green]✨ What is Contextible?[/bold green]")
        self.console.print("Contextible gives your local AI models persistent memory and personalization.")
        self.console.print("Your AI will remember your preferences, personal info, and context across conversations.")
        self.console.print()
    
    def show_setup_options(self):
        """Show setup options menu."""
        options_text = """
Choose your setup preference:

[bold blue]1.[/bold blue] Quick setup (recommended)
   • Auto-detect AI models
   • Enable context injection
   • Add sample context
   • Ready to use in 2 minutes

[bold blue]2.[/bold blue] Advanced configuration
   • Custom model configuration
   • Permission management
   • Database setup
   • For power users

[bold blue]3.[/bold blue] Import existing context
   • Import from CSV/JSON
   • Migrate from other tools
   • Bulk context import

[bold blue]4.[/bold blue] Skip setup
   • Use default settings
   • Configure later
        """
        
        self.console.print(Panel(
            options_text,
            title="[bold]Setup Options[/bold]",
            border_style="blue"
        ))
        
        choice = Prompt.ask(
            "Select setup option",
            choices=["1", "2", "3", "4"],
            default="1"
        )
        
        return choice
    
    async def quick_setup(self):
        """Perform quick setup."""
        self.console.print("\n[bold green]🚀 Quick Setup Starting...[/bold green]")
        
        # Step 1: Initialize database
        self.console.print("\n[bold]Step 1/4:[/bold] Initializing database...")
        try:
            init_database()
            self.console.print("✅ Database initialized successfully")
        except Exception as e:
            self.console.print(f"❌ Database initialization failed: {e}")
            return False
        
        # Step 2: Detect AI models
        self.console.print("\n[bold]Step 2/4:[/bold] Detecting AI models...")
        try:
            models = await model_detector.detect_all_models()
            if models:
                self.console.print(f"✅ Found {len(models)} AI models")
                self._show_detected_models(models)
            else:
                self.console.print("⚠️  No AI models detected")
                self.console.print("   Make sure Ollama or other AI services are running")
        except Exception as e:
            self.console.print(f"❌ Model detection failed: {e}")
            return False
        
        # Step 3: Configure context injection
        self.console.print("\n[bold]Step 3/4:[/bold] Configuring context injection...")
        if models:
            enable_injection = Confirm.ask("Enable context injection for detected models?")
            if enable_injection:
                for model in models:
                    model.context_injection_enabled = True
                self.console.print("✅ Context injection enabled for all models")
        
        # Step 4: Add sample context
        self.console.print("\n[bold]Step 4/4:[/bold] Adding sample context...")
        add_sample = Confirm.ask("Add sample personal context to get started?")
        if add_sample:
            self._add_sample_context()
        
        self.console.print("\n[bold green]🎉 Quick Setup Complete![/bold green]")
        self.console.print("Your AI models now have persistent memory!")
        return True
    
    def _show_detected_models(self, models):
        """Show detected models in a table."""
        table = Table(title="Detected AI Models", box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Endpoint", style="green")
        table.add_column("Status", style="yellow")
        
        for model in models:
            status_icon = "🟢" if model.status == "running" else "🔴"
            table.add_row(
                model.name,
                model.provider,
                model.endpoint,
                f"{status_icon} {model.status}"
            )
        
        self.console.print(table)
    
    def _add_sample_context(self):
        """Add sample context to the database."""
        sample_contexts = [
            "I am a software developer who loves Python and machine learning.",
            "I prefer working from home and I'm most productive in the morning.",
            "I have two cats named Luna and Pixel who love to sit on my keyboard.",
            "My favorite programming languages are Python, JavaScript, and Go.",
            "I enjoy hiking on weekends and I'm allergic to peanuts."
        ]
        
        try:
            from ..database import get_db_context
            from ..models.context import ContextEntry, ContextSource, ContextCategory
            
            with get_db_context() as db:
                for content in sample_contexts:
                    entry = ContextEntry(
                        content=content,
                        context_type="personal_info",
                        context_source=ContextSource.MANUAL,
                        context_category=ContextCategory.PERSONAL_INFO,
                        confidence_score=1.0,
                        tags=["sample", "setup"]
                    )
                    db.add(entry)
                
                db.commit()
            
            self.console.print(f"✅ Added {len(sample_contexts)} sample context entries")
            
        except Exception as e:
            self.console.print(f"❌ Failed to add sample context: {e}")
    
    async def advanced_setup(self):
        """Perform advanced setup."""
        self.console.print("\n[bold green]⚙️ Advanced Setup[/bold green]")
        self.console.print("Advanced configuration options coming soon!")
        return True
    
    def import_context(self):
        """Import existing context."""
        self.console.print("\n[bold green]📥 Import Context[/bold green]")
        self.console.print("Context import options coming soon!")
        return True
    
    def skip_setup(self):
        """Skip setup with default settings."""
        self.console.print("\n[bold yellow]⏭️ Skipping Setup[/bold yellow]")
        self.console.print("Using default configuration...")
        
        try:
            init_database()
            self.console.print("✅ Database initialized with default settings")
            return True
        except Exception as e:
            self.console.print(f"❌ Setup failed: {e}")
            return False
    
    async def run(self) -> bool:
        """Run the complete setup wizard."""
        try:
            self.show_welcome()
            choice = self.show_setup_options()
            
            if choice == "1":
                return await self.quick_setup()
            elif choice == "2":
                return await self.advanced_setup()
            elif choice == "3":
                return self.import_context()
            elif choice == "4":
                return self.skip_setup()
            
            return False
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Setup cancelled by user[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"\n[red]Setup failed: {e}[/red]")
            return False


async def run_setup_wizard() -> bool:
    """Run the setup wizard."""
    wizard = SetupWizard()
    return await wizard.run()


if __name__ == "__main__":
    success = asyncio.run(run_setup_wizard())
    sys.exit(0 if success else 1)
