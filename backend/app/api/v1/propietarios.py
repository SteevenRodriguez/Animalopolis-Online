import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.permissions import Capability, has_capability
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction
from app.schemas.propietario import PropietarioOut, PropietarioUpdate
from app.services.audit_service import log_event
from app.services.propietario_service import (
    WhatsAppAlreadyInUse,
    get_propietario,
    update_propietario,
)
from app.services.whatsapp_normalizer import InvalidWhatsAppNumber

router = APIRouter()


@router.get("/{propietario_id}", response_model=PropietarioOut)
def get_one(
    propietario_id: uuid.UUID,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Any authenticated user can look up a propietario by id (they get the id
    # from an alta/examen they already see). Sede scoping happens at the
    # alta/examen level — propietario is shared across sedes by design.
    prop = get_propietario(db, propietario_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    return PropietarioOut.model_validate(prop)


@router.patch("/{propietario_id}", response_model=PropietarioOut)
def patch(
    propietario_id: uuid.UUID,
    payload: PropietarioUpdate,
    request: Request,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_capability(user.rol, Capability.PROPIETARIO_UPDATE):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    prop = get_propietario(db, propietario_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    try:
        diff = update_propietario(
            db, prop, nombre=payload.nombre, whatsapp_raw=payload.whatsapp,
        )
    except InvalidWhatsAppNumber as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from None
    except WhatsAppAlreadyInUse as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None
    log_event(
        db,
        action=AuditAction.UPDATE_PROPIETARIO,
        user=user,
        request=request,
        resource_type="propietario",
        resource_id=prop.id,
        details={"diff": diff} if diff else {"diff": "noop"},
    )
    db.commit()
    db.refresh(prop)
    return PropietarioOut.model_validate(prop)
