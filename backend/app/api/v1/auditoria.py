import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require
from app.core.permissions import Capability
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.usuario import Usuario
from app.schemas.audit import AuditLogOut
from app.schemas.common import Page, PageParams

router = APIRouter()


@router.get("", response_model=Page[AuditLogOut])
def list_entries(
    params: PageParams = Depends(),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: uuid.UUID | None = Query(default=None),
    success: bool | None = Query(default=None),
    _: Usuario = Depends(require(Capability.AUDIT_READ)),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
    if desde is not None:
        stmt = stmt.where(AuditLog.timestamp >= desde)
    if hasta is not None:
        stmt = stmt.where(AuditLog.timestamp <= hasta)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type is not None:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if resource_id is not None:
        stmt = stmt.where(AuditLog.resource_id == resource_id)
    if success is not None:
        stmt = stmt.where(AuditLog.success == success)

    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()
    items = db.execute(stmt.offset(params.offset).limit(params.size)).scalars().all()
    return Page[AuditLogOut](
        items=[AuditLogOut.model_validate(a) for a in items],
        total=total,
        page=params.page,
        size=params.size,
    )
