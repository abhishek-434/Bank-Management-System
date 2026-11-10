"""Service for audit trail recording and historical inspection."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc
from database.connection import db_manager
from models.audit import AuditLog

logger = logging.getLogger("bms.audit_service")


class AuditService:
    """Records security, administrative, and financial events into immutable audit logs."""

    @staticmethod
    def log(
        action: str,
        target_entity: str,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "127.0.0.1",
        session=None,
    ) -> AuditLog:
        """Create and persist an audit log entry."""
        details_str = json.dumps(details or {}, default=str)
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_entity=target_entity,
            target_id=str(target_id) if target_id else None,
            details=details_str,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
        )

        if session:
            session.add(audit_entry)
        else:
            with db_manager.session_scope() as sess:
                sess.add(audit_entry)

        return audit_entry

    @staticmethod
    def get_logs(
        action_filter: Optional[str] = None,
        target_entity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Fetch audit logs ordered by timestamp descending."""
        with db_manager.session_scope() as session:
            stmt = select(AuditLog)
            if action_filter:
                stmt = stmt.where(AuditLog.action.ilike(f"%{action_filter}%"))
            if target_entity:
                stmt = stmt.where(AuditLog.target_entity == target_entity)
            stmt = stmt.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
            return session.execute(stmt).scalars().all()


audit_service = AuditService()

