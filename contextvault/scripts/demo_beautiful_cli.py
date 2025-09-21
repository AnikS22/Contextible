#!/usr/bin/env python3
"""
Beautiful ContextVault CLI Demo
Showcases the complete Claude Code-inspired experience
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.cli.components import ContextVaultUI, console
from contextvault.setup.wizard import SetupWizard
from contextvault.services.health import health_service


def demo_welcome_experience():
    """Demo the welcome experience."""
    console.clear()
    console.print("🎬 ContextVault Beautiful CLI Demo", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    # Show welcome banner
    ContextVaultUI.show_welcome_banner()
    
    # Show setup options
    console.print("Let's get started.\n", style="bold")
    
    # Simulate setup choice
    console.print("Choose your setup preference:")
    console.print("❯ 1. Quick setup (recommended)")
    console.print("  2. Advanced configuration")
    console.print("  3. Import existing context")
    console.print("  4. Skip setup")
    console.print()
    console.print("Selected: Quick setup", style="green")
    console.print()


def demo_setup_process():
    """Demo the setup process."""
    console.print("🚀 Quick Setup - Let's get you running in 2 minutes!", style="bold")
    console.print()
    
    # Show setup steps
    steps = [
        ("Checking system requirements", "All system requirements met"),
        ("Initializing database", "Database initialized successfully"),
        ("Detecting Ollama installation", "Ollama detected with 4 models"),
        ("Testing Ollama connectivity", "Ollama is responding"),
        ("Starting ContextVault services", "All services are running"),
        ("Testing context injection", "Context injection system ready"),
        ("Adding sample context", "Sample context added"),
        ("Final configuration", "Configuration saved"),
    ]
    
    for step_name, result in steps:
        ContextVaultUI.show_progress_step(step_name, "In progress...", "working")
        import time
        time.sleep(0.3)
        ContextVaultUI.show_progress_step(step_name, result, "success")
    
    console.print()
    ContextVaultUI.show_success_message(
        "🎉 Setup Complete!",
        "ContextVault is ready to use!\n\n" +
        "Quick start:\n" +
        "• Add context: contextvault add \"your information\"\n" +
        "• View status: contextvault status\n" +
        "• Start services: contextvault start\n" +
        "• Get help: contextvault help"
    )


def demo_main_dashboard():
    """Demo the main dashboard."""
    console.clear()
    console.print("📊 Main Dashboard Experience", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    ContextVaultUI.show_status_dashboard()
    
    console.print()
    console.print("Interactive Commands Demo:", style="bold")
    console.print("• add \"I'm a Python developer\" - Add context")
    console.print("• list - View stored context")
    console.print("• status - System health check")
    console.print("• demo - Run interactive demo")
    console.print()


def demo_health_check():
    """Demo the health check."""
    console.print("🏥 Comprehensive Health Check", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    ContextVaultUI.show_health_check()


def demo_context_management():
    """Demo context management."""
    console.print("📚 Context Management Demo", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    # Show context preview
    sample_contexts = [
        {
            "content": "I am a software engineer who loves Python and machine learning. I work on AI infrastructure at Google.",
            "context_type": "preference",
            "created_at": "2025-09-20T10:30:00"
        },
        {
            "content": "I prefer detailed explanations and want to understand how systems work. I'm currently building ContextVault.",
            "context_type": "preference", 
            "created_at": "2025-09-20T10:35:00"
        },
        {
            "content": "I live in San Francisco and enjoy hiking on weekends. I have two cats named Luna and Pixel.",
            "context_type": "note",
            "created_at": "2025-09-20T10:40:00"
        }
    ]
    
    ContextVaultUI.show_context_preview(sample_contexts, limit=3)


def demo_ai_interaction():
    """Demo AI interaction with context."""
    console.print("🤖 AI Interaction with Context", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    # Show before/after comparison
    console.print("❌ WITHOUT ContextVault:", style="red")
    console.print("User: What do you know about me?")
    console.print("AI: I don't have any information about you. I'm a general-purpose AI assistant.")
    console.print()
    
    console.print("✅ WITH ContextVault:", style="green")
    console.print("User: What do you know about me?")
    console.print("AI: Based on our previous conversations, you are a software engineer at Google who loves Python and machine learning. You're currently building ContextVault, a system for giving AI models persistent memory. You live in San Francisco, enjoy hiking on weekends, and have two cats named Luna and Pixel. You prefer detailed explanations and want to understand how systems work.")
    console.print()
    
    ContextVaultUI.show_success_message(
        "ContextVault transforms generic AI responses into personalized conversations!"
    )


def demo_brand_identity():
    """Demo the brand identity."""
    console.print("🎨 ContextVault Brand Identity", style="bold purple")
    console.print("=" * 60)
    console.print()
    
    from contextvault.cli.components import show_brand_colors
    show_brand_colors()


def main():
    """Run the complete demo."""
    try:
        console.print("🎬 Welcome to the ContextVault Beautiful CLI Demo!", style="bold purple")
        console.print("This demo showcases the Claude Code-inspired interface")
        console.print()
        
        # Demo sections
        sections = [
            ("Welcome Experience", demo_welcome_experience),
            ("Setup Process", demo_setup_process),
            ("Main Dashboard", demo_main_dashboard),
            ("Health Check", demo_health_check),
            ("Context Management", demo_context_management),
            ("AI Interaction", demo_ai_interaction),
            ("Brand Identity", demo_brand_identity),
        ]
        
        for i, (name, demo_func) in enumerate(sections, 1):
            console.print(f"🎬 Section {i}: {name}", style="bold purple")
            console.print()
            demo_func()
            console.print()
            
            if i < len(sections):
                console.print("Press Enter to continue to the next section...", style="dim")
                input()
                console.clear()
        
        # Final message
        console.print("🎉 Demo Complete!", style="bold green")
        console.print("=" * 60)
        console.print()
        
        final_panel = console.Panel(
            console.Text("ContextVault Beautiful CLI Demo Complete!\n\n" +
                        "Key Features Demonstrated:\n" +
                        "✅ Beautiful welcome screen with ASCII art\n" +
                        "✅ Interactive setup wizard\n" +
                        "✅ Modern status dashboard\n" +
                        "✅ Comprehensive health checks\n" +
                        "✅ Context management interface\n" +
                        "✅ AI interaction with context injection\n" +
                        "✅ Consistent brand identity\n\n" +
                        "ContextVault now provides a premium, professional CLI experience\n" +
                        "that users will love to interact with!", style="white"),
            title="🎉 Demo Complete",
            border_style="green",
            box=console.box.DOUBLE
        )
        console.print(final_panel)
        
    except KeyboardInterrupt:
        console.print("\n\nDemo interrupted by user.", style="yellow")
    except Exception as e:
        console.print(f"\n\nDemo failed: {e}", style="red")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
