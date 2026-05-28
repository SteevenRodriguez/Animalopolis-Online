import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.config import get_settings
from app.db.session import get_db
from app.models.alta import Alta
from app.models.examen import Examen
from app.schemas.alta import AltaOut
from app.schemas.common import Page, PageParams
from app.schemas.examen import ExamenOut, PresignedUrlOut
from app.services.alta_service import build_alta_query, mark_sent
from app.services.examen_service import build_examen_query, mark_sent_examen
from app.storage.factory import get_storage

router = APIRouter()


# ---------- ALTAS ----------

@router.get(
    "/altas/pendientes",
    response_model=Page[AltaOut],
    dependencies=[Depends(require_api_key)],
)
def altas_pendientes(
    params: PageParams = Depends(),
    sede: str | None = Query(default=None),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = build_alta_query(
        sede=sede,
        desde=desde,
        hasta=hasta,
        estado_envio="pendiente",
        restrict_to_sede=None,
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


@router.post(
    "/altas/{alta_id}/marcar-enviado",
    response_model=AltaOut,
    dependencies=[Depends(require_api_key)],
)
def marcar_alta_enviada(alta_id: uuid.UUID, db: Session = Depends(get_db)):
    alta = db.get(Alta, alta_id)
    if not alta:
        raise HTTPException(status_code=404, detail="Alta no encontrada")
    if alta.estado_envio == "enviado":
        return AltaOut.model_validate(alta)
    mark_sent(db, alta)
    db.commit()
    db.refresh(alta)
    return AltaOut.model_validate(alta)


# ---------- EXAMENES ----------

@router.get(
    "/examenes/pendientes",
    response_model=Page[ExamenOut],
    dependencies=[Depends(require_api_key)],
)
def examenes_pendientes(
    params: PageParams = Depends(),
    sede: str | None = Query(default=None),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = build_examen_query(
        sede=sede,
        desde=desde,
        hasta=hasta,
        estado_envio="pendiente",
        restrict_to_sede=None,
    )
    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()
    items = db.execute(stmt.offset(params.offset).limit(params.size)).scalars().all()
    return Page[ExamenOut](
        items=[ExamenOut.model_validate(e) for e in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get(
    "/examenes/{examen_id}/file-url",
    response_model=PresignedUrlOut,
    dependencies=[Depends(require_api_key)],
)
def envios_examen_file_url(examen_id: uuid.UUID, db: Session = Depends(get_db)):
    examen = db.get(Examen, examen_id)
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    settings = get_settings()
    storage = get_storage()
    url = storage.presigned_url(
        examen.storage_key, settings.S3_PRESIGNED_EXPIRES_SECONDS
    )
    return PresignedUrlOut(
        url=url,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.S3_PRESIGNED_EXPIRES_SECONDS),
    )


@router.post(
    "/examenes/{examen_id}/marcar-enviado",
    response_model=ExamenOut,
    dependencies=[Depends(require_api_key)],
)
def marcar_examen_enviado(examen_id: uuid.UUID, db: Session = Depends(get_db)):
    examen = db.get(Examen, examen_id)
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    if examen.estado_envio == "enviado":
        return ExamenOut.model_validate(examen)
    mark_sent_examen(db, examen)
    db.commit()
    db.refresh(examen)
    return ExamenOut.model_validate(examen)
