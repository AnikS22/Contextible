"""Import/Export service for context data."""

import json
import csv
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from sqlalchemy.orm import Session

from ..database import get_db_context
from ..models.context import ContextEntry, ContextType, ContextSource, ContextCategory
from ..models.sessions import Session as SessionModel
from ..models.models import AIModel

logger = logging.getLogger(__name__)


class ContextImportExport:
    """Service for importing and exporting context data."""
    
    def __init__(self):
        """Initialize the import/export service."""
        self.logger = logging.getLogger(__name__)
    
    async def export_context(self, 
                           format: str = "json",
                           user_id: Optional[str] = None,
                           include_sessions: bool = False,
                           include_models: bool = False) -> Union[str, bytes]:
        """
        Export context data in the specified format.
        
        Args:
            format: Export format ("json", "csv", "backup")
            user_id: Optional user ID to filter by
            include_sessions: Whether to include session data
            include_models: Whether to include model data
            
        Returns:
            Exported data as string or bytes
        """
        with get_db_context() as db:
            # Get context entries
            query = db.query(ContextEntry)
            if user_id:
                query = query.filter(ContextEntry.user_id == user_id)
            
            context_entries = query.all()
            
            # Prepare export data
            export_data = {
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "format": format,
                    "total_context_entries": len(context_entries),
                    "user_id": user_id
                },
                "context_entries": [self._serialize_context_entry(entry) for entry in context_entries]
            }
            
            # Add sessions if requested
            if include_sessions:
                sessions_query = db.query(SessionModel)
                if user_id:
                    sessions_query = sessions_query.filter(SessionModel.user_id == user_id)
                
                sessions = sessions_query.all()
                export_data["sessions"] = [self._serialize_session(session) for session in sessions]
                export_data["export_info"]["total_sessions"] = len(sessions)
            
            # Add models if requested
            if include_models:
                models = db.query(AIModel).all()
                export_data["models"] = [self._serialize_model(model) for model in models]
                export_data["export_info"]["total_models"] = len(models)
            
            # Format the data
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format == "csv":
                return self._export_to_csv(export_data)
            elif format == "backup":
                return self._create_backup(export_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    async def import_context(self, 
                           data: Union[str, bytes],
                           format: str = "json",
                           merge_strategy: str = "skip_existing") -> Dict[str, Any]:
        """
        Import context data from the specified format.
        
        Args:
            data: Import data
            format: Import format ("json", "csv", "backup")
            merge_strategy: How to handle existing data ("skip_existing", "overwrite", "merge")
            
        Returns:
            Import results
        """
        # Parse the data
        if format == "json":
            import_data = json.loads(data)
        elif format == "csv":
            import_data = self._parse_csv(data)
        elif format == "backup":
            import_data = self._parse_backup(data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        results = {
            "imported_at": datetime.utcnow().isoformat(),
            "format": format,
            "merge_strategy": merge_strategy,
            "context_entries_imported": 0,
            "context_entries_skipped": 0,
            "context_entries_updated": 0,
            "sessions_imported": 0,
            "models_imported": 0,
            "errors": []
        }
        
        with get_db_context() as db:
            # Import context entries
            if "context_entries" in import_data:
                context_results = await self._import_context_entries(
                    db, import_data["context_entries"], merge_strategy
                )
                results.update(context_results)
            
            # Import sessions
            if "sessions" in import_data:
                session_results = await self._import_sessions(
                    db, import_data["sessions"], merge_strategy
                )
                results.update(session_results)
            
            # Import models
            if "models" in import_data:
                model_results = await self._import_models(
                    db, import_data["models"], merge_strategy
                )
                results.update(model_results)
            
            db.commit()
        
        return results
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all data for a specific user.
        
        Args:
            user_id: User ID to export data for
            
        Returns:
            Complete user data export
        """
        with get_db_context() as db:
            # Get all user data
            context_entries = db.query(ContextEntry).filter(
                ContextEntry.user_id == user_id
            ).all()
            
            sessions = db.query(SessionModel).filter(
                SessionModel.user_id == user_id
            ).all()
            
            user_data = {
                "user_id": user_id,
                "exported_at": datetime.utcnow().isoformat(),
                "context_entries": [self._serialize_context_entry(entry) for entry in context_entries],
                "sessions": [self._serialize_session(session) for session in sessions],
                "statistics": {
                    "total_context_entries": len(context_entries),
                    "total_sessions": len(sessions),
                    "context_by_type": self._analyze_context_by_type(context_entries),
                    "session_statistics": self._analyze_sessions(sessions)
                }
            }
            
            return user_data
    
    async def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Create a complete database backup.
        
        Args:
            backup_path: Optional path for backup file
            
        Returns:
            Path to backup file
        """
        if not backup_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = f"contextvault_backup_{timestamp}.json"
        
        # Export all data
        export_data = await self.export_context(
            format="json",
            include_sessions=True,
            include_models=True
        )
        
        # Write to file
        with open(backup_path, 'w') as f:
            f.write(export_data)
        
        self.logger.info(f"Database backup created: {backup_path}")
        return backup_path
    
    async def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(backup_path, 'r') as f:
                backup_data = f.read()
            
            # Import the backup
            results = await self.import_context(
                data=backup_data,
                format="json",
                merge_strategy="overwrite"
            )
            
            self.logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore database: {e}")
            return False
    
    def _serialize_context_entry(self, entry: ContextEntry) -> Dict[str, Any]:
        """Serialize a context entry for export."""
        return {
            "id": entry.id,
            "content": entry.content,
            "context_type": entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type),
            "source": entry.source,
            "context_source": entry.context_source.value if hasattr(entry.context_source, 'value') else str(entry.context_source),
            "confidence_score": entry.confidence_score,
            "context_category": entry.context_category.value if hasattr(entry.context_category, 'value') else str(entry.context_category),
            "parent_context_id": entry.parent_context_id,
            "validation_status": entry.validation_status.value if hasattr(entry.validation_status, 'value') else str(entry.validation_status),
            "extraction_metadata": entry.extraction_metadata or {},
            "tags": entry.tags or [],
            "entry_metadata": entry.entry_metadata or {},
            "user_id": entry.user_id,
            "session_id": entry.session_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            "access_count": entry.access_count,
            "last_accessed_at": entry.last_accessed_at.isoformat() if entry.last_accessed_at else None,
            "relevance_score": entry.relevance_score
        }
    
    def _serialize_session(self, session: SessionModel) -> Dict[str, Any]:
        """Serialize a session for export."""
        return {
            "id": session.id,
            "model_id": session.model_id,
            "model_name": session.model_name,
            "user_id": session.user_id,
            "session_type": session.session_type,
            "source": session.source,
            "context_used": session.context_used or [],
            "context_count": session.context_count,
            "total_context_length": session.total_context_length,
            "original_prompt": session.original_prompt,
            "final_prompt": session.final_prompt,
            "response_summary": session.response_summary,
            "processing_time_ms": session.processing_time_ms,
            "model_response_time_ms": session.model_response_time_ms,
            "success": session.success,
            "error_message": session.error_message,
            "session_metadata": session.session_metadata or {},
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
    
    def _serialize_model(self, model: AIModel) -> Dict[str, Any]:
        """Serialize a model for export."""
        return {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "provider": model.provider.value if hasattr(model.provider, 'value') else str(model.provider),
            "model_id": model.model_id,
            "capabilities": model.capabilities or {},
            "max_context_length": model.max_context_length,
            "max_tokens": model.max_tokens,
            "status": model.status.value if hasattr(model.status, 'value') else str(model.status),
            "is_active": model.is_active,
            "endpoint": model.endpoint,
            "configuration": model.configuration or {},
            "performance_metrics": model.performance_metrics or {},
            "average_response_time_ms": model.average_response_time_ms,
            "success_rate": model.success_rate,
            "total_requests": model.total_requests,
            "total_tokens_generated": model.total_tokens_generated,
            "description": model.description,
            "tags": model.tags or [],
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "last_used_at": model.last_used_at.isoformat() if model.last_used_at else None
        }
    
    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """Export data to CSV format."""
        output = []
        
        # Export context entries
        if "context_entries" in data:
            output.append("=== CONTEXT ENTRIES ===")
            for entry in data["context_entries"]:
                output.append(f"ID: {entry['id']}")
                output.append(f"Content: {entry['content']}")
                output.append(f"Type: {entry['context_type']}")
                output.append(f"Category: {entry['context_category']}")
                output.append(f"Tags: {', '.join(entry['tags'])}")
                output.append("---")
        
        return "\n".join(output)
    
    def _create_backup(self, data: Dict[str, Any]) -> bytes:
        """Create a binary backup file."""
        json_data = json.dumps(data, indent=2, default=str)
        return json_data.encode('utf-8')
    
    def _parse_csv(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Parse CSV data."""
        # This is a simplified CSV parser
        # In a real implementation, you'd use proper CSV parsing
        return {"context_entries": [], "sessions": [], "models": []}
    
    def _parse_backup(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Parse backup data."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    
    async def _import_context_entries(self, 
                                    db: Session,
                                    entries_data: List[Dict[str, Any]],
                                    merge_strategy: str) -> Dict[str, int]:
        """Import context entries."""
        imported = 0
        skipped = 0
        updated = 0
        
        for entry_data in entries_data:
            try:
                # Check if entry already exists
                existing = db.query(ContextEntry).filter(
                    ContextEntry.id == entry_data["id"]
                ).first()
                
                if existing:
                    if merge_strategy == "skip_existing":
                        skipped += 1
                        continue
                    elif merge_strategy == "overwrite":
                        # Update existing entry
                        for key, value in entry_data.items():
                            if hasattr(existing, key) and key != "id":
                                setattr(existing, key, value)
                        updated += 1
                        continue
                
                # Create new entry
                new_entry = ContextEntry(**entry_data)
                db.add(new_entry)
                imported += 1
                
            except Exception as e:
                self.logger.error(f"Failed to import context entry: {e}")
                continue
        
        return {
            "context_entries_imported": imported,
            "context_entries_skipped": skipped,
            "context_entries_updated": updated
        }
    
    async def _import_sessions(self, 
                             db: Session,
                             sessions_data: List[Dict[str, Any]],
                             merge_strategy: str) -> Dict[str, int]:
        """Import sessions."""
        imported = 0
        
        for session_data in sessions_data:
            try:
                # Check if session already exists
                existing = db.query(SessionModel).filter(
                    SessionModel.id == session_data["id"]
                ).first()
                
                if existing and merge_strategy == "skip_existing":
                    continue
                
                # Create new session
                new_session = SessionModel(**session_data)
                db.add(new_session)
                imported += 1
                
            except Exception as e:
                self.logger.error(f"Failed to import session: {e}")
                continue
        
        return {"sessions_imported": imported}
    
    async def _import_models(self, 
                          db: Session,
                          models_data: List[Dict[str, Any]],
                          merge_strategy: str) -> Dict[str, int]:
        """Import models."""
        imported = 0
        
        for model_data in models_data:
            try:
                # Check if model already exists
                existing = db.query(AIModel).filter(
                    AIModel.id == model_data["id"]
                ).first()
                
                if existing and merge_strategy == "skip_existing":
                    continue
                
                # Create new model
                new_model = AIModel(**model_data)
                db.add(new_model)
                imported += 1
                
            except Exception as e:
                self.logger.error(f"Failed to import model: {e}")
                continue
        
        return {"models_imported": imported}
    
    def _analyze_context_by_type(self, entries: List[ContextEntry]) -> Dict[str, int]:
        """Analyze context entries by type."""
        type_counts = {}
        for entry in entries:
            type_name = entry.context_type.value if hasattr(entry.context_type, 'value') else str(entry.context_type)
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        return type_counts
    
    def _analyze_sessions(self, sessions: List[SessionModel]) -> Dict[str, Any]:
        """Analyze session statistics."""
        if not sessions:
            return {}
        
        return {
            "total_sessions": len(sessions),
            "successful_sessions": len([s for s in sessions if s.success]),
            "average_context_per_session": sum(s.context_count for s in sessions) / len(sessions),
            "models_used": list(set(s.model_id for s in sessions))
        }


# Global import/export service instance
import_export_service = ContextImportExport()
