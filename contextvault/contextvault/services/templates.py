"""
Context Injection Templates for ContextVault

This module provides various templates for injecting context into AI prompts.
Each template is designed to maximize the AI's use of provided context.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of context injection templates."""
    ASSISTANT = "assistant"
    CONVERSATION = "conversation"
    EXPERT = "expert"
    PERSONAL = "personal"
    DIRECT = "direct"
    ROLEPLAY = "roleplay"


class ContextTemplate:
    """A context injection template with metadata."""
    
    def __init__(
        self,
        name: str,
        template: str,
        description: str,
        template_type: TemplateType,
        strength: int = 5,  # 1-10 scale of how directive it is
        use_cases: List[str] = None
    ):
        self.name = name
        self.template = template
        self.description = description
        self.template_type = template_type
        self.strength = strength
        self.use_cases = use_cases or []


# Template definitions - ordered from subtle to very directive
TEMPLATES = {
    # WEAK TEMPLATES (for reference - what NOT to do)
    "weak_original": ContextTemplate(
        name="Original Weak Template",
        template="""Previous Context:
{context_entries}

Current Conversation:
{user_prompt}""",
        description="WEAK: The original template that doesn't work well",
        template_type=TemplateType.CONVERSATION,
        strength=2,
        use_cases=["Example of ineffective template"]
    ),
    
    # STRONG TEMPLATES (what we should use)
    "direct_instruction": ContextTemplate(
        name="Direct Instruction",
        template="""IMPORTANT CONTEXT ABOUT THE USER:
{context_entries}

Based on the above personal information about the user, please respond to their question: {user_prompt}

Make sure to reference specific details from their personal context when relevant. Don't ignore the context - use it to give a personalized response.""",
        description="Direct and clear instruction to use context",
        template_type=TemplateType.DIRECT,
        strength=8,
        use_cases=["General queries", "Personal questions", "Preference-based questions"]
    ),
    
    "assistant_roleplay": ContextTemplate(
        name="Personal Assistant",
        template="""You are a personal assistant who knows the following about your user:

{context_entries}

Your user is asking: {user_prompt}

Respond as their knowledgeable personal assistant who remembers these details about them. Reference specific information from what you know about them when it's relevant to their question.""",
        description="Roleplay as a personal assistant with memory",
        template_type=TemplateType.ROLEPLAY,
        strength=9,
        use_cases=["Personal assistant interactions", "Productivity questions"]
    ),
    
    "expert_consultant": ContextTemplate(
        name="Expert Consultant",
        template="""CLIENT PROFILE:
{context_entries}

CONSULTATION REQUEST: {user_prompt}

As an expert consultant, provide advice based on your client's specific background, preferences, and situation detailed above. Tailor your response to their unique context - don't give generic advice.""",
        description="Professional consultant who knows client background",
        template_type=TemplateType.EXPERT,
        strength=9,
        use_cases=["Professional advice", "Technical consulting", "Specialized guidance"]
    ),
    
    "conversation_memory": ContextTemplate(
        name="Conversation with Memory",
        template="""Here's what I remember about our previous conversations and your background:

{context_entries}

Now you're asking: {user_prompt}

I'll respond based on what I know about you from our history together.""",
        description="Conversational style emphasizing shared history",
        template_type=TemplateType.CONVERSATION,
        strength=7,
        use_cases=["Casual conversation", "Follow-up questions", "Ongoing discussions"]
    ),
    
    "personal_friend": ContextTemplate(
        name="Personal Friend",
        template="""Hey! I remember these things about you:

{context_entries}

You're asking: {user_prompt}

Let me answer based on what I know about your situation, preferences, and background!""",
        description="Friendly, casual tone with personal knowledge",
        template_type=TemplateType.PERSONAL,
        strength=8,
        use_cases=["Casual interactions", "Personal questions", "Friendly advice"]
    ),
    
    "forced_reference": ContextTemplate(
        name="Forced Context Reference",
        template="""USER BACKGROUND AND PREFERENCES:
{context_entries}

QUESTION: {user_prompt}

INSTRUCTION: You MUST reference at least one specific detail from the user's background when answering. Start your response by acknowledging something specific about them from the context above, then answer their question.""",
        description="VERY directive - forces reference to context",
        template_type=TemplateType.DIRECT,
        strength=10,
        use_cases=["Testing", "When context must be acknowledged", "Debugging"]
    ),
    
    "system_prompt": ContextTemplate(
        name="System-Style Prompt",
        template="""SYSTEM: The following user information is available:
{context_entries}

USER: {user_prompt}

ASSISTANT: I'll respond using the provided user information to give a personalized answer.""",
        description="System/user/assistant format for better model following",
        template_type=TemplateType.ASSISTANT,
        strength=8,
        use_cases=["Models that respond well to system prompts", "Structured interactions"]
    )
}


