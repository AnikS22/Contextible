"""Setup commands for ContextVault CLI."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.command()
def setup():
    """Initialize ContextVault for first-time use."""
    console.print("🚀 [bold blue]ContextVault Setup[/bold blue]")
    console.print("=" * 40)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        console.print(f"❌ [red]Python {python_version.major}.{python_version.minor} found, but 3.8+ is required[/red]")
        return
    
    console.print(f"✅ [green]Python {python_version.major}.{python_version.minor}.{python_version.micro} is compatible[/green]")
    
    # Check dependencies
    console.print("\n📦 [blue]Checking dependencies...[/blue]")
    
    required_packages = [
        "sqlalchemy", "fastapi", "uvicorn", "requests", "pydantic"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            console.print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            console.print(f"   ❌ {package}")
    
    if missing_packages:
        console.print(f"\n❌ [red]Missing required packages: {', '.join(missing_packages)}[/red]")
        console.print("   Install with: pip install -r requirements.txt")
        return
    
    # Check optional dependencies
    console.print("\n📦 [blue]Checking optional dependencies...[/blue]")
    
    optional_packages = {
        "sentence_transformers": "Semantic search (recommended)",
        "sklearn": "Fallback semantic search (required if sentence_transformers missing)"
    }
    
    for package, description in optional_packages.items():
        try:
            __import__(package)
            console.print(f"   ✅ {package} - {description}")
        except ImportError:
            if package == "sklearn":
                console.print(f"   ❌ {package} - {description}")
                console.print("   Install with: pip install scikit-learn")
            else:
                console.print(f"   ⚠️ {package} - {description}")
                console.print("   Install with: pip install sentence-transformers")
    
    # Check Ollama
    console.print("\n🤖 [blue]Checking Ollama...[/blue]")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get("models", [])
            
            if models:
                console.print(f"   ✅ Ollama is running with {len(models)} models")
                
                # Check for mistral:latest
                model_names = [model.get("name", "") for model in models]
                if "mistral:latest" in model_names:
                    console.print("   ✅ mistral:latest is available")
                else:
                    console.print("   ⚠️ mistral:latest not found")
                    console.print("   Install with: ollama pull mistral:latest")
            else:
                console.print("   ⚠️ Ollama is running but no models found")
                console.print("   Install a model: ollama pull mistral:latest")
        else:
            console.print(f"   ❌ Ollama API error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        console.print("   ❌ Ollama is not running")
        console.print("   Start with: ollama serve")
    except Exception as e:
        console.print(f"   ❌ Ollama check failed: {e}")
    
    # Initialize ContextVault
    console.print("\n🔧 [blue]Initializing ContextVault...[/blue]")
    
    try:
        from contextvault.database import init_database
        init_database()
        console.print("   ✅ Database initialized")
        
        # Create default permissions
        from contextvault.database import get_db_context
        from contextvault.models.permissions import Permission
        
        with get_db_context() as db:
            # Check if permissions already exist
            existing = db.query(Permission).filter(
                Permission.model_id == 'mistral:latest'
            ).first()
            
            if not existing:
                permission = Permission(
                    model_id='mistral:latest',
                    model_name='Mistral (Latest)',
                    scope='personal,work,preferences,notes',
                    is_active=True
                )
                db.add(permission)
                db.commit()
                console.print("   ✅ Default permissions created")
            else:
                console.print("   ✅ Permissions already exist")
        
        # Add sample context
        from contextvault.models.context import ContextEntry
        
        with get_db_context() as db:
            existing_count = db.query(ContextEntry).count()
            
            if existing_count == 0:
                sample_entries = [
                    {
                        'content': 'I am a software engineer who loves Python and testing. I prefer detailed explanations and want to understand how systems work.',
                        'context_type': 'preference',
                        'source': 'sample',
                        'tags': ['python', 'testing', 'software', 'engineering']
                    },
                    {
                        'content': 'I have two cats named Luna and Pixel. They are playful and love string toys.',
                        'context_type': 'note',
                        'source': 'sample',
                        'tags': ['pets', 'cats', 'luna', 'pixel']
                    },
                    {
                        'content': 'I drive a Tesla Model 3 and live in San Francisco. I enjoy hiking and rock climbing.',
                        'context_type': 'note',
                        'source': 'sample',
                        'tags': ['tesla', 'san francisco', 'hiking', 'rock climbing']
                    }
                ]
                
                for entry_data in sample_entries:
                    entry = ContextEntry(**entry_data)
                    db.add(entry)
                
                db.commit()
                console.print("   ✅ Sample context added")
            else:
                console.print("   ✅ Context entries already exist")
        
        console.print("\n🎉 [bold green]ContextVault setup complete![/bold green]")
        
        # Show next steps
        console.print(Panel(
            """[bold]Next Steps:[/bold]

1. Start ContextVault:
   [blue]python -m contextvault.cli start[/blue]

2. Test it works:
   [blue]python -m contextvault.cli test[/blue]

3. Run a demo:
   [blue]python -m contextvault.cli demo[/blue]

4. Use ContextVault:
   Instead of: curl http://localhost:11434/api/generate ...
   Use:        curl http://localhost:11435/api/generate ...

[bold]ContextVault is ready to give your AI models persistent memory! 🧠[/bold]""",
            title="🚀 Setup Complete",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"❌ [red]Setup failed: {e}[/red]")
        console.print("   Check the error message above and try again")
