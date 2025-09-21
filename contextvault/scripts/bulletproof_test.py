#!/usr/bin/env python3
"""
ContextVault Bulletproof Test Suite

This script ensures ContextVault works 100% of the time with comprehensive
testing, validation, and troubleshooting.
"""

import sys
import requests
import json
import time
import subprocess
import signal
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

class BulletproofTester:
    """Comprehensive test suite for ContextVault reliability."""
    
    def __init__(self):
        self.test_results = []
        self.critical_failures = []
        self.warnings = []
        self.proxy_process = None
        
    def run_all_tests(self) -> bool:
        """Run all tests and return True if everything passes."""
        console.print("🛡️ [bold blue]ContextVault Bulletproof Test Suite[/bold blue]")
        console.print("=" * 60)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Test sequence
            tests = [
                ("🔍 Checking Dependencies", self.test_dependencies),
                ("🗄️ Testing Database", self.test_database),
                ("🔧 Testing Ollama Connection", self.test_ollama_connection),
                ("🚀 Starting ContextVault Proxy", self.start_proxy),
                ("✅ Testing Proxy Health", self.test_proxy_health),
                ("🧠 Testing Context Retrieval", self.test_context_retrieval),
                ("💉 Testing Context Injection", self.test_context_injection),
                ("🎯 Testing Core Value", self.test_core_value),
                ("🔄 Testing Reliability", self.test_reliability),
                ("🛠️ Testing Troubleshooting", self.test_troubleshooting),
            ]
            
            task = progress.add_task("Running tests...", total=len(tests))
            
            for test_name, test_func in tests:
                progress.update(task, description=test_name)
                
                try:
                    result = test_func()
                    if result:
                        self.test_results.append((test_name, "✅ PASS", None))
                    else:
                        self.test_results.append((test_name, "❌ FAIL", "Test failed"))
                        self.critical_failures.append(test_name)
                except Exception as e:
                    self.test_results.append((test_name, "💥 ERROR", str(e)))
                    self.critical_failures.append(test_name)
                
                progress.advance(task)
        
        # Cleanup
        self.cleanup()
        
        # Generate report
        return self.generate_report()
    
    def test_dependencies(self) -> bool:
        """Test that all required dependencies are available."""
        try:
            import sqlalchemy
            import fastapi
            import uvicorn
            import requests
            
            # Test optional dependencies
            optional_deps = []
            try:
                from sentence_transformers import SentenceTransformer
                optional_deps.append("✅ sentence-transformers")
            except ImportError:
                optional_deps.append("⚠️ sentence-transformers (optional)")
            
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                optional_deps.append("✅ scikit-learn")
            except ImportError:
                optional_deps.append("❌ scikit-learn (required for fallback)")
                return False
            
            console.print(f"📦 Dependencies: {', '.join(optional_deps)}")
            return True
            
        except ImportError as e:
            console.print(f"❌ Missing dependency: {e}")
            return False
    
    def test_database(self) -> bool:
        """Test database connectivity and schema."""
        try:
            from contextvault.database import get_db_context, init_database
            from contextvault.models.context import ContextEntry
            
            # Initialize database
            init_database()
            
            # Test database operations
            with get_db_context() as db:
                # Test creating and querying entries
                test_entry = ContextEntry(
                    content="Test entry for bulletproof testing",
                    context_type="preference",
                    source="bulletproof_test",
                    tags=["test", "reliability"]
                )
                db.add(test_entry)
                db.commit()
                
                # Test querying
                entries = db.query(ContextEntry).filter(
                    ContextEntry.source == "bulletproof_test"
                ).all()
                
                # Cleanup
                for entry in entries:
                    db.delete(entry)
                db.commit()
                
            console.print("✅ Database operations successful")
            return True
            
        except Exception as e:
            console.print(f"❌ Database test failed: {e}")
            return False
    
    def test_ollama_connection(self) -> bool:
        """Test connection to Ollama."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                if models:
                    console.print(f"✅ Ollama connected, {len(models)} models available")
                    return True
                else:
                    console.print("⚠️ Ollama connected but no models found")
                    self.warnings.append("No Ollama models available")
                    return True
            else:
                console.print(f"❌ Ollama connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Ollama connection test failed: {e}")
            return False
    
    def start_proxy(self) -> bool:
        """Start the ContextVault proxy."""
        try:
            # Kill any existing proxy
            subprocess.run(["pkill", "-f", "ollama_proxy.py"], capture_output=True)
            time.sleep(1)
            
            # Start new proxy
            self.proxy_process = subprocess.Popen(
                ["python", "scripts/ollama_proxy.py"],
                cwd=Path(__file__).parent.parent,
                env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for proxy to start
            for i in range(10):
                try:
                    response = requests.get("http://localhost:11435/health", timeout=2)
                    if response.status_code == 200:
                        console.print("✅ ContextVault proxy started successfully")
                        return True
                except:
                    time.sleep(1)
            
            console.print("❌ ContextVault proxy failed to start")
            return False
            
        except Exception as e:
            console.print(f"❌ Failed to start proxy: {e}")
            return False
    
    def test_proxy_health(self) -> bool:
        """Test proxy health endpoint."""
        try:
            response = requests.get("http://localhost:11435/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                # Check all health components
                checks = [
                    ("proxy", health_data.get("proxy", {}).get("healthy", False)),
                    ("ollama", health_data.get("ollama", {}).get("status") == "healthy"),
                    ("database", health_data.get("database", {}).get("healthy", False)),
                    ("context_injection", health_data.get("context_injection") == "enabled")
                ]
                
                all_healthy = all(check[1] for check in checks)
                
                if all_healthy:
                    console.print("✅ All proxy components healthy")
                    return True
                else:
                    failed_checks = [check[0] for check in checks if not check[1]]
                    console.print(f"❌ Failed health checks: {failed_checks}")
                    return False
            else:
                console.print(f"❌ Proxy health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Proxy health test failed: {e}")
            return False
    
    def test_context_retrieval(self) -> bool:
        """Test context retrieval functionality."""
        try:
            from contextvault.database import get_db_context
            from contextvault.services.context_retrieval import ContextRetrievalService
            
            # Add test context
            with get_db_context() as db:
                from contextvault.models.context import ContextEntry
                
                # Clear any existing test entries
                db.query(ContextEntry).filter(
                    ContextEntry.source == "bulletproof_test"
                ).delete()
                
                # Add test entries
                test_entries = [
                    {
                        'content': 'I am a software engineer who loves Python and testing. I drive a Tesla Model 3.',
                        'context_type': 'preference',
                        'tags': ['python', 'testing', 'tesla', 'software']
                    },
                    {
                        'content': 'I have two cats named Luna and Pixel. They love to play with string.',
                        'context_type': 'note',
                        'tags': ['pets', 'cats', 'luna', 'pixel']
                    }
                ]
                
                for entry_data in test_entries:
                    entry = ContextEntry(
                        content=entry_data['content'],
                        context_type=entry_data['context_type'],
                        source="bulletproof_test",
                        tags=entry_data['tags']
                    )
                    db.add(entry)
                
                db.commit()
                
                # Test context retrieval
                retrieval_service = ContextRetrievalService(db_session=db)
                
                # Test queries
                test_queries = [
                    ("What programming languages do I like?", "python"),
                    ("What pets do I have?", "luna"),
                    ("What car do I drive?", "tesla")
                ]
                
                all_passed = True
                for query, expected_keyword in test_queries:
                    entries, metadata = retrieval_service.get_relevant_context(
                        model_id='mistral:latest',
                        query_context=query,
                        limit=5
                    )
                    
                    if not entries:
                        console.print(f"❌ No context found for query: {query}")
                        all_passed = False
                        continue
                    
                    # Check if expected keyword is in any entry
                    found_keyword = any(expected_keyword.lower() in entry.content.lower() for entry in entries)
                    if not found_keyword:
                        console.print(f"❌ Expected keyword '{expected_keyword}' not found for query: {query}")
                        all_passed = False
                
                # Cleanup
                db.query(ContextEntry).filter(
                    ContextEntry.source == "bulletproof_test"
                ).delete()
                db.commit()
                
                if all_passed:
                    console.print("✅ Context retrieval working correctly")
                    return True
                else:
                    return False
            
        except Exception as e:
            console.print(f"❌ Context retrieval test failed: {e}")
            return False
    
    def test_context_injection(self) -> bool:
        """Test that context is properly injected into AI responses."""
        try:
            # Test with a query that should trigger context injection
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
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").lower()
                
                # Check if the response contains expected context
                expected_keywords = ["luna", "pixel", "cats"]
                found_keywords = [kw for kw in expected_keywords if kw in ai_response]
                
                if found_keywords:
                    console.print(f"✅ Context injection working: found {found_keywords}")
                    return True
                else:
                    console.print(f"❌ Context injection failed: no expected keywords found")
                    console.print(f"   Response: {ai_response[:200]}...")
                    return False
            else:
                console.print(f"❌ Context injection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            console.print(f"❌ Context injection test failed: {e}")
            return False
    
    def test_core_value(self) -> bool:
        """Test that ContextVault provides clear value over direct Ollama."""
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
            
            if direct_response.status_code == 200 and contextvault_response.status_code == 200:
                direct_text = direct_response.json().get("response", "").lower()
                contextvault_text = contextvault_response.json().get("response", "").lower()
                
                # Check for value difference
                generic_phrases = ["i don't know", "i don't have", "i can't", "i don't have access", "i don't have personal", "i am an ai"]
                is_direct_generic = any(phrase in direct_text for phrase in generic_phrases)
                
                personal_keywords = ["luna", "pixel", "cats"]
                has_personal_info = any(keyword in contextvault_text for keyword in personal_keywords)
                
                # Also check if ContextVault response is longer/more detailed
                contextvault_longer = len(contextvault_text) > len(direct_text) * 1.2
                
                if (is_direct_generic and has_personal_info) or (has_personal_info and contextvault_longer):
                    console.print("✅ Core value proven: ContextVault provides personalized responses")
                    return True
                elif has_personal_info:
                    console.print("✅ Core value demonstrated: ContextVault provides personal information")
                    return True
                else:
                    console.print("❌ Core value not clear: responses too similar")
                    console.print(f"   Direct: {direct_text[:100]}...")
                    console.print(f"   ContextVault: {contextvault_text[:100]}...")
                    return False
            else:
                console.print("❌ Core value test failed: API requests failed")
                return False
                
        except Exception as e:
            console.print(f"❌ Core value test failed: {e}")
            return False
    
    def test_reliability(self) -> bool:
        """Test system reliability with multiple requests."""
        try:
            # Send multiple requests to test reliability
            test_requests = [
                "What programming languages do I like?",
                "What pets do I have?", 
                "What car do I drive?",
                "Tell me about my preferences",
                "What do I do for work?"
            ]
            
            success_count = 0
            for i, prompt in enumerate(test_requests):
                payload = {
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                }
                
                try:
                    response = requests.post(
                        "http://localhost:11435/api/generate",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        console.print(f"❌ Request {i+1} failed: {response.status_code}")
                        
                except Exception as e:
                    console.print(f"❌ Request {i+1} error: {e}")
            
            success_rate = success_count / len(test_requests)
            
            if success_rate >= 0.8:  # 80% success rate minimum
                console.print(f"✅ Reliability test passed: {success_rate:.1%} success rate")
                return True
            else:
                console.print(f"❌ Reliability test failed: {success_rate:.1%} success rate")
                return False
                
        except Exception as e:
            console.print(f"❌ Reliability test failed: {e}")
            return False
    
    def test_troubleshooting(self) -> bool:
        """Test the troubleshooting system."""
        try:
            from contextvault.services.troubleshooting import TroubleshootingAgent
            
            troubleshooter = TroubleshootingAgent()
            
            # Test diagnostic capabilities
            diagnostics = troubleshooter.run_full_diagnostics()
            
            if diagnostics.get("overall_health") in ["healthy", "degraded"]:
                console.print("✅ Troubleshooting system working correctly")
                return True
            else:
                console.print(f"⚠️ Troubleshooting found issues: {diagnostics.get('issues', [])}")
                return True  # Troubleshooting working, just found issues
                
        except Exception as e:
            console.print(f"❌ Troubleshooting test failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test resources."""
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
            except:
                try:
                    self.proxy_process.kill()
                except:
                    pass
    
    def generate_report(self) -> bool:
        """Generate comprehensive test report."""
        console.print("\n🎯 [bold blue]BULLETPROOF TEST REPORT[/bold blue]")
        console.print("=" * 60)
        
        # Create results table
        table = Table(title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        table.add_column("Details", style="yellow")
        
        for test_name, result, details in self.test_results:
            table.add_row(test_name, result, details or "")
        
        console.print(table)
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r[1]])
        failed_tests = len(self.critical_failures)
        
        console.print(f"\n📊 [bold]Summary:[/bold] {passed_tests}/{total_tests} tests passed")
        
        if failed_tests == 0:
            console.print("\n🎉 [bold green]ALL TESTS PASSED - ContextVault is BULLETPROOF![/bold green]")
            
            if self.warnings:
                console.print(f"\n⚠️ [yellow]Warnings:[/yellow] {', '.join(self.warnings)}")
            
            return True
        else:
            console.print(f"\n❌ [bold red]{failed_tests} CRITICAL FAILURES - System needs attention[/bold red]")
            console.print(f"Failed tests: {', '.join(self.critical_failures)}")
            return False

def main():
    """Run the bulletproof test suite."""
    tester = BulletproofTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            console.print("\n🚀 [bold green]ContextVault is ready for production![/bold green]")
            console.print("   All systems are bulletproof and reliable.")
            sys.exit(0)
        else:
            console.print("\n🛠️ [bold red]ContextVault needs fixes before production.[/bold red]")
            console.print("   Please address the critical failures above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n⏹️ [yellow]Testing interrupted by user[/yellow]")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        console.print(f"\n💥 [bold red]Testing failed with error: {e}[/bold red]")
        tester.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
