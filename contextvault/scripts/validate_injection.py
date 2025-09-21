#!/usr/bin/env python3
"""
Context Injection Validation Test Suite
Controlled test scenarios to validate context injection is working
"""

import sys
import os
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.models.context import ContextEntry
from contextvault.database import get_db_context
from contextvault.services.injection_debugger import injection_debugger


class ContextInjectionValidator:
    """Validates context injection through controlled test scenarios."""
    
    def __init__(self):
        self.test_results = []
        self.base_url = "http://localhost:11435"
    
    def run_all_validation_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🧪 Context Injection Validation Test Suite")
        print("=" * 60)
        
        tests = [
            ("Empty Context Test", self.test_empty_context),
            ("Specific Context Test", self.test_specific_context),
            ("Context Injection Debug Test", self.test_injection_debugging),
            ("Response Personalization Test", self.test_response_personalization),
            ("Context Retrieval Test", self.test_context_retrieval),
            ("Template Effectiveness Test", self.test_template_effectiveness)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            print("-" * 40)
            
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"{status}: {result['summary']}")
            except Exception as e:
                results[test_name] = {
                    "passed": False,
                    "summary": f"Test failed with error: {e}",
                    "error": str(e)
                }
                print(f"❌ FAIL: Test failed with error: {e}")
        
        return results
    
    def test_empty_context(self) -> Dict[str, Any]:
        """Test that AI responds generically when no context is available."""
        # Clear all context first
        self._clear_all_context()
        
        prompt = "What do you know about me?"
        response = self._send_request(prompt)
        
        # Analyze response for generic indicators
        generic_indicators = [
            "i don't know", "i don't have", "i can't tell", "i'm not sure",
            "i don't have information", "i don't have context", "i don't have details"
        ]
        
        is_generic = any(indicator in response.lower() for indicator in generic_indicators)
        
        return {
            "passed": is_generic,
            "summary": f"Response is {'generic' if is_generic else 'personalized'} (expected generic)",
            "response": response,
            "generic_score": sum(1 for indicator in generic_indicators if indicator in response.lower()) / len(generic_indicators)
        }
    
    def test_specific_context(self) -> Dict[str, Any]:
        """Test that AI uses specific context when available."""
        # Add specific test context
        self._add_test_context("I am TestUser, a software engineer at Google who loves Python programming.")
        
        prompt = "What do you know about me?"
        response = self._send_request(prompt)
        
        # Analyze response for specific context usage
        expected_keywords = ["testuser", "software engineer", "google", "python"]
        found_keywords = [kw for kw in expected_keywords if kw in response.lower()]
        
        personalization_score = len(found_keywords) / len(expected_keywords)
        passed = personalization_score >= 0.5  # At least half the keywords should be mentioned
        
        return {
            "passed": passed,
            "summary": f"Found {len(found_keywords)}/{len(expected_keywords)} expected keywords",
            "response": response,
            "found_keywords": found_keywords,
            "personalization_score": personalization_score
        }
    
    def test_injection_debugging(self) -> Dict[str, Any]:
        """Test that injection debugging works correctly."""
        # Start injection debug
        injection_id = injection_debugger.start_injection_debug("test_model", "Test prompt")
        
        # Simulate injection steps
        injection_debugger.log_context_retrieval([], {})
        injection_debugger.log_template_selection("test_template", "Test template content")
        injection_debugger.log_context_formatting("Test context", [])
        injection_debugger.log_prompt_assembly("Test context\n\nTest prompt")
        injection_debugger.complete_injection_debug(True)
        
        # Check if log was created
        recent_logs = injection_debugger.get_recent_injections(1)
        
        return {
            "passed": len(recent_logs) > 0 and recent_logs[0].injection_id == injection_id,
            "summary": f"Injection debug log {'created' if recent_logs else 'not created'}",
            "injection_id": injection_id,
            "log_created": len(recent_logs) > 0
        }
    
    def test_response_personalization(self) -> Dict[str, Any]:
        """Test that responses are more personalized with context."""
        # Test 1: No context
        self._clear_all_context()
        response_no_context = self._send_request("Tell me about my work.")
        
        # Test 2: With context
        self._add_test_context("I work as a data scientist at Netflix, specializing in machine learning and recommendation systems.")
        response_with_context = self._send_request("Tell me about my work.")
        
        # Compare responses
        no_context_generic = any(indicator in response_no_context.lower() 
                               for indicator in ["i don't know", "i can't tell", "generic"])
        with_context_specific = any(keyword in response_with_context.lower() 
                                  for keyword in ["data scientist", "netflix", "machine learning", "recommendation"])
        
        improvement_detected = no_context_generic and with_context_specific
        
        return {
            "passed": improvement_detected,
            "summary": f"Personalization {'improved' if improvement_detected else 'not detected'}",
            "response_no_context": response_no_context,
            "response_with_context": response_with_context,
            "improvement_detected": improvement_detected
        }
    
    def test_context_retrieval(self) -> Dict[str, Any]:
        """Test that context retrieval works correctly."""
        # Add multiple test contexts
        test_contexts = [
            "I am Alice, a software engineer at Microsoft.",
            "I love working with Python and machine learning.",
            "I live in Seattle, Washington.",
            "I prefer using VSCode for coding."
        ]
        
        for context in test_contexts:
            self._add_test_context(context)
        
        # Test retrieval with different queries
        queries = [
            ("What do you know about my work?", ["software engineer", "microsoft"]),
            ("Tell me about my coding preferences.", ["python", "vscode"]),
            ("Where do I live?", ["seattle", "washington"])
        ]
        
        retrieval_results = []
        
        for query, expected_keywords in queries:
            response = self._send_request(query)
            found_keywords = [kw for kw in expected_keywords if kw in response.lower()]
            retrieval_results.append({
                "query": query,
                "expected": expected_keywords,
                "found": found_keywords,
                "success": len(found_keywords) > 0
            })
        
        success_rate = sum(1 for result in retrieval_results if result["success"]) / len(retrieval_results)
        
        return {
            "passed": success_rate >= 0.7,  # At least 70% success rate
            "summary": f"Context retrieval success rate: {success_rate:.1%}",
            "retrieval_results": retrieval_results,
            "success_rate": success_rate
        }
    
    def test_template_effectiveness(self) -> Dict[str, Any]:
        """Test that different templates produce different results."""
        # Add test context
        self._add_test_context("I am TemplateTest, a product manager at Apple who loves design and user experience.")
        
        # Test with different prompts that should trigger different templates
        test_prompts = [
            "What do you know about me?",
            "Tell me about my background.",
            "What are my interests?"
        ]
        
        responses = []
        for prompt in test_prompts:
            response = self._send_request(prompt)
            responses.append({
                "prompt": prompt,
                "response": response,
                "mentions_context": any(keyword in response.lower() 
                                      for keyword in ["templatetest", "product manager", "apple", "design", "user experience"])
            })
        
        context_usage_rate = sum(1 for resp in responses if resp["mentions_context"]) / len(responses)
        
        return {
            "passed": context_usage_rate >= 0.7,
            "summary": f"Template effectiveness: {context_usage_rate:.1%} of responses used context",
            "responses": responses,
            "context_usage_rate": context_usage_rate
        }
    
    def _send_request(self, prompt: str) -> str:
        """Send request to proxy and return response."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"
    
    def _clear_all_context(self):
        """Clear all context entries."""
        try:
            with get_db_context() as db:
                db.query(ContextEntry).delete()
                db.commit()
        except Exception as e:
            print(f"Warning: Could not clear context: {e}")
    
    def _add_test_context(self, content: str):
        """Add a test context entry."""
        try:
            with get_db_context() as db:
                context_entry = ContextEntry(
                    content=content,
                    context_type="note",
                    source="test",
                    tags=["test", "validation"],
                    entry_metadata={"test_context": True}
                )
                db.add(context_entry)
                db.commit()
        except Exception as e:
            print(f"Warning: Could not add test context: {e}")
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("🧪 Context Injection Validation Report")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["passed"])
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        report.append(f"📊 Summary:")
        report.append(f"   Total Tests: {total_tests}")
        report.append(f"   Passed: {passed_tests}")
        report.append(f"   Failed: {total_tests - passed_tests}")
        report.append(f"   Success Rate: {success_rate:.1%}")
        report.append("")
        
        # Individual test results
        report.append("📋 Test Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            report.append(f"   {status} {test_name}")
            report.append(f"      {result['summary']}")
            if "error" in result:
                report.append(f"      Error: {result['error']}")
            report.append("")
        
        # Overall assessment
        report.append("🎯 Overall Assessment:")
        if success_rate >= 0.8:
            report.append("   ✅ Context injection is working well!")
        elif success_rate >= 0.6:
            report.append("   ⚠️ Context injection is partially working.")
        else:
            report.append("   ❌ Context injection has significant issues.")
        
        return "\n".join(report)


def main():
    """Run the validation test suite."""
    validator = ContextInjectionValidator()
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:11435/health", timeout=5)
        if response.status_code != 200:
            print("❌ Proxy not running on port 11435")
            print("   Start ContextVault with: python -m contextvault.main &")
            print("   Then start proxy with: python scripts/ollama_proxy.py &")
            return 1
    except:
        print("❌ Cannot connect to proxy on port 11435")
        return 1
    
    # Run tests
    results = validator.run_all_validation_tests()
    
    # Generate report
    report = validator.generate_report(results)
    print("\n" + report)
    
    # Save report
    report_file = Path("./validation_report.txt")
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Report saved to: {report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
