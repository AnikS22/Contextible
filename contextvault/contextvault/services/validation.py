"""
Context Validation System
Validates extracted context for accuracy and relevance
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .context_extractor import ExtractedContext, ExtractionConfidence


class ValidationStatus(Enum):
    """Validation status for extracted context."""
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"
    UNCERTAIN = "uncertain"


@dataclass
class ValidationResult:
    """Result of context validation."""
    status: ValidationStatus
    confidence: float  # 0.0 to 1.0
    issues: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]


class ContextValidator:
    """Validates extracted context for accuracy and relevance."""
    
    def __init__(self):
        # Define validation rules
        self.min_length = 3
        self.max_length = 500
        self.blacklisted_patterns = [
            r"^\s*$",  # Empty or whitespace only
            r"^[^a-zA-Z]*$",  # No letters
            r"^\d+$",  # Only numbers
            r"^[^\w\s]*$",  # Only punctuation
        ]
        
        # Quality indicators
        self.quality_indicators = {
            "specific": r"\b(?:specifically|exactly|precisely|definitely)\b",
            "certain": r"\b(?:always|never|certainly|absolutely)\b",
            "personal": r"\b(?:i|my|me|myself)\b",
            "factual": r"\b(?:i am|i have|i work|i live|my name is)\b",
        }
        
        # Red flags for potentially invalid content
        self.red_flags = [
            r"\b(?:maybe|perhaps|might|could|possibly)\b",  # Uncertainty
            r"\b(?:i think|i believe|in my opinion)\b",     # Opinion vs fact
            r"\b(?:sometimes|often|usually|rarely)\b",      # Vague frequency
        ]
    
    def validate_context_batch(self, contexts: List[ExtractedContext]) -> List[ValidationResult]:
        """Validate a batch of extracted contexts."""
        results = []
        
        for context in contexts:
            result = self.validate_single_context(context)
            results.append(result)
        
        return results
    
    def validate_single_context(self, context: ExtractedContext) -> ValidationResult:
        """Validate a single extracted context."""
        issues = []
        suggestions = []
        confidence_score = 0.0
        metadata = {}
        
        # Basic validation
        basic_validation = self._validate_basic_quality(context)
        issues.extend(basic_validation["issues"])
        suggestions.extend(basic_validation["suggestions"])
        confidence_score += basic_validation["confidence"]
        
        # Content validation
        content_validation = self._validate_content_quality(context)
        issues.extend(content_validation["issues"])
        suggestions.extend(content_validation["suggestions"])
        confidence_score += content_validation["confidence"]
        
        # Context type validation
        type_validation = self._validate_context_type(context)
        issues.extend(type_validation["issues"])
        suggestions.extend(type_validation["suggestions"])
        confidence_score += type_validation["confidence"]
        
        # Confidence validation
        confidence_validation = self._validate_extraction_confidence(context)
        issues.extend(confidence_validation["issues"])
        suggestions.extend(confidence_validation["suggestions"])
        confidence_score += confidence_validation["confidence"]
        
        # Normalize confidence score
        final_confidence = min(1.0, confidence_score / 4.0)  # Divide by number of validation categories
        
        # Determine final status
        status = self._determine_validation_status(final_confidence, issues)
        
        metadata.update({
            "validation_timestamp": self._get_timestamp(),
            "extraction_confidence": context.confidence.value,
            "content_length": len(context.content),
            "tag_count": len(context.tags)
        })
        
        return ValidationResult(
            status=status,
            confidence=final_confidence,
            issues=issues,
            suggestions=suggestions,
            metadata=metadata
        )
    
    def _validate_basic_quality(self, context: ExtractedContext) -> Dict[str, Any]:
        """Validate basic quality of the context."""
        issues = []
        suggestions = []
        confidence = 0.0
        
        content = context.content.strip()
        
        # Check length
        if len(content) < self.min_length:
            issues.append(f"Content too short ({len(content)} chars, minimum {self.min_length})")
            confidence -= 0.3
        elif len(content) > self.max_length:
            issues.append(f"Content too long ({len(content)} chars, maximum {self.max_length})")
            confidence -= 0.1
        else:
            confidence += 0.2
        
        # Check for blacklisted patterns
        for pattern in self.blacklisted_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                issues.append(f"Content matches blacklisted pattern: {pattern}")
                confidence -= 0.5
        
        # Check for minimum word count
        word_count = len(content.split())
        if word_count < 2:
            issues.append("Content has too few words")
            confidence -= 0.2
        else:
            confidence += 0.1
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "confidence": confidence
        }
    
    def _validate_content_quality(self, context: ExtractedContext) -> Dict[str, Any]:
        """Validate the quality of the content."""
        issues = []
        suggestions = []
        confidence = 0.0
        
        content = context.content.lower()
        
        # Check for quality indicators
        quality_score = 0
        for indicator_name, pattern in self.quality_indicators.items():
            if re.search(pattern, content):
                quality_score += 1
                confidence += 0.1
        
        if quality_score == 0:
            suggestions.append("Content could be more specific or personal")
        
        # Check for red flags
        red_flag_count = 0
        for pattern in self.red_flags:
            if re.search(pattern, content):
                red_flag_count += 1
                confidence -= 0.1
        
        if red_flag_count > 0:
            issues.append(f"Content contains {red_flag_count} uncertainty indicators")
            suggestions.append("Consider if this is factual information or opinion")
        
        # Check for proper capitalization (basic check)
        original_content = context.content
        if original_content != original_content.capitalize() and not any(c.isupper() for c in original_content):
            suggestions.append("Consider proper capitalization")
        
        # Check for context completeness
        if not self._is_context_complete(context.content):
            suggestions.append("Content might be incomplete")
            confidence -= 0.1
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "confidence": confidence
        }
    
    def _validate_context_type(self, context: ExtractedContext) -> Dict[str, Any]:
        """Validate if the context type matches the content."""
        issues = []
        suggestions = []
        confidence = 0.0
        
        content = context.content.lower()
        context_type = context.context_type.value if hasattr(context.context_type, 'value') else str(context.context_type)
        
        # Check if context type matches content
        type_indicators = {
            "preference": ["prefer", "like", "love", "favorite", "best", "worst", "hate"],
            "note": ["i am", "i have", "i work", "i live", "my name is", "fact"],
            "text": ["information", "details", "about"],
            "event": ["happened", "occurred", "event", "meeting", "appointment"],
            "file": ["document", "file", "attachment", "report"]
        }
        
        expected_indicators = type_indicators.get(context_type, [])
        if expected_indicators:
            has_indicators = any(indicator in content for indicator in expected_indicators)
            if has_indicators:
                confidence += 0.2
            else:
                suggestions.append(f"Content doesn't seem to match context type '{context_type}'")
                confidence -= 0.1
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "confidence": confidence
        }
    
    def _validate_extraction_confidence(self, context: ExtractedContext) -> Dict[str, Any]:
        """Validate the extraction confidence."""
        issues = []
        suggestions = []
        confidence = 0.0
        
        extraction_confidence = context.confidence
        
        # Map extraction confidence to validation confidence
        if extraction_confidence == ExtractionConfidence.HIGH:
            confidence += 0.3
        elif extraction_confidence == ExtractionConfidence.MEDIUM:
            confidence += 0.1
        else:  # LOW
            issues.append("Low extraction confidence")
            suggestions.append("Review extraction accuracy")
            confidence -= 0.1
        
        # Check if confidence matches content quality
        content_quality = self._assess_content_quality(context.content)
        if extraction_confidence == ExtractionConfidence.HIGH and content_quality < 0.5:
            issues.append("High extraction confidence but low content quality")
            suggestions.append("Verify extraction accuracy")
            confidence -= 0.2
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "confidence": confidence
        }
    
    def _is_context_complete(self, content: str) -> bool:
        """Check if the context appears complete."""
        # Simple heuristics for completeness
        content = content.strip()
        
        # Should end with proper punctuation
        if not content.endswith(('.', '!', '?')):
            return False
        
        # Should have at least a subject and predicate (basic check)
        words = content.split()
        if len(words) < 3:
            return False
        
        # Check for incomplete sentences
        incomplete_indicators = ["...", "etc", "and so on", "etc."]
        if any(indicator in content.lower() for indicator in incomplete_indicators):
            return False
        
        return True
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess the quality of content (0.0 to 1.0)."""
        score = 0.0
        
        # Length score
        if 10 <= len(content) <= 200:
            score += 0.3
        elif len(content) < 10:
            score += 0.1
        else:
            score += 0.2
        
        # Word count score
        word_count = len(content.split())
        if 3 <= word_count <= 50:
            score += 0.3
        else:
            score += 0.1
        
        # Quality indicators
        quality_indicators = 0
        for pattern in self.quality_indicators.values():
            if re.search(pattern, content.lower()):
                quality_indicators += 1
        
        score += min(0.4, quality_indicators * 0.1)
        
        return min(1.0, score)
    
    def _determine_validation_status(self, confidence: float, issues: List[str]) -> ValidationStatus:
        """Determine the final validation status."""
        # Be more lenient for auto-extracted content
        if confidence >= 0.5 and len(issues) == 0:
            return ValidationStatus.VALID
        elif confidence >= 0.3 and len(issues) <= 3:
            return ValidationStatus.NEEDS_REVIEW
        elif confidence >= 0.1:
            return ValidationStatus.UNCERTAIN
        else:
            return ValidationStatus.INVALID
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "quality_indicators": len(self.quality_indicators),
            "red_flags": len(self.red_flags),
            "blacklisted_patterns": len(self.blacklisted_patterns)
        }


# Global context validator instance
context_validator = ContextValidator()