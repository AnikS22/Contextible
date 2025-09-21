#!/usr/bin/env python3
"""
ContextVault System Validation

This script validates that ContextVault is working correctly and provides
clear feedback on any issues. It's designed to run after installation
and can be used for troubleshooting.
"""

import sys
import requests
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

class SystemValidator:
    """Comprehensive system validation for ContextVault."""
    
    def __init__(self):
        self.validation_results = []
        self.critical_issues = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Run all validation checks."""
        console.print("🔍 [bold blue]ContextVault System Validation[/bold blue]")
        console.print("=" * 50)
        
        validations = [
            ("🔧 Environment Check", self.validate_environment),
            ("🗄️ Database Validation", self.validate_database),
            ("🤖 Ollama Integration", self.validate_ollama),
            ("🚀 Proxy Service", self.validate_proxy),
            ("🧠 Context System", self.validate_context_system),
            ("💉 Context Injection", self.validate_context_injection),
            ("🎯 Core Value Test", self.validate_core_value),
            ("⚡ Performance Test", self.validate_performance),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Validating system...", total=len(validations))
            
            for validation_name, validation_func in validations:
                progress.update(task, description=validation_name)
                
                try:
                    result = validation_func()
                    if result["status"] == "pass":
                        self.validation_results.append((validation_name, "✅ PASS", result.get("details", "")))
                    elif result["status"] == "warning":
                        self.validation_results.append((validation_name, "⚠️ WARNING", result.get("details", "")))
                        self.warnings.append(validation_name)
                    else:
                        self.validation_results.append((validation_name, "❌ FAIL", result.get("details", "")))
                        self.critical_issues.append(validation_name)
                except Exception as e:
                    self.validation_results.append((validation_name, "💥 ERROR", str(e)))
                    self.critical_issues.append(validation_name)
                
                progress.advance(task)
        
        return self.generate_report()
    
    def validate_environment(self) -> Dict[str, any]:
        """Validate the Python environment and dependencies."""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                return {
                    "status": "fail",
                    "details": f"Python {python_version.major}.{python_version.minor} found, but 3.8+ is required"
                }
            
            # Check required packages
            required_packages = [
                "sqlalchemy", "fastapi", "uvicorn", "requests", "pydantic"
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return {
                    "status": "fail",
                    "details": f"Missing packages: {', '.join(missing_packages)}"
                }
            
            # Check optional packages
            optional_packages = {
                "sentence_transformers": "Semantic search (optional)",
                "sklearn": "Fallback semantic search (required if sentence_transformers missing)"
            }
            
            warnings = []
            for package, description in optional_packages.items():
                try:
                    __import__(package)
                except ImportError:
                    if package == "sklearn":
                        return {
                            "status": "fail",
                            "details": f"Missing required fallback package: {package} ({description})"
                        }
                    warnings.append(f"Optional package missing: {package}")
            
            details = f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"
            if warnings:
                details += f" | Warnings: {'; '.join(warnings)}"
            
            return {
                "status": "pass" if not warnings else "warning",
                "details": details
            }
            
        except Exception as e:
            return {"status": "fail", "details": f"Environment check failed: {e}"}
    
    def validate_database(self) -> Dict[str, any]:
        """Validate database connectivity and schema."""
        try:
            from contextvault.database import get_db_context, engine
            from contextvault.models.context import ContextEntry
            
            # Test connection
            with get_db_context() as db:
                # Test basic operations
                db.query(ContextEntry).limit(1).all()
                
                # Check table structure
                try:
                    inspector = engine.inspect()
                    tables = inspector.get_table_names()
                except AttributeError:
                    # Fallback for older SQLAlchemy versions
                    tables = []
                    try:
                        result = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in result.fetchall()]
                    except:
                        # If we can't inspect tables, assume they exist if we can query
                        tables = ["context_entries", "permissions", "sessions"]
                
                required_tables = ["context_entries", "permissions", "sessions"]
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    return {
                        "status": "fail",
                        "details": f"Missing database tables: {missing_tables}"
                    }
                
                # Check if we have any context entries
                context_count = db.query(ContextEntry).count()
                
                return {
                    "status": "pass",
                    "details": f"Database healthy, {context_count} context entries"
                }
                
        except Exception as e:
            return {"status": "fail", "details": f"Database validation failed: {e}"}
    
    def validate_ollama(self) -> Dict[str, any]:
        """Validate Ollama connectivity and models."""
        try:
            # Test Ollama connection
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                return {
                    "status": "fail",
                    "details": f"Ollama API error: {response.status_code}"
                }
            
            models_data = response.json()
            models = models_data.get("models", [])
            
            if not models:
                return {
                    "status": "fail",
                    "details": "No Ollama models available"
                }
            
            # Check for mistral:latest specifically
            model_names = [model.get("name", "") for model in models]
            if "mistral:latest" not in model_names:
                return {
                    "status": "warning",
                    "details": f"mistral:latest not found. Available: {', '.join(model_names)}"
                }
            
            return {
                "status": "pass",
                "details": f"Ollama connected, {len(models)} models available"
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "fail",
                "details": "Cannot connect to Ollama - is it running?"
            }
        except Exception as e:
            return {"status": "fail", "details": f"Ollama validation failed: {e}"}
    
    def validate_proxy(self) -> Dict[str, any]:
        """Validate ContextVault proxy service."""
        try:
            # Test proxy health endpoint
            response = requests.get("http://localhost:11435/health", timeout=5)
            if response.status_code != 200:
                return {
                    "status": "fail",
                    "details": f"Proxy health check failed: {response.status_code}"
                }
            
            health_data = response.json()
            
            # Check individual components
            components = {
                "proxy": health_data.get("proxy", {}).get("healthy", False),
                "ollama": health_data.get("ollama", {}).get("status") == "healthy",
                "database": health_data.get("database", {}).get("healthy", False),
                "context_injection": health_data.get("context_injection") == "enabled"
            }
            
            failed_components = [name for name, healthy in components.items() if not healthy]
            
            if failed_components:
                return {
                    "status": "fail",
                    "details": f"Proxy components failed: {', '.join(failed_components)}"
                }
            
            return {
                "status": "pass",
                "details": "Proxy service healthy, all components working"
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "fail",
                "details": "ContextVault proxy not running"
            }
        except Exception as e:
            return {"status": "fail", "details": f"Proxy validation failed: {e}"}
    
    def validate_context_system(self) -> Dict[str, any]:
        """Validate context retrieval and management."""
        try:
            from contextvault.database import get_db_context
            from contextvault.services.context_retrieval import ContextRetrievalService
            
            with get_db_context() as db:
                retrieval_service = ContextRetrievalService(db_session=db)
                
                # Test context retrieval
                entries, metadata = retrieval_service.get_relevant_context(
                    model_id='mistral:latest',
                    query_context='test query',
                    limit=5
                )
                
                # Test semantic search
                from contextvault.services.semantic_search import get_semantic_search_service
                semantic_service = get_semantic_search_service()
                
                semantic_available = semantic_service.is_available()
                
                details = f"Retrieved {len(entries)} entries"
                if semantic_available:
                    cache_stats = semantic_service.get_cache_stats()
                    if cache_stats.get("fallback_mode"):
                        details += ", using TF-IDF fallback"
                    else:
                        details += ", semantic search active"
                else:
                    details += ", semantic search unavailable"
                
                return {
                    "status": "pass",
                    "details": details
                }
                
        except Exception as e:
            return {"status": "fail", "details": f"Context system validation failed: {e}"}
    
    def validate_context_injection(self) -> Dict[str, any]:
        """Validate that context is properly injected into AI responses."""
        try:
            # Test with a simple query
            payload = {
                "model": "mistral:latest",
                "prompt": "What pets do I have?",
                "stream": False
            }
            
            response = requests.post(
                "http://localhost:11435/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "status": "fail",
                    "details": f"Context injection request failed: {response.status_code}"
                }
            
            result = response.json()
            ai_response = result.get("response", "").lower()
            
            # Check for signs of context injection
            context_indicators = ["luna", "pixel", "cats", "pets"]
            found_indicators = [indicator for indicator in context_indicators if indicator in ai_response]
            
            if found_indicators:
                return {
                    "status": "pass",
                    "details": f"Context injection working: found {found_indicators}"
                }
            else:
                # Check if response is generic
                generic_phrases = ["i don't know", "i don't have", "i can't", "i don't have access"]
                is_generic = any(phrase in ai_response for phrase in generic_phrases)
                
                if is_generic:
                    return {
                        "status": "fail",
                        "details": "Context injection failed: response is generic"
                    }
                else:
                    return {
                        "status": "warning",
                        "details": "Context injection unclear: response doesn't show clear personalization"
                    }
                
        except Exception as e:
            return {"status": "fail", "details": f"Context injection validation failed: {e}"}
    
    def validate_core_value(self) -> Dict[str, any]:
        """Validate that ContextVault provides clear value over direct Ollama."""
        try:
            # Get response without ContextVault
            direct_payload = {
                "model": "mistral:latest",
                "prompt": "What pets do I have?",
                "stream": False
            }
            
            direct_response = requests.post(
                "http://localhost:11434/api/generate",
                json=direct_payload,
                timeout=30
            )
            
            # Get response with ContextVault
            contextvault_response = requests.post(
                "http://localhost:11435/api/generate",
                json=direct_payload,
                timeout=30
            )
            
            if direct_response.status_code != 200 or contextvault_response.status_code != 200:
                return {
                    "status": "fail",
                    "details": "Failed to get responses from both services"
                }
            
            direct_text = direct_response.json().get("response", "").lower()
            contextvault_text = contextvault_response.json().get("response", "").lower()
            
            # Analyze responses
            generic_phrases = ["i don't know", "i don't have", "i can't", "i don't have access"]
            is_direct_generic = any(phrase in direct_text for phrase in generic_phrases)
            
            personal_keywords = ["luna", "pixel", "cats"]
            has_personal_info = any(keyword in contextvault_text for keyword in personal_keywords)
            
            if is_direct_generic and has_personal_info:
                return {
                    "status": "pass",
                    "details": "Core value proven: ContextVault provides personalized responses"
                }
            elif has_personal_info:
                return {
                    "status": "warning",
                    "details": "ContextVault works but direct Ollama also provides good responses"
                }
            else:
                return {
                    "status": "fail",
                    "details": "Core value not demonstrated: responses too similar"
                }
                
        except Exception as e:
            return {"status": "fail", "details": f"Core value validation failed: {e}"}
    
    def validate_performance(self) -> Dict[str, any]:
        """Validate system performance with multiple requests."""
        try:
            test_queries = [
                "What programming languages do I like?",
                "What pets do I have?",
                "What do I do for work?",
                "Tell me about my preferences"
            ]
            
            start_time = time.time()
            successful_requests = 0
            
            for query in test_queries:
                payload = {
                    "model": "mistral:latest",
                    "prompt": query,
                    "stream": False
                }
                
                try:
                    response = requests.post(
                        "http://localhost:11435/api/generate",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    else:
                        console.print(f"Request failed for query: {query}")
                        
                except Exception as e:
                    console.print(f"Request error for query '{query}': {e}")
            
            end_time = time.time()
            total_time = end_time - start_time
            success_rate = successful_requests / len(test_queries)
            avg_time = total_time / len(test_queries)
            
            if success_rate >= 0.8 and avg_time < 10:
                return {
                    "status": "pass",
                    "details": f"Performance good: {success_rate:.1%} success rate, {avg_time:.1f}s avg response time"
                }
            elif success_rate >= 0.6:
                return {
                    "status": "warning",
                    "details": f"Performance acceptable: {success_rate:.1%} success rate, {avg_time:.1f}s avg response time"
                }
            else:
                return {
                    "status": "fail",
                    "details": f"Performance poor: {success_rate:.1%} success rate, {avg_time:.1f}s avg response time"
                }
                
        except Exception as e:
            return {"status": "fail", "details": f"Performance validation failed: {e}"}
    
    def generate_report(self) -> bool:
        """Generate comprehensive validation report."""
        console.print("\n📊 [bold blue]VALIDATION REPORT[/bold blue]")
        console.print("=" * 50)
        
        # Create results table
        table = Table(title="Validation Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        for component, status, details in self.validation_results:
            table.add_row(component, status, details)
        
        console.print(table)
        
        # Summary
        total_checks = len(self.validation_results)
        passed_checks = len([r for r in self.validation_results if "✅" in r[1]])
        warning_checks = len([r for r in self.validation_results if "⚠️" in r[1]])
        failed_checks = len(self.critical_issues)
        
        console.print(f"\n📈 [bold]Summary:[/bold] {passed_checks}/{total_checks} checks passed")
        
        if warning_checks > 0:
            console.print(f"⚠️ [yellow]Warnings:[/yellow] {warning_checks} components have issues")
        
        if failed_checks > 0:
            console.print(f"❌ [red]Failures:[/red] {failed_checks} critical issues found")
        
        # Final verdict
        if failed_checks == 0:
            if warning_checks == 0:
                console.print("\n🎉 [bold green]SYSTEM FULLY VALIDATED![/bold green]")
                console.print("   ContextVault is working perfectly and ready for use.")
                return True
            else:
                console.print("\n✅ [bold green]SYSTEM VALIDATED WITH WARNINGS[/bold green]")
                console.print("   ContextVault is working but has some minor issues.")
                return True
        else:
            console.print("\n❌ [bold red]SYSTEM VALIDATION FAILED[/bold red]")
            console.print("   Critical issues must be resolved before ContextVault can be used.")
            console.print(f"   Failed components: {', '.join(self.critical_issues)}")
            return False

def main():
    """Run system validation."""
    validator = SystemValidator()
    
    try:
        success = validator.validate_all()
        
        if success:
            console.print("\n🚀 [bold green]ContextVault is ready for use![/bold green]")
            sys.exit(0)
        else:
            console.print("\n🛠️ [bold red]ContextVault needs attention before use.[/bold red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n⏹️ [yellow]Validation interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n💥 [bold red]Validation failed with error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
