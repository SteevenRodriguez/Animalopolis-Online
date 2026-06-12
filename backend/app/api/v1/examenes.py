import uuid
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, sede_scope_for
from app.config import get_settings
from app.core.permissions import Capability, has_capability
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.enums import Sede, TipoExamen
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction
from app.schemas.common import Page, PageParams
from app.schemas.examen import ExamenOut, ExamenUpdate, PresignedUrlOut
from app.services.audit_service import log_event
from app.services.examen_service import (
    build_examen_query,
    create_examen,
    get_examen_scoped,
    update_examen,
)
from app.services.file_validation import FileValidationError, validate_file
from app.services.whatsapp_normalizer import InvalidWhatsAppNumber
from app.storage.factory import get_storage

router = APIRouter()


@router.post("", response_model=ExamenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_examen_route(
    request: Request,
    sede: Sede = Form(...),
    nombre_mascota: str = Form(..., min_length=1, max_length=255),
    nombre_propietario: str = Form(..., min_length=1, max_length=255),
    whatsapp: str = Form(..., min_length=4, max_length=32),
    tipo_examen: TipoExamen = Form(...),
    consentimiento: bool = Form(...),
    file: UploadFile = File(...),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not has_capability(user.rol, Capability.EXAMEN_CREATE):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    if sede_scope_for(user) is not None and sede.value != user.sede:
        raise HTTPException(
            status_code=403, detail="No puedes crear exámenes en otra sede"
        )
    if not consentimiento:
        raise HTTPException(
            status_code=422, detail="El consentimiento es obligatorio"
        )

    cl = request.headers.get("content-length")
    if cl:
        try:
            if int(cl) > settings.MAX_UPLOAD_SIZE_BYTES + 4096:
                raise HTTPException(
                    status_code=413, detail="Archivo demasiado grande"
                )
        except ValueError:
            pass

    data = await file.read()
    declared_mime = file.content_type or "application/octet-stream"
    try:
        mime = validate_file(
            data=data,
            declared_mime=declared_mime,
            allowed_mimes=settings.allowed_upload_mime_list,
            max_size=settings.MAX_UPLOAD_SIZE_BYTES,
        )
    except FileValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    try:
        examen = create_examen(
            db,
            sede=sede.value,
            nombre_mascota=nombre_mascota,
            nombre_propietario=nombre_propietario,
            whatsapp_raw=whatsapp,
            tipo_examen=tipo_examen.value,
            file_bytes=data,
            file_name=file.filename or "archivo",
            file_mime=mime,
            created_by=user,
            storage=get_storage(),
        )
        log_event(
            db,
            action=AuditAction.CREATE_EXAMEN,
            user=user,
            request=request,
            resource_type="examen",
            resource_id=examen.id,
            details={
                "sede": examen.sede,
                "tipo_examen": examen.tipo_examen,
                "archivo_size_bytes": examen.archivo_size_bytes,
                "archivo_mime": examen.archivo_mime,
            },
        )
        db.commit()
    except InvalidWhatsAppNumber as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from None
    db.refresh(examen)
    return ExamenOut.model_validate(examen)


@router.get("", response_model=Page[ExamenOut])
def list_examenes(
    params: PageParams = Depends(),
    sede: str | None = Query(default=None),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    estado_envio: str | None = Query(default=None),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (
        has_capability(user.rol, Capability.EXAMEN_READ_ALL)
        or has_capability(user.rol, Capability.EXAMEN_READ_OWN_SEDE)
    ):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    restrict = sede_scope_for(user)
    stmt = build_examen_query(
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
    return Page[ExamenOut](
        items=[ExamenOut.model_validate(e) for e in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.get("/{examen_id}", response_model=ExamenOut)
def get_examen(
    examen_id: uuid.UUID,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not (
        has_capability(user.rol, Capability.EXAMEN_READ_ALL)
        or has_capability(user.rol, Capability.EXAMEN_READ_OWN_SEDE)
    ):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    examen = get_examen_scoped(db, examen_id, sede_scope_for(user))
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    return ExamenOut.model_validate(examen)


@router.patch("/{examen_id}", response_model=ExamenOut)
def patch_examen(
    examen_id: uuid.UUID,
    payload: ExamenUpdate,
    request: Request,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_capability(user.rol, Capability.EXAMEN_UPDATE):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    examen = get_examen_scoped(db, examen_id, sede_scope_for(user))
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    diff = update_examen(
        db, examen,
        tipo_examen=payload.tipo_examen.value if payload.tipo_examen else None,
    )
    log_event(
        db,
        action=AuditAction.UPDATE_EXAMEN,
        user=user,
        request=request,
        resource_type="examen",
        resource_id=examen.id,
        details={"diff": diff} if diff else {"diff": "noop"},
    )
    db.commit()
    db.refresh(examen)
    return ExamenOut.model_validate(examen)


@router.get("/{examen_id}/file-url", response_model=PresignedUrlOut)
def get_examen_file_url(
    examen_id: uuid.UUID,
    request: Request,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_capability(user.rol, Capability.EXAMEN_DOWNLOAD):
        raise HTTPException(status_code=403, detail="Permiso insuficiente")
    examen = get_examen_scoped(db, examen_id, sede_scope_for(user))
    if not examen:
        raise HTTPException(status_code=404, detail="Examen no encontrado")
    settings = get_settings()
    storage = get_storage()
    url = storage.presigned_url(
        examen.storage_key, settings.S3_PRESIGNED_EXPIRES_SECONDS
    )
    log_event(
        db,
        action=AuditAction.DOWNLOAD_EXAMEN,
        user=user,
        request=request,
        resource_type="examen",
        resource_id=examen.id,
        details={"via": "dashboard"},
    )
    db.commit()
    return PresignedUrlOut(
        url=url,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.S3_PRESIGNED_EXPIRES_SECONDS),
    )
