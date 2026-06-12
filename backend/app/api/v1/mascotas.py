import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import Capability, has_capability
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction
from app.schemas.mascota import MascotaOut, MascotaUpdate
from app.services.audit_service import log_event
from app.services.mascota_service import get_mascota, update_mascota

router = APIRouter()


@router.get("/{mascota_id}", response_model=MascotaOut)
def get_one(
    mascota_id: uuid.UUID,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mascota = get_mascota(db, mascota_id)
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    return MascotaOut.model_validate(mascota)


@router.patch("/{mascota_id}", response_model=MascotaOut)
def patch(
    mascota_id: uuid.UUID,
    payload: MascotaUpdate,
    request: Request,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_capability(user.rol, Capability.MASCOTA_UPDATE):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    mascota = get_mascota(db, mascota_id)
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    diff = update_mascota(db, mascota, nombre=payload.nombre)
    log_event(
        db,
        action=AuditAction.UPDATE_MASCOTA,
        user=user,
        request=request,
        resource_type="mascota",
        resource_id=mascota.id,
        details={"diff": diff} if diff else {"diff": "noop"},
    )
    db.commit()
    db.refresh(mascota)
    return MascotaOut.model_validate(mascota)
