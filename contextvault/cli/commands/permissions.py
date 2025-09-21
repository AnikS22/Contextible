"""Permission management commands for ContextVault CLI."""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextvault.services import permission_service
from contextvault.database import get_db_context
from contextvault.models import Permission

console = Console()


@click.group(name="permissions")
def permissions_group():
    """Manage model permissions."""
    pass


@permissions_group.command()
@click.argument('model_id')
@click.option('--scope', required=True, help='Comma-separated list of allowed scopes')
@click.option('--name', 'model_name', help='Human-readable model name')
@click.option('--description', help='Description of what this permission allows')
@click.option('--max-entries', type=int, help='Maximum number of context entries')
@click.option('--max-age-days', type=int, help='Maximum age of context entries in days')
@click.option('--allowed-tags', help='Comma-separated list of allowed tags')
@click.option('--excluded-tags', help='Comma-separated list of excluded tags')
def add(model_id, scope, model_name, description, max_entries, max_age_days, allowed_tags, excluded_tags):
    """Add or update permission for a model."""
    try:
        # Parse scope
        scopes = [s.strip() for s in scope.split(',') if s.strip()]
        
        # Build rules
        rules = {}
        if max_entries is not None:
            rules['max_entries'] = max_entries
        if max_age_days is not None:
            rules['max_age_days'] = max_age_days
        if allowed_tags:
            rules['allowed_tags'] = [tag.strip() for tag in allowed_tags.split(',') if tag.strip()]
        if excluded_tags:
            rules['excluded_tags'] = [tag.strip() for tag in excluded_tags.split(',') if tag.strip()]
        
        # Create permission with proper session management
        with get_db_context() as db:
            from contextvault.services.permissions import PermissionService
            session_permission_service = PermissionService(db_session=db)
            
            permission = session_permission_service.create_permission_rule(
                model_id=model_id,
                scopes=scopes,
                rules=rules,
                description=description,
                model_name=model_name,
            )
            
            # Extract data while still in session
            permission_id = permission.id
        
        console.print(f"✅ [bold green]Permission created/updated for model:[/bold green] {model_id}")
        console.print(f"   ID: {permission_id}")
        console.print(f"   Scopes: {', '.join(scopes)}")
        if model_name:
            console.print(f"   Name: {model_name}")
        if description:
            console.print(f"   Description: {description}")
        if rules:
            console.print(f"   Rules: {rules}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to add permission:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.option('--model', help='Filter by model ID')
@click.option('--active', type=bool, help='Filter by active status')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def list(model, active, format):
    """List all permission rules."""
    try:
        with get_db_context() as db:
            query = db.query(Permission)
            
            if model:
                query = query.filter(Permission.model_id == model)
            
            if active is not None:
                query = query.filter(Permission.is_active == active)
            
            permissions = query.all()
            
            # Extract data while still in session to avoid detached instance errors
            perm_data = []
            for perm in permissions:
                perm_data.append({
                    'id': perm.id,
                    'model_id': perm.model_id,
                    'model_name': perm.model_name,
                    'scope': perm.scope,
                    'rules': perm.rules,
                    'description': perm.description,
                    'is_active': perm.is_active,
                    'created_at': perm.created_at,
                    'updated_at': perm.updated_at,
                    'usage_count': perm.usage_count,
                    'last_used_at': perm.last_used_at,
                })
        
        if not perm_data:
            console.print("📭 [yellow]No permissions found[/yellow]")
            return
        
        if format == 'json':
            import json
            console.print(json.dumps(perm_data, indent=2, default=str))
        else:
            console.print(f"🔐 [bold]Permission Rules ({len(perm_data)}):[/bold]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Model ID", style="cyan", width=15)
            table.add_column("Name", style="blue", width=15)
            table.add_column("Scopes", style="green", width=20)
            table.add_column("Active", style="yellow", width=8)
            table.add_column("Usage", style="white", width=8)
            table.add_column("Created", style="yellow", width=12)
            
            for perm in perm_data:
                active_status = "✅ Yes" if perm['is_active'] else "❌ No"
                scopes_str = perm['scope'] or ""
                if len(scopes_str) > 17:
                    scopes_str = scopes_str[:14] + "..."
                
                created_str = perm['created_at'].strftime("%m-%d %H:%M") if perm['created_at'] else ""
                
                table.add_row(
                    perm['model_id'],
                    perm['model_name'] or "",
                    scopes_str,
                    active_status,
                    str(perm['usage_count'] or 0),
                    created_str
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to list permissions:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.argument('model_id')
@click.option('--format', type=click.Choice(['detailed', 'json']), default='detailed',
              help='Output format')
def show(model_id, format):
    """Show detailed permission information for a model."""
    try:
        summary = permission_service.get_permission_summary(model_id)
        
        if not summary.get('has_permissions') and not summary.get('error'):
            console.print(f"❌ [bold red]No permissions found for model:[/bold red] {model_id}")
            sys.exit(1)
        
        if format == 'json':
            import json
            console.print(json.dumps(summary, indent=2, default=str))
        else:
            console.print(Panel.fit(f"🔐 [bold]Permissions for {model_id}[/bold]"))
            
            if summary.get('error'):
                console.print(f"❌ [bold red]Error:[/bold red] {summary['error']}")
                return
            
            console.print(f"[bold cyan]Access Level:[/bold cyan] {summary['access_level']}")
            console.print(f"[bold cyan]Total Permissions:[/bold cyan] {summary['total_permissions']}")
            console.print(f"[bold cyan]Active Permissions:[/bold cyan] {summary['active_permissions']}")
            
            if summary['allowed_scopes']:
                console.print(f"[bold cyan]Allowed Scopes:[/bold cyan] {', '.join(summary['allowed_scopes'])}")
            
            if summary['restrictions']:
                console.print(f"[bold cyan]Restrictions:[/bold cyan]")
                for restriction in summary['restrictions']:
                    console.print(f"  • {restriction}")
            
            if summary.get('last_used'):
                console.print(f"[bold cyan]Last Used:[/bold cyan] {summary['last_used']}")
            
            if summary.get('total_usage'):
                console.print(f"[bold cyan]Total Usage:[/bold cyan] {summary['total_usage']}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to show permissions:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.argument('permission_id')
@click.option('--scope', help='Update allowed scopes')
@click.option('--name', 'model_name', help='Update model name')
@click.option('--description', help='Update description')
@click.option('--active', type=bool, help='Set active status')
def update(permission_id, scope, model_name, description, active):
    """Update a permission rule."""
    try:
        with get_db_context() as db:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not permission:
                console.print(f"❌ [bold red]Permission not found:[/bold red] {permission_id}")
                sys.exit(1)
            
            # Apply updates
            updates = {}
            if scope is not None:
                updates['scope'] = scope
            if model_name is not None:
                updates['model_name'] = model_name
            if description is not None:
                updates['description'] = description
            if active is not None:
                updates['is_active'] = active
            
            if not updates:
                console.print("❌ [bold red]No updates specified[/bold red]")
                sys.exit(1)
            
            for field, value in updates.items():
                setattr(permission, field, value)
            
            from datetime import datetime
            permission.updated_at = datetime.utcnow()
            
            db.commit()
            
            console.print(f"✅ [bold green]Permission updated:[/bold green] {permission_id}")
            
            # Show what was updated
            for field, value in updates.items():
                console.print(f"   {field.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to update permission:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.argument('permission_id')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def delete(permission_id, force):
    """Delete a permission rule."""
    try:
        with get_db_context() as db:
            permission = db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not permission:
                console.print(f"❌ [bold red]Permission not found:[/bold red] {permission_id}")
                sys.exit(1)
            
            model_id = permission.model_id
            
            if not force:
                if not click.confirm(f"Delete permission for model '{model_id}' ({permission_id})?"):
                    console.print("❌ [yellow]Deletion cancelled[/yellow]")
                    return
            
            db.delete(permission)
            db.commit()
            
            console.print(f"✅ [bold green]Permission deleted:[/bold green] {model_id} ({permission_id})")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to delete permission:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.argument('model_id')
@click.argument('context_entry_id', required=False)
@click.option('--scope', help='Specific scope to check')
@click.option('--tags', help='Comma-separated tags to check')
@click.option('--context-type', help='Context type to check')
def check(model_id, context_entry_id, scope, tags, context_type):
    """Check if a model has permission to access content."""
    try:
        from contextvault.schemas.permissions import PermissionCheck
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create check request
        check_request = PermissionCheck(
            model_id=model_id,
            context_entry_id=context_entry_id,
            scope=scope,
            tags=tag_list,
            context_type=context_type,
        )
        
        # Perform permission check using API endpoint logic
        with get_db_context() as db:
            from contextvault.api.permissions import check_permission as api_check_permission
            
            # Simulate the API call
            import asyncio
            
            class MockDB:
                def __init__(self, session):
                    self._session = session
                
                def query(self, model):
                    return self._session.query(model)
                
                def commit(self):
                    return self._session.commit()
            
            mock_db = MockDB(db)
            
            # Use the permission service directly
            if context_entry_id:
                from contextvault.models import ContextEntry
                entry = db.query(ContextEntry).filter(ContextEntry.id == context_entry_id).first()
                if not entry:
                    console.print(f"❌ [bold red]Context entry not found:[/bold red] {context_entry_id}")
                    sys.exit(1)
                
                allowed, reason, perm_ids = permission_service.check_permission(model_id, entry)
            else:
                # Check general permissions
                allowed_scopes = permission_service.get_allowed_scopes(model_id)
                if scope and scope in allowed_scopes:
                    allowed = True
                    reason = f"Model has access to scope '{scope}'"
                    perm_ids = []
                elif "all" in allowed_scopes:
                    allowed = True
                    reason = "Model has unrestricted access"
                    perm_ids = []
                else:
                    allowed = False
                    reason = f"Model does not have access to scope '{scope}'" if scope else "No permissions found"
                    perm_ids = []
        
        # Display results
        status = "✅ ALLOWED" if allowed else "❌ DENIED"
        console.print(f"🔍 [bold]Permission Check Result:[/bold] {status}")
        console.print(f"   Model: {model_id}")
        
        if context_entry_id:
            console.print(f"   Context Entry: {context_entry_id}")
        if scope:
            console.print(f"   Scope: {scope}")
        if tag_list:
            console.print(f"   Tags: {', '.join(tag_list)}")
        if context_type:
            console.print(f"   Context Type: {context_type}")
        
        console.print(f"   Reason: {reason}")
        
        if perm_ids:
            console.print(f"   Applicable Permissions: {', '.join(perm_ids)}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Permission check failed:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.argument('model_id')
@click.option('--scope', default='basic', help='Default scope to assign')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def reset(model_id, scope, force):
    """Reset permissions for a model to default settings."""
    try:
        if not force:
            if not click.confirm(f"Reset all permissions for model '{model_id}' to default?"):
                console.print("❌ [yellow]Reset cancelled[/yellow]")
                return
        
        with get_db_context() as db:
            # Delete existing permissions
            existing_permissions = db.query(Permission).filter(Permission.model_id == model_id).all()
            for perm in existing_permissions:
                db.delete(perm)
            
            # Create default permission
            default_permission = Permission.create_default_permission(model_id, scope)
            db.add(default_permission)
            
            db.commit()
            
            console.print(f"✅ [bold green]Permissions reset for model:[/bold green] {model_id}")
            console.print(f"   Default scope: {scope}")
            console.print(f"   Permission ID: {default_permission.id}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to reset permissions:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.option('--include-inactive', is_flag=True, help='Include inactive permissions')
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def models(include_inactive, format):
    """List all models with their permission summaries."""
    try:
        with get_db_context() as db:
            query = db.query(Permission.model_id).distinct()
            
            if not include_inactive:
                query = query.filter(Permission.is_active == True)
            
            model_ids = [result[0] for result in query.all()]
        
        if not model_ids:
            console.print("📭 [yellow]No models with permissions found[/yellow]")
            return
        
        summaries = []
        for model_id in model_ids:
            try:
                summary = permission_service.get_permission_summary(model_id)
                summaries.append(summary)
            except Exception:
                continue
        
        if format == 'json':
            import json
            console.print(json.dumps(summaries, indent=2, default=str))
        else:
            console.print(f"🤖 [bold]Models with Permissions ({len(summaries)}):[/bold]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Model ID", style="cyan", width=15)
            table.add_column("Access Level", style="blue", width=12)
            table.add_column("Permissions", style="green", width=12)
            table.add_column("Scopes", style="white", width=25)
            table.add_column("Usage", style="yellow", width=8)
            
            for summary in summaries:
                access_level = summary['access_level']
                if access_level == 'unlimited':
                    access_level = "🔓 Unlimited"
                elif access_level == 'none':
                    access_level = "🔒 None"
                else:
                    access_level = "🔑 Limited"
                
                scopes_str = ', '.join(summary['allowed_scopes'][:3])
                if len(summary['allowed_scopes']) > 3:
                    scopes_str += "..."
                
                table.add_row(
                    summary['model_id'],
                    access_level,
                    f"{summary['active_permissions']}/{summary['total_permissions']}",
                    scopes_str,
                    str(summary.get('total_usage', 0))
                )
            
            console.print(table)
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to list models:[/bold red] {e}")
        sys.exit(1)


@permissions_group.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def templates(format):
    """Show available permission templates."""
    templates_data = [
        {
            "name": "basic",
            "description": "Basic access to text and preferences",
            "scope": "text,preferences",
            "rules": {"max_entries": 25, "max_age_days": 14}
        },
        {
            "name": "assistant",
            "description": "Standard assistant access",
            "scope": "preferences,notes,text",
            "rules": {"max_entries": 50, "max_age_days": 30}
        },
        {
            "name": "coding",
            "description": "Coding assistant with file access",
            "scope": "preferences,notes,files,text",
            "rules": {"max_entries": 100, "max_age_days": 60, "allowed_tags": ["coding", "programming", "development"]}
        },
        {
            "name": "unlimited",
            "description": "Unrestricted access to all content",
            "scope": "all",
            "rules": {}
        }
    ]
    
    if format == 'json':
        import json
        console.print(json.dumps(templates_data, indent=2))
    else:
        console.print("📋 [bold]Available Permission Templates:[/bold]")
        
        for template in templates_data:
            console.print(f"\n[bold cyan]{template['name']}:[/bold cyan]")
            console.print(f"  Description: {template['description']}")
            console.print(f"  Scope: {template['scope']}")
            if template['rules']:
                console.print(f"  Rules: {template['rules']}")
            
            console.print(f"  [dim]Usage: contextvault permissions add MODEL_ID --scope={template['scope']}[/dim]")