class TemplateManager:
    """Manages context injection templates and selection logic."""
    
    def __init__(self):
        self.templates = TEMPLATES
        self.default_template = "direct_instruction"
        self.current_template = self.default_template
    
    def get_template(self, template_name: Optional[str] = None) -> ContextTemplate:
        """Get a template by name, or return current/default."""
        name = template_name or self.current_template
        if name not in self.templates:
            logger.warning(f"Template '{name}' not found, using default")
            name = self.default_template
        return self.templates[name]
    
    def set_current_template(self, template_name: str) -> bool:
        """Set the current active template."""
        if template_name in self.templates:
            self.current_template = template_name
            logger.info(f"Active template set to: {template_name}")
            return True
        else:
            logger.error(f"Template '{template_name}' not found")
            return False
    
    def get_all_templates(self) -> List[ContextTemplate]:
        """Get all available templates."""
        return list(self.templates.values())
    
    def get_all_templates_names(self) -> List[str]:
        """Get all available template names."""
        return list(self.templates.keys())
    
    def set_active_template(self, template_name: str) -> ContextTemplate:
        """Set the active template and return it."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        self.current_template = template_name
        logger.info(f"Active template set to: {template_name}")
        return self.templates[template_name]
    
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """List all available templates with metadata."""
        return {
            name: {
                "description": template.description,
                "type": template.template_type.value,
                "strength": template.strength,
                "use_cases": template.use_cases
            }
            for name, template in self.templates.items()
        }
    
    def get_template_by_type(self, template_type: TemplateType) -> List[str]:
        """Get template names by type."""
        return [
            name for name, template in self.templates.items()
            if template.template_type == template_type
        ]
    
    def get_strongest_templates(self, min_strength: int = 8) -> List[str]:
        """Get templates above a certain strength threshold."""
        return [
            name for name, template in self.templates.items()
            if template.strength >= min_strength
        ]
    
    def format_context(
        self,
        context_entries: List[str],
        user_prompt: str,
        template_name: Optional[str] = None
    ) -> str:
        """Format context using the specified template."""
        template = self.get_template(template_name)
        
        # Join context entries with clear separation
        formatted_context = "\n".join([
            f"• {entry}" for entry in context_entries
        ])
        
        # Apply the template
        formatted_prompt = template.template.format(
            context_entries=formatted_context,
            user_prompt=user_prompt
        )
        
        logger.debug(f"Using template: {template.name}")
        logger.debug(f"Context entries: {len(context_entries)}")
        logger.debug(f"Formatted prompt length: {len(formatted_prompt)}")
        
        return formatted_prompt
    
    def select_best_template(
        self,
        context_types: List[str],
        query_type: str = "general"
    ) -> str:
        """Intelligently select the best template based on context and query."""
        
        # Simple heuristics for template selection
        if "personal" in context_types or "preferences" in context_types:
            return "personal_friend"
        elif "work" in context_types or "professional" in context_types:
            return "expert_consultant"
        elif query_type == "conversation":
            return "conversation_memory"
        else:
            return "direct_instruction"


# Global template manager instance
template_manager = TemplateManager()


def get_template_manager() -> TemplateManager:
    """Get the global template manager instance."""
    return template_manager


def format_context_with_template(
    context_entries: List[str],
    user_prompt: str,
    template_name: Optional[str] = None
) -> str:
    """Convenience function to format context with a template."""
    return template_manager.format_context(context_entries, user_prompt, template_name)


# Example usage and testing functions
def demo_templates():
    """Demonstrate different templates with sample data."""
    sample_context = [
        "I am a software engineer who loves Python and testing",
        "I prefer detailed explanations and want to understand how systems work",
        "I built ContextVault to give local AI models persistent memory"
    ]
    sample_prompt = "What programming languages should I learn next?"
    
    print("TEMPLATE COMPARISON DEMO")
    print("=" * 60)
    
    for name, template in TEMPLATES.items():
        print(f"\n🔹 {template.name} (Strength: {template.strength}/10)")
        print(f"   Type: {template.template_type.value}")
        print(f"   Description: {template.description}")
        print("\n📝 Generated Prompt:")
        print("-" * 40)
        
        formatted = template_manager.format_context(
            sample_context, sample_prompt, name
        )
        print(formatted)
        print("-" * 40)


if __name__ == "__main__":
    demo_templates()
