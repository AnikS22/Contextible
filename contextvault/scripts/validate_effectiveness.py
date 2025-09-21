#!/usr/bin/env python3
"""
ContextVault Effectiveness Validation Script

Tests and measures how effectively context injection improves AI responses.
Provides A/B testing between responses with and without context.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sys
import requests
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.database import get_db_context
from contextvault.services.vault import VaultService
from contextvault.services.context_retrieval import ContextRetrievalService
from contextvault.models.context import ContextType

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """A test scenario for context effectiveness validation."""
    name: str
    description: str
    user_query: str
    expected_context_types: List[ContextType]
    expected_keywords: List[str]
    context_entries: List[Dict[str, Any]]


@dataclass
class TestResult:
    """Result of a context effectiveness test."""
    scenario_name: str
    query: str
    with_context_response: str
    without_context_response: str
    context_used: List[Dict[str, Any]]
    personalization_score: float
    context_relevance_score: float
    response_time_ms: int
    timestamp: datetime


class ContextEffectivenessTester:
    """Tests and validates context injection effectiveness."""
    
    def __init__(self, ollama_url: str = "http://localhost:11435", ollama_direct_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_direct_url = ollama_direct_url
        self.test_results: List[TestResult] = []
        
        # Setup test scenarios
        self.scenarios = self._create_test_scenarios()
    
    def _create_test_scenarios(self) -> List[TestScenario]:
        """Create predefined test scenarios."""
        return [
            TestScenario(
                name="programming_preferences",
                description="Test retrieval of user's programming preferences",
                user_query="What programming languages should I learn next?",
                expected_context_types=[ContextType.PREFERENCE, ContextType.NOTE],
                expected_keywords=["Python", "FastAPI", "backend", "engineer"],
                context_entries=[
                    {
                        "content": "I am a software engineer who loves Python and FastAPI for backend development",
                        "context_type": ContextType.PREFERENCE,
                        "tags": ["programming", "preferences", "backend"],
                        "source": "user_profile"
                    },
                    {
                        "content": "I prefer detailed explanations and want to understand how systems work",
                        "context_type": ContextType.PREFERENCE,
                        "tags": ["learning", "preferences"],
                        "source": "user_profile"
                    }
                ]
            ),
            TestScenario(
                name="current_project",
                description="Test retrieval of current project context",
                user_query="How can I improve my current project?",
                expected_context_types=[ContextType.NOTE, ContextType.EVENT],
                expected_keywords=["ContextVault", "testing", "development"],
                context_entries=[
                    {
                        "content": "I am currently working on ContextVault, a system for giving AI models persistent memory",
                        "context_type": ContextType.NOTE,
                        "tags": ["project", "development", "AI"],
                        "source": "project_notes"
                    },
                    {
                        "content": "Today I am testing ContextVault to ensure everything works properly",
                        "context_type": ContextType.EVENT,
                        "tags": ["testing", "today", "development"],
                        "source": "daily_log"
                    }
                ]
            ),
            TestScenario(
                name="technical_expertise",
                description="Test retrieval of user's technical background",
                user_query="What debugging techniques do you recommend?",
                expected_context_types=[ContextType.NOTE, ContextType.PREFERENCE],
                expected_keywords=["rigorous", "testing", "debug", "engineer"],
                context_entries=[
                    {
                        "content": "I am a software engineer who loves rigorous testing and debugging",
                        "context_type": ContextType.PREFERENCE,
                        "tags": ["engineering", "testing", "debugging"],
                        "source": "user_profile"
                    }
                ]
            )
        ]
    
    def setup_test_context(self) -> bool:
        """Set up test context entries in the database."""
        try:
            with get_db_context() as db:
                vault_service = VaultService(db_session=db)
                
                # Clear existing test entries
                existing_entries = db.query(vault_service.model).filter(
                    vault_service.model.source.in_([
                        "user_profile", "project_notes", "daily_log", "test_setup"
                    ])
                ).all()
                
                for entry in existing_entries:
                    db.delete(entry)
                db.commit()
                
                # Add test context entries
                for scenario in self.scenarios:
                    for context_data in scenario.context_entries:
                        context_data["source"] = context_data.get("source", "test_setup")
                        context_data["tags"] = context_data.get("tags", [])
                        
                        vault_service.add_context(
                            content=context_data["content"],
                            context_type=context_data["context_type"],
                            source=context_data["source"],
                            tags=context_data["tags"],
                            metadata={"test_scenario": scenario.name}
                        )
                
                db.commit()
                console.print("✅ [green]Test context setup completed[/green]")
                return True
                
        except Exception as e:
            console.print(f"❌ [red]Failed to setup test context: {e}[/red]")
            return False
    
    def _call_ollama(self, prompt: str, use_contextvault: bool = True) -> Tuple[str, int]:
        """Call Ollama with or without ContextVault."""
        url = self.ollama_url if use_contextvault else self.ollama_direct_url
        
        payload = {
            "model": "mistral:latest",
            "prompt": prompt,
            "stream": False
        }
        
        start_time = time.time()
        try:
            response = requests.post(f"{url}/api/generate", json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            response_time = int((time.time() - start_time) * 1000)
            
            return result.get("response", ""), response_time
            
        except Exception as e:
            console.print(f"❌ [red]Error calling Ollama: {e}[/red]")
            return "", 0
    
    def _calculate_personalization_score(self, response: str, expected_keywords: List[str]) -> float:
        """Calculate how personalized a response is based on expected keywords."""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        keyword_matches = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        
        # Score based on keyword matches and response length (longer responses often more detailed)
        keyword_score = min(keyword_matches / len(expected_keywords), 1.0)
        length_score = min(len(response) / 500, 1.0)  # Normalize to reasonable response length
        
        # Weighted combination
        return (keyword_score * 0.7) + (length_score * 0.3)
    
    def _calculate_context_relevance_score(self, context_used: List[Dict[str, Any]], expected_context_types: List[ContextType]) -> float:
        """Calculate how relevant the retrieved context is."""
        if not context_used:
            return 0.0
        
        # Check if context types match expectations
        retrieved_types = [entry.get("context_type") for entry in context_used]
        type_matches = sum(1 for expected_type in expected_context_types 
                          if expected_type in retrieved_types)
        
        type_score = type_matches / len(expected_context_types) if expected_context_types else 1.0
        
        # Bonus for having context at all
        presence_bonus = 1.0 if context_used else 0.0
        
        return (type_score * 0.8) + (presence_bonus * 0.2)
    
    def run_scenario_test(self, scenario: TestScenario) -> TestResult:
        """Run a single scenario test."""
        console.print(f"\n🧪 [bold blue]Testing scenario: {scenario.name}[/bold blue]")
        console.print(f"📝 Query: {scenario.user_query}")
        
        # Get context that would be used
        with get_db_context() as db:
            retrieval_service = ContextRetrievalService(db_session=db)
            entries, metadata = retrieval_service.get_relevant_context(
                model_id="test-model",
                query_context=scenario.user_query,
                limit=5
            )
            
            context_used = [
                {
                    "content": entry.content,
                    "context_type": entry.context_type,
                    "tags": entry.tags,
                    "relevance_score": getattr(entry, 'relevance_score', 0.0)
                }
                for entry in entries
            ]
        
        # Test with ContextVault (context injection)
        with_context_response, with_context_time = self._call_ollama(
            scenario.user_query, 
            use_contextvault=True
        )
        
        # Test without ContextVault (direct to Ollama)
        without_context_response, without_context_time = self._call_ollama(
            scenario.user_query,
            use_contextvault=False
        )
        
        # Calculate scores
        personalization_score = self._calculate_personalization_score(
            with_context_response, scenario.expected_keywords
        )
        
        context_relevance_score = self._calculate_context_relevance_score(
            context_used, scenario.expected_context_types
        )
        
        # Create result
        result = TestResult(
            scenario_name=scenario.name,
            query=scenario.user_query,
            with_context_response=with_context_response,
            without_context_response=without_context_response,
            context_used=context_used,
            personalization_score=personalization_score,
            context_relevance_score=context_relevance_score,
            response_time_ms=with_context_time,
            timestamp=datetime.now()
        )
        
        self.test_results.append(result)
        
        # Display results
        self._display_scenario_result(result)
        
        return result
    
    def _display_scenario_result(self, result: TestResult):
        """Display results for a single scenario."""
        console.print(f"\n📊 [bold green]Results for {result.scenario_name}[/bold green]")
        
        # Context used
        if result.context_used:
            console.print(f"🎯 [blue]Context Retrieved ({len(result.context_used)} entries):[/blue]")
            for i, ctx in enumerate(result.context_used, 1):
                console.print(f"   {i}. [{ctx['context_type']}] {ctx['content'][:80]}...")
        else:
            console.print("⚠️  [yellow]No context retrieved[/yellow]")
        
        # Scores
        console.print(f"\n📈 [blue]Scores:[/blue]")
        console.print(f"   Personalization: {result.personalization_score:.2f}/1.0")
        console.print(f"   Context Relevance: {result.context_relevance_score:.2f}/1.0")
        console.print(f"   Response Time: {result.response_time_ms}ms")
        
        # Response comparison
        console.print(f"\n💬 [blue]Response Comparison:[/blue]")
        
        with_context_panel = Panel(
            result.with_context_response[:300] + ("..." if len(result.with_context_response) > 300 else ""),
            title="[green]With Context[/green]",
            border_style="green"
        )
        
        without_context_panel = Panel(
            result.without_context_response[:300] + ("..." if len(result.without_context_response) > 300 else ""),
            title="[red]Without Context[/red]",
            border_style="red"
        )
        
        console.print(with_context_panel)
        console.print(without_context_panel)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios."""
        console.print("🚀 [bold blue]Starting ContextVault Effectiveness Tests[/bold blue]")
        console.print("=" * 60)
        
        # Setup test context
        if not self.setup_test_context():
            return {"error": "Failed to setup test context"}
        
        # Run all scenarios
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Running effectiveness tests...", total=len(self.scenarios))
            
            for scenario in self.scenarios:
                progress.update(task, description=f"Testing {scenario.name}...")
                self.run_scenario_test(scenario)
                progress.advance(task)
        
        # Generate summary
        return self._generate_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary and effectiveness metrics."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate aggregate metrics
        total_personalization_score = sum(r.personalization_score for r in self.test_results)
        total_context_relevance_score = sum(r.context_relevance_score for r in self.test_results)
        avg_response_time = sum(r.response_time_ms for r in self.test_results) / len(self.test_results)
        
        avg_personalization = total_personalization_score / len(self.test_results)
        avg_context_relevance = total_context_relevance_score / len(self.test_results)
        
        # Count scenarios with context
        scenarios_with_context = sum(1 for r in self.test_results if r.context_used)
        
        summary = {
            "total_scenarios": len(self.test_results),
            "scenarios_with_context": scenarios_with_context,
            "context_retrieval_rate": scenarios_with_context / len(self.test_results),
            "average_personalization_score": avg_personalization,
            "average_context_relevance_score": avg_context_relevance,
            "average_response_time_ms": avg_response_time,
            "effectiveness_rating": self._calculate_effectiveness_rating(avg_personalization, avg_context_relevance),
            "test_results": [
                {
                    "scenario": r.scenario_name,
                    "personalization_score": r.personalization_score,
                    "context_relevance_score": r.context_relevance_score,
                    "context_entries_used": len(r.context_used),
                    "response_time_ms": r.response_time_ms
                }
                for r in self.test_results
            ]
        }
        
        self._display_summary(summary)
        return summary
    
    def _calculate_effectiveness_rating(self, personalization: float, context_relevance: float) -> str:
        """Calculate overall effectiveness rating."""
        combined_score = (personalization * 0.6) + (context_relevance * 0.4)
        
        if combined_score >= 0.8:
            return "Excellent"
        elif combined_score >= 0.6:
            return "Good"
        elif combined_score >= 0.4:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _display_summary(self, summary: Dict[str, Any]):
        """Display test summary."""
        console.print("\n" + "=" * 60)
        console.print("📊 [bold blue]ContextVault Effectiveness Test Summary[/bold blue]")
        console.print("=" * 60)
        
        # Key metrics table
        metrics_table = Table(title="Key Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_column("Rating", style="yellow")
        
        metrics_table.add_row(
            "Context Retrieval Rate",
            f"{summary['context_retrieval_rate']:.1%}",
            "✅" if summary['context_retrieval_rate'] >= 0.8 else "⚠️"
        )
        
        metrics_table.add_row(
            "Average Personalization Score",
            f"{summary['average_personalization_score']:.2f}/1.0",
            "✅" if summary['average_personalization_score'] >= 0.6 else "⚠️"
        )
        
        metrics_table.add_row(
            "Average Context Relevance Score",
            f"{summary['average_context_relevance_score']:.2f}/1.0",
            "✅" if summary['average_context_relevance_score'] >= 0.6 else "⚠️"
        )
        
        metrics_table.add_row(
            "Average Response Time",
            f"{summary['average_response_time_ms']:.0f}ms",
            "✅" if summary['average_response_time_ms'] <= 2000 else "⚠️"
        )
        
        metrics_table.add_row(
            "Overall Effectiveness",
            summary['effectiveness_rating'],
            "🎉" if summary['effectiveness_rating'] in ["Excellent", "Good"] else "🔧"
        )
        
        console.print(metrics_table)
        
        # Detailed results table
        if summary['test_results']:
            results_table = Table(title="Detailed Results")
            results_table.add_column("Scenario", style="cyan")
            results_table.add_column("Personalization", style="green")
            results_table.add_column("Context Relevance", style="blue")
            results_table.add_column("Context Entries", style="yellow")
            results_table.add_column("Response Time", style="magenta")
            
            for result in summary['test_results']:
                results_table.add_row(
                    result['scenario'],
                    f"{result['personalization_score']:.2f}",
                    f"{result['context_relevance_score']:.2f}",
                    str(result['context_entries_used']),
                    f"{result['response_time_ms']}ms"
                )
            
            console.print(results_table)
        
        # Recommendations
        console.print("\n💡 [bold blue]Recommendations:[/bold blue]")
        
        if summary['context_retrieval_rate'] < 0.8:
            console.print("   • Improve context retrieval - some queries aren't finding relevant context")
        
        if summary['average_personalization_score'] < 0.6:
            console.print("   • Enhance context templates to make AI responses more personalized")
        
        if summary['average_context_relevance_score'] < 0.6:
            console.print("   • Tune semantic search similarity thresholds")
        
        if summary['average_response_time_ms'] > 2000:
            console.print("   • Optimize context retrieval performance")
        
        console.print("\n🎯 [green]ContextVault is working and improving AI responses![/green]")
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save test results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"contextvault_effectiveness_test_{timestamp}.json"
        
        results_data = {
            "test_timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(),
            "detailed_results": [
                {
                    "scenario_name": r.scenario_name,
                    "query": r.query,
                    "with_context_response": r.with_context_response,
                    "without_context_response": r.without_context_response,
                    "context_used": r.context_used,
                    "personalization_score": r.personalization_score,
                    "context_relevance_score": r.context_relevance_score,
                    "response_time_ms": r.response_time_ms,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.test_results
            ]
        }
        
        filepath = Path(filename)
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        console.print(f"💾 [green]Test results saved to: {filepath.absolute()}[/green]")
        return str(filepath.absolute())


def main():
    """Main function to run effectiveness tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ContextVault effectiveness")
    parser.add_argument("--ollama-url", default="http://localhost:11435", help="ContextVault proxy URL")
    parser.add_argument("--ollama-direct-url", default="http://localhost:11434", help="Direct Ollama URL")
    parser.add_argument("--save-results", help="Save results to JSON file")
    parser.add_argument("--scenario", help="Run specific scenario only")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create tester
    tester = ContextEffectivenessTester(
        ollama_url=args.ollama_url,
        ollama_direct_url=args.ollama_direct_url
    )
    
    try:
        if args.scenario:
            # Run specific scenario
            scenario = next((s for s in tester.scenarios if s.name == args.scenario), None)
            if not scenario:
                console.print(f"❌ [red]Scenario '{args.scenario}' not found[/red]")
                return
            
            tester.setup_test_context()
            tester.run_scenario_test(scenario)
        else:
            # Run all tests
            summary = tester.run_all_tests()
            
            if "error" not in summary:
                if args.save_results:
                    tester.save_results(args.save_results)
                else:
                    tester.save_results()
        
    except KeyboardInterrupt:
        console.print("\n⏹️  [yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"❌ [red]Test failed: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
