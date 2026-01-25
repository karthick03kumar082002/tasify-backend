from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import create_login_audit_log
from contextvars import ContextVar
from sqlalchemy.orm import Mapper
from typing import Optional, Dict, Any
import json
from datetime import datetime, date
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.core.db import db_instance
from contextlib import asynccontextmanager


async def log_audit(
    db: AsyncSession,
    action: str,
    status: str,
    user_id: int = None,
    request: Request = None,
    message: str = None
):
    """
    Reusable audit logging function.

    Parameters:
    - db: AsyncSession
    - action: str ("login", "logout", etc.)
    - status: str ("success", "failure")
    - user_id: int | None
    - request: Request object (optional, to get IP and user-agent)
    - message: str | None
    """
    ip = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    await create_login_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        status=status,
        ip_address=ip,
        user_agent=user_agent,
        message=message
    )



current_user_id = ContextVar("current_user_id", default=None)
current_ip = ContextVar("current_ip", default=None)

# ------------------ AUDIT LOG MODEL ------------------

# ------------------ AUDIT LOG HELPER ------------------
def safe_json_dumps(data):
    """Safely serialize data to JSON, converting datetime and other non-serializable types."""
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        return str(o)

    return json.dumps(data, default=default)


# ------------------ AUDIT LOG FUNCTION ------------------
def add_audit_log(session, instance, action, changes=None):
    """Create an audit entry for CREATE, UPDATE, DELETE actions."""
    try:
        # ✅ Skip auditing itself or any other excluded tables
        if isinstance(instance, AuditLog) or instance.__tablename__ in {"audit_logs", "audit_logs_new"}:
            return

        table_name = instance.__tablename__
        record_id = getattr(instance, "id", None)
        user_id = current_user_id.get() or getattr(session, "current_user", None)
        ip_address = current_ip.get() or getattr(session, "client_ip", None)

        audit_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            changed_data=safe_json_dumps(changes) if changes else None,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
        )

        # Add safely — no manual conn.execute()
        session.add(audit_entry)

        print(f"[AUDIT] {action} on {table_name} (ID={record_id}) by {user_id} from {ip_address}")

    except Exception as e:
        print(f"[AUDIT ERROR] {e}")


# ------------------ SQLALCHEMY EVENT LISTENER ------------------
@event.listens_for(Session, "after_flush")
def receive_after_flush(session, flush_context):
    """Global listener for CREATE, UPDATE, DELETE events."""
    try:
        # Handle inserts
        for instance in session.new:
            if isinstance(instance, AuditLog) or instance.__tablename__ in {"audit_logs", "audit_logs_new"}:
                continue
            add_audit_log(session, instance, "CREATE", {
                c.name: getattr(instance, c.name) for c in instance.__table__.columns
            })

        # Handle updates
        for instance in session.dirty:
            if isinstance(instance, AuditLog) or instance.__tablename__ in {"audit_logs", "audit_logs_new"}:
                continue
            state = inspect(instance)
            changes = {}
            for attr in state.attrs:
                if attr.history.has_changes():
                    old = attr.history.deleted[0] if attr.history.deleted else None
                    new = attr.history.added[0] if attr.history.added else None
                    changes[attr.key] = {"old": old, "new": new}
            if changes:
                add_audit_log(session, instance, "UPDATE", changes)

        # Handle deletions
        for instance in session.deleted:
            if isinstance(instance, AuditLog) or instance.__tablename__ in {"audit_logs", "audit_logs_new"}:
                continue
            add_audit_log(session, instance, "DELETE")

    except Exception as e:
        print(f"[AUDIT ERROR in after_flush] {e}")