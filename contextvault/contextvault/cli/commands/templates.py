"""Template management commands for ContextVault CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

@click.group(name="templates")
def templates():
    """Template management commands."""
    pass

@templates.command()
def list():
    """List available context injection templates."""
    console.print("📝 [bold blue]Available Templates[/bold blue]")
    
    try:
        from contextvault.services.templates import template_manager
        
        all_templates = template_manager.get_all_templates()
        
        if all_templates:
            table = Table(title="Context Injection Templates")
            table.add_column("Name", style="cyan", width=20)
            table.add_column("Type", style="blue", width=15)
            table.add_column("Strength", style="green", width=10)
            table.add_column("Description", style="white", max_width=40)
            
            for template in all_templates:
                strength_display = f"{template.strength}/10"
                if template.strength >= 8:
                    strength_style = "green"
                elif template.strength >= 6:
                    strength_style = "yellow"
                else:
                    strength_style = "red"
                
                table.add_row(
                    template.name.replace('_', ' ').title(),
                    template.template_type.value.title(),
                    f"[{strength_style}]{strength_display}[/{strength_style}]",
                    template.description
                )
            
            console.print(table)
            
            # Show current active template
            active_template = template_manager.get_template()
            console.print(f"\n✅ [green]Active Template:[/green] {active_template.name.replace('_', ' ').title()}")
            
        else:
            console.print("ℹ️ [yellow]No templates available[/yellow]")
            
    except Exception as e:
        console.print(f"❌ [red]Error listing templates: {e}[/red]")

@templates.command()
@click.argument('template_name')
def set(template_name: str):
    """Set the active context injection template."""
    console.print(f"⚙️ [bold blue]Setting Active Template: {template_name}[/bold blue]")
    
    try:
        from contextvault.services.templates import template_manager
        
        # Try to set the template
        new_template = template_manager.set_active_template(template_name)
        
        console.print(f"✅ [green]Active template set to:[/green] {new_template.name.replace('_', ' ').title()}")
        console.print(f"   Type: {new_template.template_type.value}")
        console.print(f"   Strength: {new_template.strength}/10")
        console.print(f"   Description: {new_template.description}")
        
    except ValueError as e:
        console.print(f"❌ [red]Invalid template: {e}[/red]")
        console.print("   Use 'templates list' to see available templates")
    except Exception as e:
        console.print(f"❌ [red]Error setting template: {e}[/red]")

@templates.command()
def current():
    """Show the current active template."""
    console.print("📋 [bold blue]Current Active Template[/bold blue]")
    
    try:
        from contextvault.services.templates import template_manager
        
        active_template = template_manager.get_template()
        
        panel_content = f"""[bold]Name:[/bold] {active_template.name.replace('_', ' ').title()}
[bold]Type:[/bold] {active_template.template_type.value.title()}
[bold]Strength:[/bold] {active_template.strength}/10
[bold]Description:[/bold] {active_template.description}

[bold]Template Preview:[/bold]
{active_template.template[:200]}{'...' if len(active_template.template) > 200 else ''}"""
        
        panel = Panel(
            panel_content,
            title="Active Template Details",
            border_style="blue"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"❌ [red]Error getting current template: {e}[/red]")

@templates.command()
@click.argument('template_name')
def preview(template_name: str):
    """Preview a template with sample data."""
    console.print(f"👁️ [bold blue]Previewing Template: {template_name}[/bold blue]")
    
    try:
        from contextvault.services.templates import template_manager, format_context_with_template
        
        # Get the template
        template = template_manager.get_template(template_name)
        
        # Sample data
        sample_context = [
            "I am a software engineer who loves Python and testing",
            "I have two cats named Luna and Pixel",
            "I prefer detailed explanations and want to understand how systems work"
        ]
        sample_prompt = "What programming languages should I learn next?"
        
        # Generate preview
        formatted_prompt = format_context_with_template(
            context_entries=sample_context,
            user_prompt=sample_prompt,
            template_name=template_name
        )
        
        panel = Panel(
            formatted_prompt,
            title=f"Template Preview: {template.name.replace('_', ' ').title()}",
            border_style="blue",
            subtitle=f"Strength: {template.strength}/10"
        )
        console.print(panel)
        
    except ValueError as e:
        console.print(f"❌ [red]Invalid template: {e}[/red]")
        console.print("   Use 'templates list' to see available templates")
    except Exception as e:
        console.print(f"❌ [red]Error previewing template: {e}[/red]")

@templates.command()
def test():
    """Test all templates with sample data."""
    console.print("🧪 [bold blue]Testing All Templates[/bold blue]")
    
    try:
        from contextvault.services.templates import template_manager, format_context_with_template
        
        # Sample data
        sample_context = [
            "I am a software engineer who loves Python and testing",
            "I have two cats named Luna and Pixel",
            "I prefer detailed explanations and want to understand how systems work"
        ]
        sample_prompt = "What pets do I have?"
        
        all_templates = template_manager.get_all_templates()
        
        for template in all_templates:
            console.print(f"\n🔹 [bold cyan]{template.name.replace('_', ' ').title()}[/bold cyan] (Strength: {template.strength}/10)")
            
            # Generate formatted prompt
            formatted_prompt = format_context_with_template(
                context_entries=sample_context,
                user_prompt=sample_prompt,
                template_name=template.name
            )
            
            # Show preview (first 300 characters)
            preview = formatted_prompt[:300] + "..." if len(formatted_prompt) > 300 else formatted_prompt
            console.print(f"   Preview: {preview}")
        
        console.print(f"\n✅ [green]Tested {len(all_templates)} templates[/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Error testing templates: {e}[/red]")
