"""CLI commands for managing context injection templates."""

import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, '.')

from contextvault.services.templates import template_manager, TEMPLATES

console = Console()


@click.group()
def templates():
    """Manage context injection templates."""
    pass


@templates.command()
def list():
    """List all available templates."""
    console.print("[bold blue]Available Context Injection Templates[/bold blue]")
    console.print("=" * 60)
    
    table = Table(title="Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Strength", justify="center")
    table.add_column("Description", style="green")
    
    for name, template in TEMPLATES.items():
        strength_color = "green" if template.strength >= 8 else "yellow" if template.strength >= 6 else "red"
        strength_display = f"[{strength_color}]{template.strength}/10[/{strength_color}]"
        
        table.add_row(
            name,
            template.template_type.value,
            strength_display,
            template.description
        )
    
    console.print(table)
    
    # Show current template
    current = template_manager.current_template
    current_template = template_manager.get_template(current)
    console.print(Panel(
        f"Current Active Template: [bold cyan]{current}[/bold cyan]\n"
        f"Type: {current_template.template_type.value}\n"
        f"Strength: {current_template.strength}/10\n"
        f"Description: {current_template.description}",
        title="Current Template"
    ))


@templates.command()
@click.argument('template_name')
def show(template_name):
    """Show details of a specific template."""
    if template_name not in TEMPLATES:
        console.print(f"❌ Template '{template_name}' not found", style="red")
        console.print("Available templates:", style="yellow")
        for name in TEMPLATES.keys():
            console.print(f"  • {name}")
        return
    
    template = TEMPLATES[template_name]
    
    console.print(Panel(
        f"[bold cyan]{template.name}[/bold cyan]\n\n"
        f"Type: {template.template_type.value}\n"
        f"Strength: {template.strength}/10\n"
        f"Description: {template.description}\n\n"
        f"Use Cases:\n" + "\n".join([f"  • {use_case}" for use_case in template.use_cases]) + "\n\n"
        f"Template:\n{template.template}",
        title=f"Template: {template_name}"
    ))


@templates.command()
@click.argument('template_name')
def set(template_name):
    """Set the active template for context injection."""
    if template_name not in TEMPLATES:
        console.print(f"❌ Template '{template_name}' not found", style="red")
        console.print("Available templates:", style="yellow")
        for name in TEMPLATES.keys():
            console.print(f"  • {name}")
        return
    
    success = template_manager.set_current_template(template_name)
    if success:
        template = TEMPLATES[template_name]
        console.print(f"✅ Active template set to: [bold cyan]{template_name}[/bold cyan]")
        console.print(f"   Type: {template.template_type.value}")
        console.print(f"   Strength: {template.strength}/10")
        console.print(f"   Description: {template.description}")
    else:
        console.print(f"❌ Failed to set template '{template_name}'", style="red")


@templates.command()
def current():
    """Show the currently active template."""
    current = template_manager.current_template
    template = template_manager.get_template(current)
    
    console.print(Panel(
        f"[bold cyan]{template.name}[/bold cyan]\n\n"
        f"Type: {template.template_type.value}\n"
        f"Strength: {template.strength}/10\n"
        f"Description: {template.description}",
        title="Current Active Template"
    ))


@templates.command()
@click.option('--context', '-c', multiple=True, help='Context entries to test with')
@click.option('--prompt', '-p', default="What do you know about me?", help='Test prompt')
@click.argument('template_name')
def test(template_name, context, prompt):
    """Test a template with sample context and prompt."""
    if template_name not in TEMPLATES:
        console.print(f"❌ Template '{template_name}' not found", style="red")
        return
    
    # Use provided context or default
    if not context:
        context = [
            "I am a software engineer who loves Python and testing",
            "I prefer detailed explanations and want to understand how systems work",
            "I built ContextVault to give local AI models persistent memory"
        ]
    
    template = TEMPLATES[template_name]
    formatted = template_manager.format_context(list(context), prompt, template_name)
    
    console.print(Panel(
        f"Template: [bold cyan]{template.name}[/bold cyan]\n"
        f"Strength: {template.strength}/10\n"
        f"Type: {template.template_type.value}",
        title="Template Info"
    ))
    
    console.print("\n[bold yellow]Context Entries:[/bold yellow]")
    for i, entry in enumerate(context, 1):
        console.print(f"  {i}. {entry}")
    
    console.print(f"\n[bold yellow]User Prompt:[/bold yellow]\n  {prompt}")
    
    console.print("\n[bold green]Formatted Result:[/bold green]")
    console.print(Panel(formatted, title="Final Prompt Sent to AI"))


@templates.command()
@click.option('--min-strength', default=7, help='Minimum template strength to include')
def recommend(min_strength):
    """Get template recommendations based on strength."""
    strong_templates = template_manager.get_strongest_templates(min_strength)
    
    console.print(f"[bold blue]Recommended Templates (Strength >= {min_strength}/10)[/bold blue]")
    console.print("=" * 60)
    
    if not strong_templates:
        console.print("❌ No templates found with the specified minimum strength")
        return
    
    table = Table(title=f"Strong Templates (>= {min_strength}/10)")
    table.add_column("Name", style="cyan")
    table.add_column("Strength", justify="center")
    table.add_column("Type")
    table.add_column("Best For")
    
    for name in strong_templates:
        template = TEMPLATES[name]
        strength_display = f"[green]{template.strength}/10[/green]"
        use_cases = ", ".join(template.use_cases[:2])  # Show first 2 use cases
        
        table.add_row(
            name,
            strength_display,
            template.template_type.value,
            use_cases
        )
    
    console.print(table)
    
    # Recommend the strongest
    strongest = max(strong_templates, key=lambda x: TEMPLATES[x].strength)
    console.print(Panel(
        f"💡 Recommended: [bold cyan]{strongest}[/bold cyan]\n"
        f"This template has the highest strength ({TEMPLATES[strongest].strength}/10) "
        f"and is most likely to produce personalized responses.",
        title="Recommendation"
    ))


@templates.command()
def demo():
    """Show a demo of all templates with sample data."""
    console.print("[bold blue]Template Demo - All Templates with Sample Data[/bold blue]")
    console.print("=" * 80)
    
    sample_context = [
        "I am a software engineer who loves Python and testing",
        "I prefer detailed explanations and want to understand how systems work",
        "I built ContextVault to give local AI models persistent memory"
    ]
    sample_prompt = "What programming languages should I learn next?"
    
    for name, template in TEMPLATES.items():
        console.print(f"\n🔹 [bold cyan]{template.name}[/bold cyan] (Strength: {template.strength}/10)")
        console.print(f"   Type: {template.template_type.value}")
        console.print(f"   {template.description}")
        
        formatted = template_manager.format_context(sample_context, sample_prompt, name)
        
        # Show a preview of the formatted prompt
        preview = formatted[:200] + "..." if len(formatted) > 200 else formatted
        console.print(f"\n   📝 Preview:\n   {preview}")
        console.print("   " + "─" * 60)


if __name__ == "__main__":
    templates()
