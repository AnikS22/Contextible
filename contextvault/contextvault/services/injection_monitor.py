"""
Real-time Context Injection Monitor
Live dashboard showing context injection happening in real-time
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import deque

from .injection_debugger import injection_debugger


@dataclass
class InjectionEvent:
    """A real-time injection event."""
    timestamp: float
    event_type: str  # 'start', 'context_retrieved', 'template_selected', 'prompt_assembled', 'ai_response', 'complete'
    model_id: str
    data: Dict[str, Any]


class ContextInjectionMonitor:
    """Real-time monitor for context injection events."""
    
    def __init__(self, max_events: int = 100):
        self.events = deque(maxlen=max_events)
        self.active_injections = {}  # injection_id -> injection data
        self.stats = {
            "total_injections": 0,
            "successful_injections": 0,
            "failed_injections": 0,
            "average_context_entries": 0.0,
            "average_injection_time": 0.0,
            "templates_used": {},
            "models_used": {}
        }
    
    def log_event(self, event_type: str, model_id: str, data: Dict[str, Any], injection_id: Optional[str] = None):
        """Log a real-time injection event."""
        event = InjectionEvent(
            timestamp=time.time(),
            event_type=event_type,
            model_id=model_id,
            data=data
        )
        
        self.events.append(event)
        
        # Update active injection tracking
        if injection_id:
            if injection_id not in self.active_injections:
                self.active_injections[injection_id] = {
                    "start_time": time.time(),
                    "model_id": model_id,
                    "events": []
                }
            
            self.active_injections[injection_id]["events"].append(event)
        
        # Update stats
        self._update_stats(event, injection_id)
    
    def get_live_dashboard_data(self) -> Dict[str, Any]:
        """Get data for live dashboard."""
        recent_events = list(self.events)[-10:]  # Last 10 events
        
        return {
            "timestamp": time.time(),
            "recent_events": [
                {
                    "time": datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S"),
                    "type": event.event_type,
                    "model": event.model_id,
                    "data": event.data
                }
                for event in recent_events
            ],
            "active_injections": len(self.active_injections),
            "stats": self.stats,
            "event_count": len(self.events)
        }
    
    def get_injection_pipeline_view(self, injection_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed view of a specific injection pipeline."""
        if injection_id not in self.active_injections:
            return None
        
        injection_data = self.active_injections[injection_id]
        events = injection_data["events"]
        
        # Organize events by step
        pipeline_steps = {
            "start": None,
            "context_retrieved": None,
            "template_selected": None,
            "context_formatted": None,
            "prompt_assembled": None,
            "ai_response": None,
            "complete": None
        }
        
        for event in events:
            if event.event_type in pipeline_steps:
                pipeline_steps[event.event_type] = {
                    "timestamp": event.timestamp,
                    "data": event.data
                }
        
        return {
            "injection_id": injection_id,
            "model_id": injection_data["model_id"],
            "start_time": injection_data["start_time"],
            "duration": time.time() - injection_data["start_time"],
            "pipeline_steps": pipeline_steps,
            "completed": pipeline_steps["complete"] is not None
        }
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        return {
            "monitoring_started": len(self.events) > 0,
            "total_events": len(self.events),
            "active_injections": len(self.active_injections),
            "stats": self.stats,
            "recent_activity": self._get_recent_activity_summary()
        }
    
    def _update_stats(self, event: InjectionEvent, injection_id: Optional[str]):
        """Update monitoring statistics."""
        if event.event_type == "start":
            self.stats["total_injections"] += 1
            self.stats["models_used"][event.model_id] = self.stats["models_used"].get(event.model_id, 0) + 1
        
        elif event.event_type == "complete":
            if injection_id and injection_id in self.active_injections:
                injection_data = self.active_injections[injection_id]
                duration = time.time() - injection_data["start_time"]
                
                # Update success/failure
                if event.data.get("success", False):
                    self.stats["successful_injections"] += 1
                else:
                    self.stats["failed_injections"] += 1
                
                # Update average injection time
                total_injections = self.stats["successful_injections"] + self.stats["failed_injections"]
                if total_injections > 0:
                    current_avg = self.stats["average_injection_time"]
                    self.stats["average_injection_time"] = (current_avg * (total_injections - 1) + duration) / total_injections
        
        elif event.event_type == "template_selected":
            template = event.data.get("selected_template", "unknown")
            self.stats["templates_used"][template] = self.stats["templates_used"].get(template, 0) + 1
        
        elif event.event_type == "context_retrieved":
            context_count = event.data.get("contexts_found", 0)
            total_injections = self.stats["successful_injections"] + self.stats["failed_injections"] + 1
            current_avg = self.stats["average_context_entries"]
            self.stats["average_context_entries"] = (current_avg * (total_injections - 1) + context_count) / total_injections
    
    def _get_recent_activity_summary(self) -> Dict[str, Any]:
        """Get summary of recent activity."""
        if not self.events:
            return {"message": "No recent activity"}
        
        recent_events = list(self.events)[-20:]  # Last 20 events
        
        # Count event types
        event_counts = {}
        for event in recent_events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Get most recent injection
        recent_injection = None
        for event in reversed(recent_events):
            if event.event_type == "start":
                recent_injection = {
                    "model": event.model_id,
                    "timestamp": event.timestamp,
                    "time_ago": time.time() - event.timestamp
                }
                break
        
        return {
            "event_counts": event_counts,
            "most_recent_injection": recent_injection,
            "time_range": {
                "oldest": recent_events[0].timestamp if recent_events else None,
                "newest": recent_events[-1].timestamp if recent_events else None
            }
        }
    
    def clear_old_data(self, max_age_hours: int = 24):
        """Clear old monitoring data."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clear old events
        self.events = deque(
            (event for event in self.events if event.timestamp > cutoff_time),
            maxlen=self.events.maxlen
        )
        
        # Clear old active injections
        old_injections = [
            injection_id for injection_id, data in self.active_injections.items()
            if data["start_time"] < cutoff_time
        ]
        for injection_id in old_injections:
            del self.active_injections[injection_id]


# Global injection monitor instance
injection_monitor = ContextInjectionMonitor()
