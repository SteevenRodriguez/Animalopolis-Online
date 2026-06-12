"""
Audit logging. One row per significant event, kept in the same DB transaction
as the action it describes — so the log can't lie: if the action rolls back,
its audit row rolls back too.

For events that happen even on failure (e.g. failed login), call `log_event()`
and then commit explicitly.
"""
from __future__ import annotations

import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction


def _ip(request: Request | None) -> str | None:
    if request is None:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return None


def _ua(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    return ua[:512] if ua else None


def log_event(
    db: Session,
    *,
    action: AuditAction | str,
    user: Usuario | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    success: bool = True,
    request: Request | None = None,
    details: dict | None = None,
    external_actor: str | None = None,
) -> AuditLog:
    """Adds an audit entry to the session. Caller is responsible for commit.

    `external_actor` is used when the caller is the WhatsApp service
    authenticated via X-API-Key (no user). It is stored in user_email
    so the trail is still searchable.
    """
    action_str = action.value if isinstance(action, AuditAction) else action
    entry = AuditLog(
        action=action_str,
        user_id=user.id if user else None,
        user_email=user.email if user else external_actor,
        user_rol=user.rol if user else ("service" if external_actor else None),
        user_sede=user.sede if user else None,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        ip=_ip(request),
        user_agent=_ua(request),
        details=details,
    )
    db.add(entry)
    return entry
