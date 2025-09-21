#!/usr/bin/env python3
"""
Template Effectiveness Testing for ContextVault

Tests different context injection templates to measure their effectiveness
at making AI responses more personalized and context-aware.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import httpx
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from contextvault.services.templates import template_manager, TEMPLATES
from contextvault.database import get_db_context
from contextvault.services.vault import VaultService

console = Console()


class TemplateTestResult:
    """Results from testing a template."""
    
    def __init__(
        self,
        template_name: str,
        context_entries: List[str],
        user_prompt: str,
        ai_response: str,
        response_time: float,
        context_usage_score: float = 0.0,
        personalization_score: float = 0.0
    ):
        self.template_name = template_name
        self.context_entries = context_entries
        self.user_prompt = user_prompt
        self.ai_response = ai_response
        self.response_time = response_time
        self.context_usage_score = context_usage_score
        self.personalization_score = personalization_score
        self.timestamp = datetime.now()


class TemplateEffectivenessTester:
    """Tests template effectiveness with real AI models."""
    
    def __init__(
        self,
        proxy_url: str = "http://localhost:11435",
        ollama_url: str = "http://localhost:11434",
        model: str = "mistral:latest"
    ):
        self.proxy_url = proxy_url
        self.ollama_url = ollama_url
        self.model = model
        self.results: List[TemplateTestResult] = []
    
    async def test_template(
        self,
        template_name: str,
        context_entries: List[str],
        user_prompt: str,
        use_proxy: bool = True
    ) -> TemplateTestResult:
        """Test a specific template with given context and prompt."""
        
        start_time = time.time()
        
        try:
            if use_proxy:
                # Test through ContextVault proxy (with context injection)
                url = f"{self.proxy_url}/api/generate"
                response = await self._make_request(url, user_prompt)
            else:
                # Test direct to Ollama (without context injection)
                url = f"{self.ollama_url}/api/generate"
                response = await self._make_request(url, user_prompt)
            
            response_time = time.time() - start_time
            
            # Score the response
            context_score = self._score_context_usage(response, context_entries)
            personalization_score = self._score_personalization(response, context_entries)
            
            return TemplateTestResult(
                template_name=template_name,
                context_entries=context_entries,
                user_prompt=user_prompt,
                ai_response=response,
                response_time=response_time,
                context_usage_score=context_score,
                personalization_score=personalization_score
            )
            
        except Exception as e:
            console.print(f"❌ Error testing template {template_name}: {e}")
            return TemplateTestResult(
                template_name=template_name,
                context_entries=context_entries,
                user_prompt=user_prompt,
                ai_response=f"ERROR: {str(e)}",
                response_time=0.0
            )
    
    async def _make_request(self, url: str, prompt: str) -> str:
        """Make request to AI model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 100,
                "temperature": 0.3  # Lower temperature for more consistent results
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No response")
    
    def _score_context_usage(self, response: str, context_entries: List[str]) -> float:
        """Score how well the response uses provided context (0-10)."""
        if not response or not context_entries:
            return 0.0
        
        response_lower = response.lower()
        total_score = 0.0
        
        for entry in context_entries:
            entry_words = entry.lower().split()
            matched_words = sum(1 for word in entry_words if word in response_lower)
            entry_score = (matched_words / len(entry_words)) * 10
            total_score += entry_score
        
        # Average across all context entries
        return min(total_score / len(context_entries), 10.0)
    
    def _score_personalization(self, response: str, context_entries: List[str]) -> float:
        """Score how personalized the response feels (0-10)."""
        if not response:
            return 0.0
        
        response_lower = response.lower()
        
        # Look for personal indicators
        personal_indicators = [
            "you are", "your", "based on", "remember", "know about you",
            "your background", "your preferences", "your situation",
            "given that you", "since you", "as someone who"
        ]
        
        score = 0.0
        for indicator in personal_indicators:
            if indicator in response_lower:
                score += 1.0
        
        # Check for specific context references
        for entry in context_entries:
            key_terms = [word for word in entry.split() if len(word) > 4]
            for term in key_terms[:3]:  # Check first 3 significant terms
                if term.lower() in response_lower:
                    score += 2.0
        
        return min(score, 10.0)
    
    async def compare_templates(
        self,
        context_entries: List[str],
        user_prompt: str,
        template_names: Optional[List[str]] = None
    ) -> List[TemplateTestResult]:
        """Compare multiple templates with the same context and prompt."""
        
        if template_names is None:
            # Test the strongest templates by default
            template_names = template_manager.get_strongest_templates(min_strength=7)
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing templates...", total=len(template_names))
            
            for template_name in template_names:
                progress.update(task, description=f"Testing {template_name}...")
                
                # Set the template for ContextVault to use
                template_manager.set_current_template(template_name)
                
                # Wait a moment for the change to propagate
                await asyncio.sleep(0.5)
                
                result = await self.test_template(
                    template_name, context_entries, user_prompt, use_proxy=True
                )
                results.append(result)
                
                progress.advance(task)
        
        # Also test direct Ollama (no context) for comparison
        console.print("🔍 Testing direct Ollama (no context) for comparison...")
        direct_result = await self.test_template(
            "direct_ollama", context_entries, user_prompt, use_proxy=False
        )
        results.append(direct_result)
        
        self.results.extend(results)
        return results
    
    def print_comparison_results(self, results: List[TemplateTestResult]):
        """Print a comparison table of template results."""
        
        table = Table(title="Template Effectiveness Comparison")
        table.add_column("Template", style="cyan")
        table.add_column("Context Score", justify="center")
        table.add_column("Personal Score", justify="center")
        table.add_column("Response Time", justify="center")
        table.add_column("Response Preview", style="green")
        
        # Sort by combined score
        sorted_results = sorted(
            results,
            key=lambda r: r.context_usage_score + r.personalization_score,
            reverse=True
        )
        
        for result in sorted_results:
            context_score = f"{result.context_usage_score:.1f}/10"
            personal_score = f"{result.personalization_score:.1f}/10"
            response_time = f"{result.response_time:.2f}s"
            preview = result.ai_response[:80] + "..." if len(result.ai_response) > 80 else result.ai_response
            
            # Color code the scores
            if result.context_usage_score >= 7:
                context_score = f"[green]{context_score}[/green]"
            elif result.context_usage_score >= 4:
                context_score = f"[yellow]{context_score}[/yellow]"
            else:
                context_score = f"[red]{context_score}[/red]"
            
            if result.personalization_score >= 7:
                personal_score = f"[green]{personal_score}[/green]"
            elif result.personalization_score >= 4:
                personal_score = f"[yellow]{personal_score}[/yellow]"
            else:
                personal_score = f"[red]{personal_score}[/red]"
            
            table.add_row(
                result.template_name,
                context_score,
                personal_score,
                response_time,
                preview
            )
        
        console.print(table)
        
        # Show best template recommendation
        if sorted_results:
            best = sorted_results[0]
            console.print(Panel(
                f"🏆 Best Template: [bold cyan]{best.template_name}[/bold cyan]\n"
                f"Context Usage: {best.context_usage_score:.1f}/10\n"
                f"Personalization: {best.personalization_score:.1f}/10\n"
                f"Total Score: {best.context_usage_score + best.personalization_score:.1f}/20",
                title="Recommendation"
            ))
    
    def save_results(self, filename: str = "template_test_results.json"):
        """Save test results to a JSON file."""
        results_data = []
        for result in self.results:
            results_data.append({
                "template_name": result.template_name,
                "context_entries": result.context_entries,
                "user_prompt": result.user_prompt,
                "ai_response": result.ai_response,
                "response_time": result.response_time,
                "context_usage_score": result.context_usage_score,
                "personalization_score": result.personalization_score,
                "timestamp": result.timestamp.isoformat()
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        console.print(f"✅ Results saved to {filename}")


# Pre-defined test scenarios
TEST_SCENARIOS = [
    {
        "name": "Personal Preferences",
        "context": [
            "I am a software engineer who loves Python and FastAPI",
            "I prefer detailed explanations and want to understand how systems work",
            "I built ContextVault to give local AI models persistent memory"
        ],
        "prompts": [
            "What programming languages should I learn next?",
            "How should I approach testing in my projects?",
            "What do you know about me?"
        ]
    },
    {
        "name": "Work Context",
        "context": [
            "I work as a senior backend developer at a fintech company",
            "I specialize in microservices architecture and API design",
            "I'm currently leading a team of 5 developers"
        ],
        "prompts": [
            "How should I handle technical debt in my current project?",
            "What's the best way to mentor junior developers?",
            "Should I consider a new job opportunity?"
        ]
    },
    {
        "name": "Hobby Context",
        "context": [
            "I love photography, especially landscape and street photography",
            "I own a Canon EOS R5 and several prime lenses",
            "I'm planning a photography trip to Iceland next month"
        ],
        "prompts": [
            "What camera settings should I use?",
            "How should I prepare for my upcoming trip?",
            "What's your opinion on my photography equipment?"
        ]
    }
]


@click.command()
@click.option('--scenario', type=click.Choice(['personal', 'work', 'hobby', 'all']), 
              default='personal', help='Test scenario to run')
@click.option('--templates', help='Comma-separated list of templates to test')
@click.option('--model', default='mistral:latest', help='AI model to test with')
@click.option('--save', is_flag=True, help='Save results to JSON file')
@click.option('--demo', is_flag=True, help='Show template demo without testing')
def main(scenario: str, templates: Optional[str], model: str, save: bool, demo: bool):
    """Test context injection template effectiveness."""
    
    console.print("[bold blue]ContextVault Template Effectiveness Tester[/bold blue]")
    console.print("=" * 60)
    
    if demo:
        from contextvault.services.templates import demo_templates
        demo_templates()
        return
    
    # Select test scenario
    if scenario == 'all':
        scenarios = TEST_SCENARIOS
    else:
        scenario_map = {
            'personal': TEST_SCENARIOS[0],
            'work': TEST_SCENARIOS[1],
            'hobby': TEST_SCENARIOS[2]
        }
        scenarios = [scenario_map[scenario]]
    
    # Parse template list
    template_list = None
    if templates:
        template_list = [t.strip() for t in templates.split(',')]
    
    # Run tests
    tester = TemplateEffectivenessTester(model=model)
    
    async def run_tests():
        for test_scenario in scenarios:
            console.print(f"\n🧪 Testing Scenario: [bold]{test_scenario['name']}[/bold]")
            
            for prompt in test_scenario['prompts']:
                console.print(f"\n📝 Prompt: [italic]{prompt}[/italic]")
                
                results = await tester.compare_templates(
                    test_scenario['context'],
                    prompt,
                    template_list
                )
                
                tester.print_comparison_results(results)
                console.print("\n" + "─" * 60)
    
    # Run the async tests
    try:
        asyncio.run(run_tests())
        
        if save:
            tester.save_results()
            
    except KeyboardInterrupt:
        console.print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        console.print(f"❌ Error running tests: {e}")


if __name__ == "__main__":
    main()
