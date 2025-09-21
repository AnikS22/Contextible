"""
Context Extraction Engine - Analyzes conversations to extract context
This service analyzes user prompts and AI responses to extract meaningful context
"""

import re
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.context import ContextType
from .conversation_logger import Conversation, ConversationMessage


class ExtractionConfidence(Enum):
    """Confidence levels for extracted context."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ExtractedContext:
    """A piece of context extracted from a conversation."""
    content: str
    context_type: ContextType
    confidence: ExtractionConfidence
    source: str  # conversation_id
    conversation_id: str
    message_id: str
    tags: List[str]
    metadata: Dict[str, Any]


class ContextExtractor:
    """Extracts context from conversations using pattern matching and analysis."""
    
    def __init__(self):
        # Define patterns for different types of information
        self.personal_info_patterns = {
            "name": [
                r"\b(?:my name is|i'm|i am|call me)\s+([A-Za-z\s]+)",
                r"\b(name|called)\s+([A-Za-z\s]+)",
            ],
            "location": [
                r"\b(?:i live in|i'm from|based in|located in)\s+([A-Za-z\s,]+)",
                r"\b(?:i'm in|living in)\s+([A-Za-z\s,]+)",
            ],
            "profession": [
                r"\b(?:i work as|i'm a|my job is|i do)\s+([A-Za-z\s]+)",
                r"\b(?:profession|career|occupation)\s+([A-Za-z\s]+)",
            ],
            "interests": [
                r"\b(?:i love|i enjoy|i like|i'm interested in|i'm passionate about)\s+([A-Za-z\s,]+)",
                r"\b(?:hobbies|interests)\s+([A-Za-z\s,]+)",
            ],
            "preferences": [
                r"\b(?:i prefer|i'd rather|i like|i don't like|i hate)\s+([A-Za-z\s,]+)",
                r"\b(?:favorite|best|worst)\s+([A-Za-z\s,]+)",
            ],
            "goals": [
                r"\b(?:i want to|i'm trying to|my goal is|i hope to)\s+([A-Za-z\s,]+)",
                r"\b(?:planning to|working on|building)\s+([A-Za-z\s,]+)",
            ],
            "current_projects": [
                r"\b(?:i'm working on|currently building|developing)\s+([A-Za-z\s,]+)",
                r"\b(?:project|building|creating)\s+([A-Za-z\s,]+)",
            ]
        }
        
        # Define patterns for facts and statements
        self.fact_patterns = [
            r"\b(?:i have|i own|i possess)\s+([A-Za-z\s,]+)",
            r"\b(?:i went to|i studied at|i graduated from)\s+([A-Za-z\s,]+)",
            r"\b(?:i have been|i've been)\s+([A-Za-z\s,]+)",
            r"\b(?:i used to|i previously)\s+([A-Za-z\s,]+)",
        ]
        
        # Define patterns for preferences and opinions
        self.preference_patterns = [
            r"\b(?:i think|i believe|in my opinion)\s+([A-Za-z\s,]+)",
            r"\b(?:i prefer|i'd rather|i like)\s+([A-Za-z\s,]+)",
            r"\b(?:i don't like|i hate|i dislike)\s+([A-Za-z\s,]+)",
            r"\b(?:i'm not a fan of|i'm not interested in)\s+([A-Za-z\s,]+)",
        ]
    
    def extract_from_conversation(self, conversation_id: str, conversation: Conversation) -> List[ExtractedContext]:
        """Extract context from a conversation."""
        extracted_contexts = []
        
        for message in conversation.messages:
            if message.role == "user":
                # Extract from user messages
                user_contexts = self._extract_from_user_prompt(message, conversation)
                extracted_contexts.extend(user_contexts)
            
            elif message.role == "assistant":
                # Extract from assistant messages (AI responses)
                assistant_contexts = self._extract_from_assistant_response(message, conversation)
                extracted_contexts.extend(assistant_contexts)
        
        return extracted_contexts
    
    def _extract_from_user_prompt(self, message: ConversationMessage, conversation: Conversation) -> List[ExtractedContext]:
        """Extract context from user prompts."""
        extracted_contexts = []
        content = message.content.lower()
        
        # Extract personal information
        for info_type, patterns in self.personal_info_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Handle tuple matches (capture groups)
                    if isinstance(match, tuple):
                        extracted_text = match[-1].strip()  # Take the last capture group
                    else:
                        extracted_text = match.strip()
                    
                    if extracted_text and len(extracted_text) > 2:
                        confidence = self._calculate_confidence(extracted_text, pattern, content)
                        
                        # Map info type to context type
                        context_type = self._map_info_type_to_context_type(info_type)
                        
                        extracted_context = ExtractedContext(
                            content=f"User {info_type}: {extracted_text}",
                            context_type=context_type,
                            confidence=confidence,
                            source="user_prompt",
                            conversation_id=conversation.id,
                            message_id=message.id,
                            tags=[info_type, 'auto_extracted'],
                            metadata={
                                "extraction_pattern": pattern,
                                "info_type": info_type,
                                "original_message": message.content[:100] + "..." if len(message.content) > 100 else message.content
                            }
                        )
                        extracted_contexts.append(extracted_context)
        
        # Extract facts
        for pattern in self.fact_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_text = match[-1].strip()
                else:
                    extracted_text = match.strip()
                
                if extracted_text and len(extracted_text) > 2:
                    confidence = self._calculate_confidence(extracted_text, pattern, content)
                    
                    extracted_context = ExtractedContext(
                        content=f"User fact: {extracted_text}",
                        context_type=ContextType.NOTE,
                        confidence=confidence,
                        source="user_prompt",
                        conversation_id=conversation.id,
                        message_id=message.id,
                        tags=['fact', 'auto_extracted'],
                        metadata={
                            "extraction_pattern": pattern,
                            "original_message": message.content[:100] + "..." if len(message.content) > 100 else message.content
                        }
                    )
                    extracted_contexts.append(extracted_context)
        
        # Extract preferences
        for pattern in self.preference_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_text = match[-1].strip()
                else:
                    extracted_text = match.strip()
                
                if extracted_text and len(extracted_text) > 2:
                    confidence = self._calculate_confidence(extracted_text, pattern, content)
                    
                    extracted_context = ExtractedContext(
                        content=f"User preference: {extracted_text}",
                        context_type=ContextType.PREFERENCE,
                        confidence=confidence,
                        source="user_prompt",
                        conversation_id=conversation.id,
                        message_id=message.id,
                        tags=['preference', 'auto_extracted'],
                        metadata={
                            "extraction_pattern": pattern,
                            "original_message": message.content[:100] + "..." if len(message.content) > 100 else message.content
                        }
                    )
                    extracted_contexts.append(extracted_context)
        
        return extracted_contexts
    
    def _extract_from_assistant_response(self, message: ConversationMessage, conversation: Conversation) -> List[ExtractedContext]:
        """Extract context from assistant responses."""
        extracted_contexts = []
        content = message.content.lower()
        
        # Look for references to user information in AI responses
        # This happens when the AI mentions something about the user based on previous context
        
        # Pattern: AI mentions user's name, location, job, etc.
        reference_patterns = [
            r"\b(?:you are|you're|you work as|you live in|you have)\s+([A-Za-z\s,]+)",
            r"\b(?:as a|since you're|given that you)\s+([A-Za-z\s,]+)",
            r"\b(?:based on|considering|given your)\s+([A-Za-z\s,]+)",
        ]
        
        for pattern in reference_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    extracted_text = match[-1].strip()
                else:
                    extracted_text = match.strip()
                
                if extracted_text and len(extracted_text) > 2:
                    confidence = self._calculate_confidence(extracted_text, pattern, content)
                    
                    extracted_context = ExtractedContext(
                        content=f"AI reference: {extracted_text}",
                        context_type=ContextType.NOTE,
                        confidence=confidence,
                        source="ai_response",
                        conversation_id=conversation.id,
                        message_id=message.id,
                        tags=['ai_reference', 'auto_extracted'],
                        metadata={
                            "extraction_pattern": pattern,
                            "original_message": message.content[:100] + "..." if len(message.content) > 100 else message.content
                        }
                    )
                    extracted_contexts.append(extracted_context)
        
        return extracted_contexts
    
    def _calculate_confidence(self, extracted_text: str, pattern: str, full_content: str) -> ExtractionConfidence:
        """Calculate confidence level for extracted context."""
        # Base confidence on various factors
        confidence_score = 0
        
        # Length of extracted text (longer is usually more specific)
        if len(extracted_text) > 10:
            confidence_score += 1
        elif len(extracted_text) > 5:
            confidence_score += 0.5
        
        # Presence of specific keywords that indicate certainty
        certainty_keywords = ["always", "never", "definitely", "certainly", "absolutely"]
        if any(keyword in extracted_text.lower() for keyword in certainty_keywords):
            confidence_score += 1
        
        # Pattern specificity (more specific patterns get higher confidence)
        if "my name is" in pattern or "i am" in pattern:
            confidence_score += 1
        elif "i prefer" in pattern or "i like" in pattern:
            confidence_score += 0.5
        
        # Context around the extraction
        if extracted_text in full_content:
            context_start = full_content.find(extracted_text.lower())
            if context_start > 0:
                # Check if there's good context before
                before_context = full_content[max(0, context_start-20):context_start]
                if any(word in before_context for word in ["i", "my", "me"]):
                    confidence_score += 0.5
        
        # Map score to confidence level
        if confidence_score >= 2:
            return ExtractionConfidence.HIGH
        elif confidence_score >= 1:
            return ExtractionConfidence.MEDIUM
        else:
            return ExtractionConfidence.LOW
    
    def _map_info_type_to_context_type(self, info_type: str) -> ContextType:
        """Map information type to context type."""
        mapping = {
            "name": ContextType.NOTE,
            "location": ContextType.NOTE,
            "profession": ContextType.NOTE,
            "interests": ContextType.PREFERENCE,
            "preferences": ContextType.PREFERENCE,
            "goals": ContextType.NOTE,
            "current_projects": ContextType.NOTE,
        }
        return mapping.get(info_type, ContextType.TEXT)
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            "personal_info_patterns": len(self.personal_info_patterns),
            "fact_patterns": len(self.fact_patterns),
            "preference_patterns": len(self.preference_patterns),
            "total_patterns": len(self.personal_info_patterns) + len(self.fact_patterns) + len(self.preference_patterns)
        }


# Global context extractor instance
context_extractor = ContextExtractor()