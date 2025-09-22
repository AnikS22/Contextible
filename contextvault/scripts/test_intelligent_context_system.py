#!/usr/bin/env python3
"""
Comprehensive test suite for ContextVault intelligent context system.
Tests all core functionality including retrieval, categorization, and analytics.
"""

import sys
import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the parent directory to the path so we can import contextvault modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextvault.services.vault import VaultService
from contextvault.database import get_db_context
from contextvault.models import ContextEntry, ContextType, Session

class TestSuite:
    """Comprehensive test suite for ContextVault."""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_database_connection(self) -> bool:
        """Test database connectivity and basic operations."""
        try:
            with get_db_context() as db:
                # Test basic query
                count = db.query(ContextEntry).count()
                self.log_test("Database Connection", True, f"Found {count} existing contexts")
                return True
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
            return False
    
    def test_context_creation(self) -> bool:
        """Test context entry creation."""
        try:
            test_contexts = [
                {
                    "content": "I am a software engineer specializing in Python and machine learning.",
                    "context_type": ContextType.PERSONAL_INFO,
                    "source": "test_suite"
                },
                {
                    "content": "I work at TechCorp as a Senior Developer on the AI team.",
                    "context_type": ContextType.PROJECT,
                    "source": "test_suite"
                },
                {
                    "content": "I enjoy hiking, reading sci-fi novels, and playing guitar.",
                    "context_type": ContextType.PREFERENCE,
                    "source": "test_suite"
                },
                {
                    "content": "Our team is working on a new recommendation system using transformers.",
                    "context_type": ContextType.PROJECT,
                    "source": "test_suite"
                }
            ]
            
            created_ids = []
            with get_db_context() as db:
                for ctx_data in test_contexts:
                    context_entry = ContextEntry(
                        content=ctx_data["content"],
                        context_type=ctx_data["context_type"],
                        source=ctx_data["source"],
                        metadata={"test": True, "timestamp": datetime.now().isoformat()}
                    )
                    db.add(context_entry)
                    db.commit()
                    created_ids.append(context_entry.id)
            
            self.log_test("Context Creation", True, f"Created {len(created_ids)} test contexts")
            return True
            
        except Exception as e:
            self.log_test("Context Creation", False, str(e))
            return False
    
    def test_context_retrieval(self) -> bool:
        """Test context retrieval and search."""
        try:
            with get_db_context() as db:
                # Test basic retrieval
                vault_service_with_db = VaultService(db_session=db)
                contexts, total = vault_service_with_db.get_context(limit=10)
                if contexts:
                    self.log_test("Context Retrieval", True, f"Retrieved {len(contexts)} contexts")
                else:
                    self.log_test("Context Retrieval", False, "No contexts retrieved")
                    return False
                
                # Test search functionality
                search_results, search_total = vault_service_with_db.search_context("Python", limit=5)
                if search_results:
                    self.log_test("Context Search", True, f"Found {len(search_results)} matching contexts")
                else:
                    self.log_test("Context Search", False, "No search results found")
                    return False
                
                return True
                
        except Exception as e:
            self.log_test("Context Retrieval", False, str(e))
            return False
    
    def test_categorization(self) -> bool:
        """Test context categorization."""
        try:
            with get_db_context() as db:
                # Get contexts and check categorization
                vault_service_with_db = VaultService(db_session=db)
                contexts, total = vault_service_with_db.get_context(limit=20)
                
                personal_count = sum(1 for ctx in contexts if ctx.context_type == ContextType.PERSONAL_INFO)
                project_count = sum(1 for ctx in contexts if ctx.context_type == ContextType.PROJECT)
                
                self.log_test("Context Categorization", True, 
                             f"Personal: {personal_count}, Project: {project_count}")
                return True
                
        except Exception as e:
            self.log_test("Context Categorization", False, str(e))
            return False
    
    def test_session_tracking(self) -> bool:
        """Test session tracking functionality."""
        try:
            with get_db_context() as db:
                # Create a test session
                session = Session(
                    id="test_session_123",
                    model_id="test_model",
                    started_at=datetime.now(),
                    session_metadata={"test": True}
                )
                db.add(session)
                db.commit()
                
                # Retrieve session
                retrieved_session = db.query(Session).filter(
                    Session.id == "test_session_123"
                ).first()
                
                if retrieved_session:
                    self.log_test("Session Tracking", True, "Session created and retrieved")
                    return True
                else:
                    self.log_test("Session Tracking", False, "Session not found")
                    return False
                    
        except Exception as e:
            self.log_test("Session Tracking", False, str(e))
            return False
    
    def test_analytics(self) -> bool:
        """Test analytics functionality."""
        try:
            with get_db_context() as db:
                # Test basic analytics - count contexts
                context_count = db.query(ContextEntry).count()
                
                if context_count >= 0:
                    self.log_test("Analytics System", True, 
                                 f"Total contexts: {context_count}")
                    return True
                else:
                    self.log_test("Analytics System", False, "Could not count contexts")
                    return False
                    
        except Exception as e:
            self.log_test("Analytics System", False, str(e))
            return False
    
    def test_proxy_connectivity(self) -> bool:
        """Test proxy and Ollama connectivity."""
        proxy_ok = False
        ollama_ok = False
        
        # Test proxy
        try:
            response = requests.get("http://localhost:11435/health", timeout=5)
            if response.status_code == 200:
                proxy_ok = True
                self.log_test("Proxy Connectivity", True, "Proxy is running")
            else:
                self.log_test("Proxy Connectivity", False, f"Proxy returned status {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_test("Proxy Connectivity", False, "Proxy not accessible")
        
        # Test Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                ollama_ok = True
                self.log_test("Ollama Connectivity", True, f"Ollama running with {len(models)} models")
            else:
                self.log_test("Ollama Connectivity", False, f"Ollama returned status {response.status_code}")
        except requests.exceptions.RequestException:
            self.log_test("Ollama Connectivity", False, "Ollama not accessible")
        
        return proxy_ok and ollama_ok
    
    def test_context_injection_simulation(self) -> bool:
        """Simulate context injection process."""
        try:
            # Simulate a conversation request
            test_prompt = "What do you know about me?"
            
            with get_db_context() as db:
                # Get relevant context
                vault_service_with_db = VaultService(db_session=db)
                contexts, total = vault_service_with_db.search_context("software", limit=3)
                
                if contexts:
                    # Simulate context injection
                    injected_context = "\n".join([ctx.content for ctx in contexts])
                    enhanced_prompt = f"Context about the user:\n{injected_context}\n\nUser question: {test_prompt}"
                    
                    self.log_test("Context Injection Simulation", True, 
                                 f"Injected {len(contexts)} contexts into prompt")
                    return True
                else:
                    self.log_test("Context Injection Simulation", False, "No contexts found for injection")
                    return False
                    
        except Exception as e:
            self.log_test("Context Injection Simulation", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("🧪 ContextVault Comprehensive Test Suite")
        print("=" * 60)
        print(f"Started: {self.start_time.isoformat()}")
        print()
        
        # Run all tests
        tests = [
            self.test_database_connection,
            self.test_context_creation,
            self.test_context_retrieval,
            self.test_categorization,
            self.test_session_tracking,
            self.test_analytics,
            self.test_proxy_connectivity,
            self.test_context_injection_simulation
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Unexpected error: {str(e)}")
        
        # Calculate results
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["success"])
        failed_tests = total_tests - passed_tests
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print()
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print()
            print("❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print()
        if failed_tests == 0:
            print("🎉 All tests passed! ContextVault is working perfectly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "duration": duration.total_seconds(),
            "results": self.results
        }

def main():
    """Main test function."""
    test_suite = TestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
