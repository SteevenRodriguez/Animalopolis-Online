import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, sede_scope_for
from app.core.permissions import (
    Capability,
    has_capability,
)
from app.db.session import get_db
from app.models.alta import Alta
from app.models.usuario import Usuario
from app.schemas.alta import AltaCreate, AltaOut
from app.schemas.common import Page, PageParams
from app.services.alta_service import (
    build_alta_query,
    create_alta,
    get_alta_scoped,
)
from app.services.whatsapp_normalizer import InvalidWhatsAppNumber

router = APIRouter()


@router.post("", response_model=AltaOut, status_code=status.HTTP_201_CREATED)
def create(
    payload: AltaCreate,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_capability(user.rol, Capability.ALTA_CREATE):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    # Staff can only create altas in their own sede.
    if sede_scope_for(user) is not None and payload.sede.value != user.sede:
        raise HTTPException(
            status_code=403, detail="No puedes crear altas en otra sede"
        )
    try:
        alta = create_alta(
            db,
            sede=payload.sede.value,
            nombre_mascota=payload.nombre_mascota,
            nombre_propietario=payload.nombre_propietario,
            whatsapp_raw=payload.whatsapp,
            fecha_atencion=payload.fecha_atencion,
            tipo_consulta=payload.tipo_consulta.value,
            consentimiento=payload.consentimiento,
            created_by=user,
        )
        db.commit()
    except InvalidWhatsAppNumber as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from None
    db.refresh(alta)
    return AltaOut.model_validate(alta)


@router.get("", response_model=Page[AltaOut])
def list_altas(
    params: PageParams = Depends(),
    sede: str | None = Query(default=None),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    estado_envio: str | None = Query(default=None),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (
        has_capability(user.rol, Capability.ALTA_READ_ALL)
        or has_capability(user.rol, Capability.ALTA_READ_OWN_SEDE)
    ):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    restrict = sede_scope_for(user)
    stmt = build_alta_query(
        sede=sede,
        desde=desde,
        hasta=hasta,
        estado_envio=estado_envio,
        restrict_to_sede=restrict,
    )
    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()
    items = db.execute(stmt.offset(params.offset).limit(params.size)).scalars().all()
    return Page[AltaOut](
        items=[AltaOut.model_validate(a) for a in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{alta_id}", response_model=AltaOut)
def get_alta(
    alta_id: uuid.UUID,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (
        has_capability(user.rol, Capability.ALTA_READ_ALL)
        or has_capability(user.rol, Capability.ALTA_READ_OWN_SEDE)
    ):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    alta = get_alta_scoped(db, alta_id, sede_scope_for(user))
    if not alta:
        raise HTTPException(status_code=404, detail="Alta no encontrada")
    return AltaOut.model_validate(alta)
