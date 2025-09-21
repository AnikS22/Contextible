"""Version control service for context entries."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..database import get_db_context
from ..models.context import ContextEntry
from ..models.context_versions import ContextVersion, ChangeType

logger = logging.getLogger(__name__)


class ContextVersionControl:
    """Service for managing context entry versions."""
    
    def __init__(self):
        """Initialize the version control service."""
        self.logger = logging.getLogger(__name__)
    
    async def create_version(self, 
                           context_entry: ContextEntry,
                           change_type: ChangeType,
                           changed_by: str,
                           change_reason: Optional[str] = None,
                           changes_made: Optional[Dict[str, Any]] = None) -> ContextVersion:
        """
        Create a new version for a context entry.
        
        Args:
            context_entry: Context entry to version
            change_type: Type of change
            changed_by: User who made the change
            change_reason: Reason for the change
            changes_made: Detailed changes made
            
        Returns:
            Created version
        """
        with get_db_context() as db:
            # Get next version number
            next_version = await self._get_next_version_number(context_entry.id)
            
            # Create version
            version = ContextVersion.create_version(
                context_id=context_entry.id,
                version_number=next_version,
                change_type=change_type,
                changed_by=changed_by,
                content=context_entry.content,
                context_type=context_entry.context_type.value if hasattr(context_entry.context_type, 'value') else str(context_entry.context_type),
                context_category=context_entry.context_category.value if hasattr(context_entry.context_category, 'value') else str(context_entry.context_category),
                tags=context_entry.tags,
                version_metadata=context_entry.entry_metadata,
                change_reason=change_reason,
                changes_made=changes_made
            )
            
            db.add(version)
            db.commit()
            db.refresh(version)
            
            self.logger.info(f"Created version {next_version} for context {context_entry.id}")
            return version
    
    async def get_version_history(self, context_id: str) -> List[ContextVersion]:
        """
        Get version history for a context entry.
        
        Args:
            context_id: ID of the context entry
            
        Returns:
            List of versions ordered by version number
        """
        with get_db_context() as db:
            versions = db.query(ContextVersion).filter(
                ContextVersion.context_id == context_id
            ).order_by(ContextVersion.version_number).all()
            
            return versions
    
    async def get_version(self, context_id: str, version_number: int) -> Optional[ContextVersion]:
        """
        Get a specific version of a context entry.
        
        Args:
            context_id: ID of the context entry
            version_number: Version number
            
        Returns:
            Version if found, None otherwise
        """
        with get_db_context() as db:
            version = db.query(ContextVersion).filter(
                and_(
                    ContextVersion.context_id == context_id,
                    ContextVersion.version_number == version_number
                )
            ).first()
            
            return version
    
    async def rollback_to_version(self, 
                                context_id: str, 
                                version_number: int,
                                rolled_back_by: str,
                                rollback_reason: Optional[str] = None) -> bool:
        """
        Rollback a context entry to a specific version.
        
        Args:
            context_id: ID of the context entry
            version_number: Version number to rollback to
            rolled_back_by: User performing the rollback
            rollback_reason: Reason for rollback
            
        Returns:
            True if successful, False otherwise
        """
        with get_db_context() as db:
            # Get the target version
            target_version = await self.get_version(context_id, version_number)
            if not target_version:
                self.logger.error(f"Version {version_number} not found for context {context_id}")
                return False
            
            # Get the current context entry
            context_entry = db.query(ContextEntry).filter(
                ContextEntry.id == context_id
            ).first()
            
            if not context_entry:
                self.logger.error(f"Context entry {context_id} not found")
                return False
            
            # Create a version of the current state before rollback
            await self.create_version(
                context_entry=context_entry,
                change_type=ChangeType.UPDATE,
                changed_by=rolled_back_by,
                change_reason="Pre-rollback state"
            )
            
            # Rollback to target version
            context_entry.content = target_version.content
            context_entry.context_type = target_version.context_type
            context_entry.context_category = target_version.context_category
            context_entry.tags = target_version.tags
            context_entry.entry_metadata = target_version.version_metadata
            context_entry.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Create version for the rollback
            await self.create_version(
                context_entry=context_entry,
                change_type=ChangeType.RESTORE,
                changed_by=rolled_back_by,
                change_reason=rollback_reason or f"Rollback to version {version_number}"
            )
            
            self.logger.info(f"Rolled back context {context_id} to version {version_number}")
            return True
    
    async def compare_versions(self, 
                            context_id: str, 
                            version1: int, 
                            version2: int) -> Dict[str, Any]:
        """
        Compare two versions of a context entry.
        
        Args:
            context_id: ID of the context entry
            version1: First version number
            version2: Second version number
            
        Returns:
            Comparison results
        """
        with get_db_context() as db:
            # Get both versions
            v1 = await self.get_version(context_id, version1)
            v2 = await self.get_version(context_id, version2)
            
            if not v1 or not v2:
                return {"error": "One or both versions not found"}
            
            # Compare content
            content_changed = v1.content != v2.content
            content_diff = self._calculate_content_diff(v1.content, v2.content)
            
            # Compare metadata
            metadata_changed = v1.version_metadata != v2.version_metadata
            metadata_diff = self._calculate_metadata_diff(v1.version_metadata, v2.version_metadata)
            
            # Compare tags
            tags_changed = v1.tags != v2.tags
            tags_diff = self._calculate_tags_diff(v1.tags, v2.tags)
            
            return {
                "version1": v1.to_dict(),
                "version2": v2.to_dict(),
                "changes": {
                    "content_changed": content_changed,
                    "content_diff": content_diff,
                    "metadata_changed": metadata_changed,
                    "metadata_diff": metadata_diff,
                    "tags_changed": tags_changed,
                    "tags_diff": tags_diff
                },
                "summary": {
                    "total_changes": sum([
                        content_changed,
                        metadata_changed,
                        tags_changed
                    ]),
                    "time_diff_hours": (v2.created_at - v1.created_at).total_seconds() / 3600
                }
            }
    
    async def get_latest_version(self, context_id: str) -> Optional[ContextVersion]:
        """Get the latest version of a context entry."""
        with get_db_context() as db:
            version = db.query(ContextVersion).filter(
                ContextVersion.context_id == context_id
            ).order_by(desc(ContextVersion.version_number)).first()
            
            return version
    
    async def get_version_statistics(self, context_id: str) -> Dict[str, Any]:
        """Get version statistics for a context entry."""
        with get_db_context() as db:
            # Get all versions
            versions = await self.get_version_history(context_id)
            
            if not versions:
                return {"error": "No versions found"}
            
            # Calculate statistics
            total_versions = len(versions)
            change_types = {}
            contributors = set()
            
            for version in versions:
                change_type = version.change_type.value if hasattr(version.change_type, 'value') else str(version.change_type)
                change_types[change_type] = change_types.get(change_type, 0) + 1
                contributors.add(version.changed_by)
            
            # Calculate time span
            first_version = min(versions, key=lambda v: v.created_at)
            last_version = max(versions, key=lambda v: v.created_at)
            time_span_days = (last_version.created_at - first_version.created_at).days
            
            return {
                "context_id": context_id,
                "total_versions": total_versions,
                "change_types": change_types,
                "contributors": list(contributors),
                "time_span_days": time_span_days,
                "first_version": first_version.created_at.isoformat(),
                "last_version": last_version.created_at.isoformat()
            }
    
    async def cleanup_old_versions(self, 
                                 context_id: str, 
                                 keep_versions: int = 10) -> int:
        """
        Clean up old versions, keeping only the specified number.
        
        Args:
            context_id: ID of the context entry
            keep_versions: Number of versions to keep
            
        Returns:
            Number of versions deleted
        """
        with get_db_context() as db:
            # Get all versions ordered by version number
            versions = db.query(ContextVersion).filter(
                ContextVersion.context_id == context_id
            ).order_by(desc(ContextVersion.version_number)).all()
            
            if len(versions) <= keep_versions:
                return 0
            
            # Delete old versions
            versions_to_delete = versions[keep_versions:]
            deleted_count = 0
            
            for version in versions_to_delete:
                db.delete(version)
                deleted_count += 1
            
            db.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old versions for context {context_id}")
            return deleted_count
    
    async def _get_next_version_number(self, context_id: str) -> int:
        """Get the next version number for a context entry."""
        with get_db_context() as db:
            max_version = db.query(func.max(ContextVersion.version_number)).filter(
                ContextVersion.context_id == context_id
            ).scalar()
            
            return (max_version or 0) + 1
    
    def _calculate_content_diff(self, content1: str, content2: str) -> Dict[str, Any]:
        """Calculate content differences."""
        # Simple diff calculation
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        added_lines = [line for line in lines2 if line not in lines1]
        removed_lines = [line for line in lines1 if line not in lines2]
        
        return {
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "length_change": len(content2) - len(content1)
        }
    
    def _calculate_metadata_diff(self, metadata1: Dict[str, Any], metadata2: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metadata differences."""
        all_keys = set(metadata1.keys()) | set(metadata2.keys())
        
        changes = {}
        for key in all_keys:
            val1 = metadata1.get(key)
            val2 = metadata2.get(key)
            
            if val1 != val2:
                changes[key] = {
                    "old_value": val1,
                    "new_value": val2
                }
        
        return changes
    
    def _calculate_tags_diff(self, tags1: List[str], tags2: List[str]) -> Dict[str, Any]:
        """Calculate tag differences."""
        set1 = set(tags1 or [])
        set2 = set(tags2 or [])
        
        return {
            "added_tags": list(set2 - set1),
            "removed_tags": list(set1 - set2),
            "common_tags": list(set1 & set2)
        }


# Global version control service instance
version_control_service = ContextVersionControl()
