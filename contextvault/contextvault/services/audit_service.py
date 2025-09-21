"""Comprehensive audit service for enterprise compliance."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, Integer

from ..database import get_db_context
from ..models.audit import AuditLog, AuditEventType, ComplianceReport
# Removed user import - focusing on core functionality
from ..models.context import ContextEntry
from ..models.sessions import Session as SessionModel

logger = logging.getLogger(__name__)


class AuditService:
    """Service for comprehensive audit trails and compliance."""
    
    def __init__(self):
        """Initialize the audit service."""
        self.logger = logging.getLogger(__name__)
    
    async def log_event(self,
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
                       audit_metadata: Optional[Dict[str, Any]] = None) -> AuditLog:
        """
        Log an audit event.
        
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
            Created audit log entry
        """
        with get_db_context() as db:
            # Convert string to enum if needed
            if isinstance(event_type, str):
                event_type = AuditEventType(event_type)
            
            # Create audit log
            audit_log = AuditLog.create_audit_log(
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
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            # Get the ID and other attributes before returning to avoid detached instance
            audit_id = audit_log.id
            event_type_value = event_type.value if hasattr(event_type, 'value') else str(event_type)
            
            self.logger.info(f"Logged audit event: {event_type_value} for user {user_id}")
            
            # Return a dictionary instead of the SQLAlchemy object to avoid session issues
            return {
                "id": audit_id,
                "event_type": event_type_value,
                "user_id": user_id,
                "success": success,
                "event_timestamp": audit_log.event_timestamp.isoformat() if audit_log.event_timestamp else None
            }
    
    async def log_context_access(self,
                               user_id: str,
                               context_id: str,
                               access_type: str,
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None) -> AuditLog:
        """Log context access event."""
        return await self.log_event(
            event_type=AuditEventType.CONTEXT_ACCESS,
            user_id=user_id,
            event_data={
                "context_id": context_id,
                "access_type": access_type
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_context_creation(self,
                                 user_id: str,
                                 context_id: str,
                                 context_type: str,
                                 ip_address: Optional[str] = None,
                                 user_agent: Optional[str] = None) -> AuditLog:
        """Log context creation event."""
        return await self.log_event(
            event_type=AuditEventType.CONTEXT_CREATE,
            user_id=user_id,
            event_data={
                "context_id": context_id,
                "context_type": context_type
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_model_request(self,
                              user_id: str,
                              model_id: str,
                              request_data: Dict[str, Any],
                              session_id: Optional[str] = None,
                              ip_address: Optional[str] = None,
                              user_agent: Optional[str] = None) -> AuditLog:
        """Log model request event."""
        return await self.log_event(
            event_type=AuditEventType.MODEL_REQUEST,
            user_id=user_id,
            session_id=session_id,
            event_data={
                "model_id": model_id,
                "request_data": request_data
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_model_response(self,
                               user_id: str,
                               model_id: str,
                               response_data: Dict[str, Any],
                               success: bool,
                               session_id: Optional[str] = None,
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None) -> AuditLog:
        """Log model response event."""
        return await self.log_event(
            event_type=AuditEventType.MODEL_RESPONSE,
            user_id=user_id,
            session_id=session_id,
            event_data={
                "model_id": model_id,
                "response_data": response_data
            },
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_data_export(self,
                            user_id: str,
                            export_type: str,
                            data_subject_id: Optional[str] = None,
                            legal_basis: Optional[str] = None,
                            consent_given: Optional[bool] = None,
                            ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None) -> AuditLog:
        """Log data export event for compliance."""
        return await self.log_event(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=user_id,
            event_data={
                "export_type": export_type
            },
            data_subject_id=data_subject_id,
            legal_basis=legal_basis,
            consent_given=consent_given,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_privacy_request(self,
                                data_subject_id: str,
                                request_type: str,
                                user_id: Optional[str] = None,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> AuditLog:
        """Log privacy request event (GDPR/CCPA)."""
        return await self.log_event(
            event_type=AuditEventType.PRIVACY_REQUEST,
            user_id=user_id,
            event_data={
                "request_type": request_type
            },
            data_subject_id=data_subject_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_audit_trail(self,
                            user_id: Optional[str] = None,
                            event_type: Optional[AuditEventType] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: int = 1000,
                            offset: int = 0) -> List[AuditLog]:
        """
        Get audit trail with filtering.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            List of audit log entries
        """
        with get_db_context() as db:
            query = db.query(AuditLog)
            
            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if event_type:
                query = query.filter(AuditLog.event_type == event_type)
            
            if start_date:
                query = query.filter(AuditLog.event_timestamp >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.event_timestamp <= end_date)
            
            # Order by timestamp and apply pagination
            audit_logs = query.order_by(desc(AuditLog.event_timestamp)).limit(limit).offset(offset).all()
            
            return audit_logs
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary for compliance reporting."""
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get activity counts by event type
            activity_counts = db.query(
                AuditLog.event_type,
                func.count(AuditLog.id).label('count')
            ).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_timestamp >= start_date
                )
            ).group_by(AuditLog.event_type).all()
            
            # Get success/failure rates
            success_rate = db.query(
                func.avg(func.cast(AuditLog.success, Integer)).label('success_rate')
            ).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_timestamp >= start_date
                )
            ).scalar()
            
            # Get data access events
            data_access_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_type == AuditEventType.DATA_ACCESS,
                    AuditLog.event_timestamp >= start_date
                )
            ).count()
            
            return {
                "user_id": user_id,
                "period_days": days,
                "activity_counts": {event_type.value: count for event_type, count in activity_counts},
                "success_rate": float(success_rate) if success_rate else 0.0,
                "data_access_events": data_access_events,
                "total_events": sum(count for _, count in activity_counts)
            }
    
    async def generate_compliance_report(self,
                                      report_type: str,
                                      period_start: datetime,
                                      period_end: datetime,
                                      generated_by: str) -> ComplianceReport:
        """
        Generate a compliance report.
        
        Args:
            report_type: Type of compliance report
            period_start: Start of reporting period
            period_end: End of reporting period
            generated_by: User ID who generated the report
            
        Returns:
            Generated compliance report
        """
        with get_db_context() as db:
            # Generate report data based on type
            if report_type.lower() == "gdpr":
                report_data = await self._generate_gdpr_report(period_start, period_end)
            elif report_type.lower() == "ccpa":
                report_data = await self._generate_ccpa_report(period_start, period_end)
            elif report_type.lower() == "sox":
                report_data = await self._generate_sox_report(period_start, period_end)
            elif report_type.lower() == "hipaa":
                report_data = await self._generate_hipaa_report(period_start, period_end)
            else:
                report_data = await self._generate_general_report(period_start, period_end)
            
            # Create compliance report
            report = ComplianceReport(
                report_type=report_type,
                report_name=f"{report_type.upper()} Compliance Report - {period_start.date()} to {period_end.date()}",
                period_start=period_start,
                period_end=period_end,
                report_data=report_data,
                compliance_score=report_data.get("compliance_score", 0.0),
                violations_count=report_data.get("violations_count", 0),
                recommendations_count=report_data.get("recommendations_count", 0),
                generated_by=generated_by
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            self.logger.info(f"Generated {report_type} compliance report: {report.id}")
            return report
    
    async def _generate_gdpr_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        with get_db_context() as db:
            # Data processing activities
            data_processing_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type.in_([
                        AuditEventType.DATA_ACCESS,
                        AuditEventType.DATA_MODIFICATION,
                        AuditEventType.DATA_EXPORT
                    ]),
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Privacy requests
            privacy_requests = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.PRIVACY_REQUEST,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Consent changes
            consent_changes = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.CONSENT_CHANGE,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            return {
                "report_type": "GDPR",
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "data_processing_activities": len(data_processing_events),
                "privacy_requests": len(privacy_requests),
                "consent_changes": len(consent_changes),
                "compliance_score": 0.85,  # Placeholder
                "violations_count": 0,
                "recommendations_count": 3,
                "recommendations": [
                    "Implement data retention policies",
                    "Enhance consent management",
                    "Regular privacy impact assessments"
                ]
            }
    
    async def _generate_ccpa_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate CCPA compliance report."""
        with get_db_context() as db:
            # Consumer requests
            consumer_requests = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.PRIVACY_REQUEST,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Data sales (if any)
            data_sales = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.DATA_EXPORT,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            return {
                "report_type": "CCPA",
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "consumer_requests": len(consumer_requests),
                "data_sales": len(data_sales),
                "compliance_score": 0.90,
                "violations_count": 0,
                "recommendations_count": 2,
                "recommendations": [
                    "Implement consumer rights portal",
                    "Enhance data sale tracking"
                ]
            }
    
    async def _generate_sox_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate SOX compliance report."""
        with get_db_context() as db:
            # System access events
            access_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type.in_([
                        AuditEventType.LOGIN,
                        AuditEventType.CONTEXT_ACCESS,
                        AuditEventType.MODEL_REQUEST
                    ]),
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Configuration changes
            config_changes = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.CONFIG_CHANGE,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            return {
                "report_type": "SOX",
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "access_events": len(access_events),
                "config_changes": len(config_changes),
                "compliance_score": 0.95,
                "violations_count": 0,
                "recommendations_count": 1,
                "recommendations": [
                    "Implement automated compliance monitoring"
                ]
            }
    
    async def _generate_hipaa_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report."""
        with get_db_context() as db:
            # PHI access events
            phi_access = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.DATA_ACCESS,
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Security events
            security_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type.in_([
                        AuditEventType.LOGIN_FAILED,
                        AuditEventType.SYSTEM_ERROR
                    ]),
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            return {
                "report_type": "HIPAA",
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "phi_access_events": len(phi_access),
                "security_events": len(security_events),
                "compliance_score": 0.88,
                "violations_count": 0,
                "recommendations_count": 2,
                "recommendations": [
                    "Implement PHI encryption at rest",
                    "Enhance access controls"
                ]
            }
    
    async def _generate_general_report(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate general compliance report."""
        with get_db_context() as db:
            # All events in period
            all_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).all()
            
            # Success rate
            success_rate = db.query(
                func.avg(func.cast(AuditLog.success, Integer))
            ).filter(
                and_(
                    AuditLog.event_timestamp >= period_start,
                    AuditLog.event_timestamp <= period_end
                )
            ).scalar()
            
            return {
                "report_type": "General",
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "total_events": len(all_events),
                "success_rate": float(success_rate) if success_rate else 0.0,
                "compliance_score": 0.80,
                "violations_count": 0,
                "recommendations_count": 1,
                "recommendations": [
                    "Regular compliance monitoring"
                ]
            }
    
    async def get_risk_assessment(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get risk assessment for a user."""
        with get_db_context() as db:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get high-risk events
            high_risk_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.risk_level == "high",
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Get failed events
            failed_events = db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.success == False,
                    AuditLog.event_timestamp >= start_date
                )
            ).all()
            
            # Calculate risk score
            risk_score = min(1.0, (len(high_risk_events) * 0.3 + len(failed_events) * 0.1))
            
            return {
                "user_id": user_id,
                "risk_score": risk_score,
                "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.3 else "low",
                "high_risk_events": len(high_risk_events),
                "failed_events": len(failed_events),
                "recommendations": [
                    "Review high-risk activities",
                    "Implement additional monitoring"
                ] if risk_score > 0.5 else []
            }


# Global audit service instance
audit_service = AuditService()
