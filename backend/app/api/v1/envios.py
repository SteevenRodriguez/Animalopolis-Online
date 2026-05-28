import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.db.session import get_db
from app.models.alta import Alta
from app.schemas.alta import AltaOut
from app.schemas.common import Page, PageParams
from app.services.alta_service import build_alta_query, mark_sent

router = APIRouter()


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
