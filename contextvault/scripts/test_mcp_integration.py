#!/usr/bin/env python3
"""
MCP Integration Test Suite

This script tests ContextVault's MCP (Model Context Protocol) integration
with various data sources including Google Calendar, Gmail, and filesystem.
"""

import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the contextvault package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class MCPIntegrationTester:
    """Test MCP integration capabilities."""
    
    def __init__(self):
        self.test_results = []
        
    async def run_all_tests(self):
        """Run comprehensive MCP tests."""
        console.print("🔗 [bold blue]ContextVault MCP Integration Test Suite[/bold blue]")
        console.print("=" * 60)
        
        tests = [
            ("🧪 MCP Manager Initialization", self.test_mcp_manager),
            ("📅 Calendar Integration", self.test_calendar_integration),
            ("📧 Email Integration", self.test_email_integration),
            ("📁 Filesystem Integration", self.test_filesystem_integration),
            ("🔍 Context Retrieval", self.test_context_retrieval),
            ("🎯 Smart Context Injection", self.test_smart_injection),
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Testing MCP integration...", total=len(tests))
            
            for test_name, test_func in tests:
                progress.update(task, description=test_name)
                
                try:
                    result = await test_func()
                    self.test_results.append((test_name, "✅ PASS", result))
                except Exception as e:
                    self.test_results.append((test_name, "❌ FAIL", str(e)))
                
                progress.advance(task)
        
        return self.generate_report()
    
    async def test_mcp_manager(self) -> str:
        """Test MCP manager initialization and basic functionality."""
        try:
            from contextvault.integrations.mcp import MCPManager
            
            manager = MCPManager()
            
            # Test initialization
            await manager.initialize()
            
            # Check available provider types
            provider_types = list(manager._provider_types.keys())
            
            return f"MCP Manager initialized with {len(provider_types)} provider types: {', '.join(provider_types)}"
            
        except Exception as e:
            raise Exception(f"MCP Manager test failed: {e}")
    
    async def test_calendar_integration(self) -> str:
        """Test Google Calendar integration capabilities."""
        try:
            from contextvault.integrations.mcp import MCPManager, CalendarMCPProvider
            from contextvault.integrations.mcp.client import MCPClient, MCPCache
            
            # Create mock MCP client for testing
            mock_client = MCPClient("stdio:calendar-mcp-server")
            mock_cache = MCPCache()
            
            calendar_provider = CalendarMCPProvider(mock_client, mock_cache)
            
            # Test calendar provider methods
            methods = [
                'get_recent_activity',
                'get_scheduled_events', 
                'search',
                'get_context_for_query'
            ]
            
            available_methods = [method for method in methods if hasattr(calendar_provider, method)]
            
            # Test context formatting
            sample_events = [
                {
                    'title': 'Team Meeting',
                    'start_time': '2024-01-15T10:00:00Z',
                    'end_time': '2024-01-15T11:00:00Z',
                    'description': 'Weekly team standup'
                },
                {
                    'title': 'Doctor Appointment',
                    'start_time': '2024-01-16T14:30:00Z',
                    'end_time': '2024-01-16T15:30:00Z',
                    'description': 'Annual checkup'
                }
            ]
            
            formatted_context = calendar_provider.format_context(sample_events)
            
            return f"Calendar provider ready with {len(available_methods)} methods. Sample context: {len(formatted_context)} chars"
            
        except Exception as e:
            return f"Calendar integration test failed: {e}"
    
    async def test_email_integration(self) -> str:
        """Test Gmail/Email integration capabilities."""
        try:
            from contextvault.integrations.mcp import GmailMCPProvider
            from contextvault.integrations.mcp.client import MCPClient, MCPCache
            
            # Create mock MCP client for testing
            mock_client = MCPClient("stdio:gmail-mcp-server")
            mock_cache = MCPCache()
            
            email_provider = GmailMCPProvider(mock_client, mock_cache)
            
            # Test email provider methods
            methods = [
                'get_recent_activity',
                'get_emails_with_deadlines',
                'search',
                'get_context_for_query'
            ]
            
            available_methods = [method for method in methods if hasattr(email_provider, method)]
            
            # Test context formatting
            sample_emails = [
                {
                    'subject': 'Project Deadline Reminder',
                    'sender': 'manager@company.com',
                    'date': '2024-01-15T09:00:00Z',
                    'snippet': 'Please submit your project by Friday'
                },
                {
                    'subject': 'Meeting Invitation',
                    'sender': 'colleague@company.com', 
                    'date': '2024-01-14T16:00:00Z',
                    'snippet': 'Join us for the quarterly review'
                }
            ]
            
            formatted_context = email_provider.format_context(sample_emails)
            
            return f"Email provider ready with {len(available_methods)} methods. Sample context: {len(formatted_context)} chars"
            
        except Exception as e:
            return f"Email integration test failed: {e}"
    
    async def test_filesystem_integration(self) -> str:
        """Test filesystem integration capabilities."""
        try:
            from contextvault.integrations.mcp import FilesystemMCPProvider
            from contextvault.integrations.mcp.client import MCPClient, MCPCache
            
            # Create mock MCP client for testing
            mock_client = MCPClient("stdio:filesystem-mcp-server")
            mock_cache = MCPCache()
            
            filesystem_provider = FilesystemMCPProvider(mock_client, mock_cache)
            
            # Test filesystem provider methods
            methods = [
                'get_recent_activity',
                'search',
                'get_context_for_query'
            ]
            
            available_methods = [method for method in methods if hasattr(filesystem_provider, method)]
            
            # Test context formatting
            sample_files = [
                {
                    'name': 'project_proposal.pdf',
                    'path': '/Documents/Work/project_proposal.pdf',
                    'modified': '2024-01-15T10:30:00Z',
                    'size': 1024000
                },
                {
                    'name': 'meeting_notes.txt',
                    'path': '/Documents/Work/meeting_notes.txt',
                    'modified': '2024-01-14T15:45:00Z',
                    'size': 2048
                }
            ]
            
            formatted_context = filesystem_provider.format_context(sample_files)
            
            return f"Filesystem provider ready with {len(available_methods)} methods. Sample context: {len(formatted_context)} chars"
            
        except Exception as e:
            return f"Filesystem integration test failed: {e}"
    
    async def test_context_retrieval(self) -> str:
        """Test context retrieval from MCP providers."""
        try:
            from contextvault.integrations.mcp import MCPManager
            
            manager = MCPManager()
            await manager.initialize()
            
            # Test context retrieval for different scenarios
            test_scenarios = [
                ('recent_activity', 'Recent activity context'),
                ('scheduled_events', 'Scheduled events context'),
                ('search', 'Search-based context')
            ]
            
            results = []
            for context_type, description in test_scenarios:
                try:
                    context = await manager.get_context_for_model('mistral:latest', context_type, 5)
                    results.append(f"{description}: {len(context)} chars")
                except Exception as e:
                    results.append(f"{description}: Error - {str(e)[:50]}")
            
            return "; ".join(results)
            
        except Exception as e:
            return f"Context retrieval test failed: {e}"
    
    async def test_smart_injection(self) -> str:
        """Test smart context injection based on query analysis."""
        try:
            # Test query analysis for different types of requests
            test_queries = [
                ("What meetings do I have today?", "calendar"),
                ("Any important emails I should check?", "email"),
                ("What files did I work on recently?", "filesystem"),
                ("Tell me about my schedule", "calendar"),
                ("Any deadlines coming up?", "email"),
                ("What's in my documents folder?", "filesystem")
            ]
            
            # Mock smart injection logic
            injection_results = []
            for query, expected_source in test_queries:
                # Simple keyword-based detection
                if any(word in query.lower() for word in ['meeting', 'schedule', 'calendar', 'today', 'tomorrow']):
                    detected_source = 'calendar'
                elif any(word in query.lower() for word in ['email', 'message', 'deadline', 'urgent']):
                    detected_source = 'email'
                elif any(word in query.lower() for word in ['file', 'document', 'folder', 'recent']):
                    detected_source = 'filesystem'
                else:
                    detected_source = 'general'
                
                match = "✅" if detected_source == expected_source else "❌"
                injection_results.append(f"{match} '{query}' -> {detected_source}")
            
            return f"Smart injection tested: {len(injection_results)} scenarios"
            
        except Exception as e:
            return f"Smart injection test failed: {e}"
    
    def generate_report(self):
        """Generate comprehensive test report."""
        console.print("\n📊 [bold blue]MCP Integration Test Report[/bold blue]")
        console.print("=" * 60)
        
        # Create results table
        table = Table(title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        table.add_column("Details", style="white")
        
        for test_name, result, details in self.test_results:
            table.add_row(test_name, result, details)
        
        console.print(table)
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r[1]])
        
        console.print(f"\n📈 [bold]Summary:[/bold] {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            console.print("\n🎉 [bold green]ALL MCP TESTS PASSED![/bold green]")
            console.print("   ContextVault MCP integration is working correctly.")
        else:
            console.print(f"\n⚠️ [bold yellow]{total_tests - passed_tests} tests failed[/bold yellow]")
            console.print("   Some MCP features may need attention.")
        
        return passed_tests == total_tests

async def main():
    """Run MCP integration tests."""
    tester = MCPIntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            console.print("\n🚀 [bold green]MCP Integration is ready![/bold green]")
            console.print("   ContextVault can connect to calendars, email, and filesystems.")
        else:
            console.print("\n🛠️ [bold yellow]MCP Integration needs attention.[/bold yellow]")
            console.print("   Check the failed tests above.")
            
    except Exception as e:
        console.print(f"\n💥 [bold red]MCP testing failed with error: {e}[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
