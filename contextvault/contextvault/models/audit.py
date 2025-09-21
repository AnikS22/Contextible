"""SQLAlchemy models for audit trails and compliance."""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, String, Text, func, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AuditEventType(str, Enum):
    """Enumeration of audit event types."""
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Context events
    CONTEXT_ACCESS = "context_access"
    CONTEXT_CREATE = "context_create"
    CONTEXT_UPDATE = "context_update"
    CONTEXT_DELETE = "context_delete"
    CONTEXT_EXPORT = "context_export"
    CONTEXT_IMPORT = "context_import"
    
    # Model events
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    MODEL_ROUTING = "model_routing"
    MODEL_PERFORMANCE = "model_performance"
    
    # Session events
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_ERROR = "session_error"
    
    # Permission events
    PERMISSION_CHECK = "permission_check"
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_DENY = "permission_deny"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
    CONFIG_CHANGE = "config_change"
    
    # Compliance events
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    PRIVACY_REQUEST = "privacy_request"
    CONSENT_CHANGE = "consent_change"


class AuditLog(Base):
    """
    Model for storing audit logs.
    
    Comprehensive audit trail for all system activities,
    required for enterprise compliance and security.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the audit log entry"
    )
    
    # Event information
    event_type: Mapped[AuditEventType] = mapped_column(
        nullable=False,
        comment="Type of audit event"
    )
    
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the event occurred"
    )
    
    # User and session information
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="User ID who performed the action"
    )
    
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="Session ID where the event occurred"
    )
    
    # Request information
    request_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="Request ID for tracking"
    )
    
    # Event details
    event_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Detailed event data"
    )
    
    # Security information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), 
        nullable=True,
        comment="IP address of the request"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        comment="User agent string"
    )
    
    # Result information
    success: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Whether the event was successful"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Error message if the event failed"
    )
    
    # Compliance information
    data_subject_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="Data subject ID for GDPR compliance"
    )
    
    legal_basis: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True,
        comment="Legal basis for data processing"
    )
    
    consent_given: Mapped[Optional[bool]] = mapped_column(
        Boolean, 
        nullable=True,
        comment="Whether consent was given"
    )
    
    # Risk assessment
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True,
        comment="Risk level of the event"
    )
    
    risk_score: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Risk score (0.0-1.0)"
    )
    
    # Additional metadata
    audit_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Additional audit metadata"
    )
    
    def __repr__(self) -> str:
        """String representation of the audit log."""
        return (
            f"<AuditLog(id='{self.id}', "
            f"event_type='{self.event_type}', "
            f"user_id='{self.user_id}', "
            f"success={self.success})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit log to a dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            "event_timestamp": self.event_timestamp.isoformat() if self.event_timestamp else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "event_data": self.event_data or {},
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "data_subject_id": self.data_subject_id,
            "legal_basis": self.legal_basis,
            "consent_given": self.consent_given,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "audit_metadata": self.audit_metadata or {}
        }
    
    @classmethod
    def create_audit_log(cls,
                        event_type: AuditEventType,
                        user_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        request_id: Optional[str] = None,
                        event_data: Optional[Dict[str, Any]] = None,
                        ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        data_subject_id: Optional[str] = None,
                        legal_basis: Optional[str] = None,
                        consent_given: Optional[bool] = None,
                        risk_level: Optional[str] = None,
                        risk_score: Optional[float] = None,
                        audit_metadata: Optional[Dict[str, Any]] = None) -> "AuditLog":
        """
        Create a new audit log entry.
        
        Args:
            event_type: Type of audit event
            user_id: User ID
            session_id: Session ID
            request_id: Request ID
            event_data: Event data
            ip_address: IP address
            user_agent: User agent
            success: Whether successful
            error_message: Error message
            data_subject_id: Data subject ID
            legal_basis: Legal basis
            consent_given: Consent given
            risk_level: Risk level
            risk_score: Risk score
            audit_metadata: Additional metadata
            
        Returns:
            New AuditLog instance
        """
        return cls(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            event_data=event_data or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            data_subject_id=data_subject_id,
            legal_basis=legal_basis,
            consent_given=consent_given,
            risk_level=risk_level,
            risk_score=risk_score,
            audit_metadata=audit_metadata or {}
        )


class ComplianceReport(Base):
    """
    Model for storing compliance reports.
    
    Automated generation of regulatory compliance reports
    for GDPR, CCPA, SOX, HIPAA, and other regulations.
    """
    
    __tablename__ = "compliance_reports"
    
    # Primary identifier
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier for the compliance report"
    )
    
    # Report information
    report_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Type of compliance report (gdpr, ccpa, sox, hipaa)"
    )
    
    report_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Human-readable report name"
    )
    
    # Time period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        comment="Start of the reporting period"
    )
    
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        comment="End of the reporting period"
    )
    
    # Report data
    report_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="Report data and findings"
    )
    
    # Compliance metrics
    compliance_score: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Overall compliance score (0.0-1.0)"
    )
    
    violations_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="Number of compliance violations found"
    )
    
    recommendations_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="Number of recommendations generated"
    )
    
    # Generation information
    generated_by: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="User ID who generated the report"
    )
    
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When the report was generated"
    )
    
    # Status
    is_approved: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Whether the report has been approved"
    )
    
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="User ID who approved the report"
    )
    
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When the report was approved"
    )
    
    def __repr__(self) -> str:
        """String representation of the compliance report."""
        return (
            f"<ComplianceReport(id='{self.id}', "
            f"report_type='{self.report_type}', "
            f"period='{self.period_start}' to '{self.period_end}')>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the compliance report to a dictionary."""
        return {
            "id": self.id,
            "report_type": self.report_type,
            "report_name": self.report_name,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "report_data": self.report_data or {},
            "compliance_score": self.compliance_score,
            "violations_count": self.violations_count,
            "recommendations_count": self.recommendations_count,
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "is_approved": self.is_approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None
        }
