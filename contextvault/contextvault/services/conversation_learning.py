"""Conversation learning service for extracting and saving context from conversations."""

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..database import get_db_context
from ..models import ContextEntry, ContextType
from ..services.vault import VaultService

logger = logging.getLogger(__name__)


class ConversationLearningService:
    """
    Service for automatically extracting and learning from conversations.
    
    This service analyzes user prompts and AI responses to identify:
    - Personal preferences and opinions
    - Facts about the user
    - Goals and projects
    - Relationships and connections
    - Skills and expertise
    - And other contextual information
    """
    
    def __init__(self, vault_service: Optional[VaultService] = None):
        """Initialize the conversation learning service."""
        self.vault_service = vault_service or VaultService()
        
        # Patterns for identifying different types of information
        self.patterns = {
            'personal_facts': [
                r'(?:i am|i\'m|my name is|i live in|i work at|i study at) (.+?)(?:\.|,|$)',
                r'(?:i have|i own|i like|i enjoy|i prefer|i love|i hate|i dislike) (.+?)(?:\.|,|$)',
                r'(?:i am from|i was born in|i grew up in) (.+?)(?:\.|,|$)',
                r'(?:my (?:favorite|favourite)|i like|i enjoy) (.+?)(?:\.|,|$)',
                r'(?:i\'m allergic to|i have allergies to) (.+?)(?:\.|,|$)',
                r'(?:i own|i have) (?:a|an|two|three|some) (.+?)(?:\.|,|$)',
            ],
            'goals_projects': [
                r'(?:i want to|i\'m trying to|i\'m working on|my goal is to|i hope to) (.+?)(?:\.|,|$)',
                r'(?:i\'m building|i\'m creating|i\'m developing) (.+?)(?:\.|,|$)',
                r'(?:my project|my startup|my company) (.+?)(?:\.|,|$)',
                r'(?:i\'m learning|i want to learn|i need to learn) (.+?)(?:\.|,|$)',
                r'(?:deadline|due date|finish by|complete by) (.+?)(?:\.|,|$)',
            ],
            'preferences': [
                r'(?:i prefer|i like|i enjoy|i love|i hate|i dislike) (.+?)(?:over|instead of|rather than) (.+?)(?:\.|,|$)',
                r'(?:i prefer|i like|i enjoy|i love|i hate|i dislike) (.+?)(?:\.|,|$)',
                r'(?:my favorite|my favourite) (.+?)(?:is|are) (.+?)(?:\.|,|$)',
                r'(?:i use|i work with|i code in|i develop with) (.+?)(?:\.|,|$)',
            ],
            'relationships': [
                r'(?:my (?:wife|husband|partner|boyfriend|girlfriend|spouse)) (.+?)(?:\.|,|$)',
                r'(?:my (?:son|daughter|child|children)) (.+?)(?:\.|,|$)',
                r'(?:my (?:mom|dad|mother|father|parents)) (.+?)(?:\.|,|$)',
                r'(?:my (?:friend|colleague|boss|manager)) (.+?)(?:\.|,|$)',
                r'(?:i work with|i collaborate with) (.+?)(?:\.|,|$)',
            ],
            'skills_expertise': [
                r'(?:i know|i\'m good at|i\'m skilled in|i\'m expert in|i specialize in) (.+?)(?:\.|,|$)',
                r'(?:i have experience with|i\'ve worked with|i\'m familiar with) (.+?)(?:\.|,|$)',
                r'(?:my background is in|i studied|i majored in) (.+?)(?:\.|,|$)',
                r'(?:years of experience|i\'ve been working with) (.+?)(?:\.|,|$)',
            ],
            'schedule_time': [
                r'(?:i work|i have meetings|i have appointments) (.+?)(?:\.|,|$)',
                r'(?:my schedule|i\'m busy|i\'m free) (.+?)(?:\.|,|$)',
                r'(?:i wake up|i go to bed|i have lunch|i have dinner) (.+?)(?:\.|,|$)',
                r'(?:weekends|weekdays|mornings|evenings) (.+?)(?:\.|,|$)',
            ]
        }
        
        # Keywords that indicate important information
        self.importance_keywords = [
            'important', 'crucial', 'critical', 'essential', 'key', 'main',
            'favorite', 'favourite', 'love', 'hate', 'prefer', 'always',
            'never', 'always', 'usually', 'typically', 'often', 'sometimes'
        ]
        
        # Context types mapping
        self.context_type_mapping = {
            'personal_facts': ContextType.PREFERENCE,
            'goals_projects': ContextType.NOTE,
            'preferences': ContextType.PREFERENCE,
            'relationships': ContextType.NOTE,
            'skills_expertise': ContextType.PREFERENCE,
            'schedule_time': ContextType.NOTE,
        }
    
    async def learn_from_conversation(
        self,
        user_prompt: str,
        ai_response: str,
        model_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[ContextEntry]:
        """
        Learn from a conversation by extracting relevant information.
        
        Args:
            user_prompt: The user's input/prompt
            ai_response: The AI's response
            model_id: The AI model used
            session_id: Session ID for tracking
            user_id: User ID for multi-user support
            
        Returns:
            List of newly created context entries
        """
        extracted_contexts = []
        
        try:
            # Extract from user prompt
            user_contexts = self._extract_from_text(
                user_prompt, 
                source="user_prompt",
                model_id=model_id,
                session_id=session_id,
                user_id=user_id
            )
            extracted_contexts.extend(user_contexts)
            
            # Extract from AI response (if it contains user-specific information)
            ai_contexts = self._extract_from_ai_response(
                ai_response,
                model_id=model_id,
                session_id=session_id,
                user_id=user_id
            )
            extracted_contexts.extend(ai_contexts)
            
            # Filter out duplicates and low-quality extractions
            filtered_contexts = self._filter_extractions(extracted_contexts)
            
            # Save to vault
            saved_contexts = []
            for context_data in filtered_contexts:
                try:
                    entry = self.vault_service.save_context(
                        content=context_data['content'],
                        context_type=context_data['context_type'],
                        source=context_data['source'],
                        tags=context_data['tags'],
                        metadata=context_data['metadata'],
                        user_id=user_id,
                        session_id=session_id
                    )
                    saved_contexts.append(entry)
                    logger.info(f"Learned new context: {context_data['content'][:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Failed to save extracted context: {e}")
            
            return saved_contexts
            
        except Exception as e:
            logger.error(f"Conversation learning failed: {e}", exc_info=True)
            return []
    
    def _extract_from_text(
        self,
        text: str,
        source: str,
        model_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract context from a text string."""
        extracted = []
        
        # Clean and normalize text
        text = text.strip()
        if len(text) < 10:  # Skip very short texts
            return extracted
        
        # Extract different types of information
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Get the extracted content
                    if match.groups():
                        content = match.group(1).strip()
                        
                        # Skip if too short or too generic
                        if len(content) < 3 or self._is_generic_content(content):
                            continue
                        
                        # Determine importance
                        importance = self._calculate_importance(text, content)
                        if importance < 0.3:  # Skip low-importance extractions
                            continue
                        
                        # Create context entry
                        context_data = {
                            'content': content,
                            'context_type': self.context_type_mapping[category],
                            'source': source,
                            'tags': [category, 'learned'],
                            'metadata': {
                                'extraction_method': 'pattern_matching',
                                'category': category,
                                'pattern': pattern,
                                'importance_score': importance,
                                'model_id': model_id,
                                'extracted_at': datetime.utcnow().isoformat()
                            },
                            'session_id': session_id,
                            'user_id': user_id
                        }
                        
                        extracted.append(context_data)
        
        return extracted
    
    def _extract_from_ai_response(
        self,
        ai_response: str,
        model_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract user-specific information from AI responses."""
        extracted = []
        
        # Look for patterns where AI is referencing user information
        ai_patterns = [
            r'(?:based on|according to|i see that|i know that|you mentioned that) (.+?)(?:\.|,|$)',
            r'(?:you are|you\'re|you have|you work|you live|you like) (.+?)(?:\.|,|$)',
            r'(?:your (?:name|location|job|hobby|preference|favorite)) (.+?)(?:\.|,|$)',
        ]
        
        for pattern in ai_patterns:
            matches = re.finditer(pattern, ai_response, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                if match.groups():
                    content = match.group(1).strip()
                    
                    # Skip if too short or generic
                    if len(content) < 5 or self._is_generic_content(content):
                        continue
                    
                    # Create context entry
                    context_data = {
                        'content': content,
                        'context_type': ContextType.NOTE,
                        'source': 'ai_response',
                        'tags': ['learned', 'ai_reference'],
                        'metadata': {
                            'extraction_method': 'ai_response_parsing',
                            'importance_score': 0.7,  # AI references are usually important
                            'model_id': model_id,
                            'extracted_at': datetime.utcnow().isoformat()
                        },
                        'session_id': session_id,
                        'user_id': user_id
                    }
                    
                    extracted.append(context_data)
        
        return extracted
    
    def _is_generic_content(self, content: str) -> bool:
        """Check if content is too generic to be useful."""
        generic_phrases = [
            'a person', 'someone', 'something', 'things', 'stuff',
            'i think', 'i believe', 'i guess', 'maybe', 'perhaps',
            'it depends', 'i don\'t know', 'not sure'
        ]
        
        content_lower = content.lower()
        for phrase in generic_phrases:
            if phrase in content_lower:
                return True
        
        # Check if it's just common words
        words = content.split()
        if len(words) <= 2:
            return True
        
        return False
    
    def _calculate_importance(self, full_text: str, extracted_content: str) -> float:
        """Calculate importance score for extracted content."""
        score = 0.5  # Base score
        
        full_text_lower = full_text.lower()
        content_lower = extracted_content.lower()
        
        # Increase score for importance keywords
        for keyword in self.importance_keywords:
            if keyword in full_text_lower:
                score += 0.1
        
        # Increase score for longer, more specific content
        if len(extracted_content) > 20:
            score += 0.2
        elif len(extracted_content) > 50:
            score += 0.3
        
        # Increase score for personal pronouns
        if any(pronoun in content_lower for pronoun in ['my', 'i', 'me', 'myself']):
            score += 0.2
        
        # Decrease score for questions
        if '?' in extracted_content:
            score -= 0.3
        
        return min(1.0, max(0.0, score))
    
    def _filter_extractions(self, extractions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and deduplicate extractions."""
        filtered = []
        seen_content = set()
        
        # Sort by importance score
        extractions.sort(key=lambda x: x['metadata'].get('importance_score', 0.5), reverse=True)
        
        for extraction in extractions:
            content = extraction['content'].lower().strip()
            
            # Skip if we've seen similar content
            if content in seen_content:
                continue
            
            # Skip if too similar to existing content
            is_duplicate = False
            for seen in seen_content:
                if self._calculate_similarity(content, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(extraction)
                seen_content.add(content)
        
        return filtered
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learned context."""
        try:
            with get_db_context() as db:
                # Count learned entries by category
                learned_entries = db.query(ContextEntry).filter(
                    ContextEntry.source.in_(['user_prompt', 'ai_response'])
                ).all()
                
                stats = {
                    'total_learned': len(learned_entries),
                    'by_source': {},
                    'by_context_type': {},
                    'recent_learning': 0
                }
                
                # Count by source
                for entry in learned_entries:
                    source = entry.source or 'unknown'
                    stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
                    
                    context_type = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
                    stats['by_context_type'][context_type] = stats['by_context_type'].get(context_type, 0) + 1
                    
                    # Count recent (last 24 hours)
                    if entry.created_at and (datetime.utcnow() - entry.created_at).total_seconds() < 86400:
                        stats['recent_learning'] += 1
                
                return stats
            
        except Exception as e:
            logger.error(f"Failed to get learning stats: {e}")
            return {'error': str(e)}


# Global instance
conversation_learning_service = ConversationLearningService()
