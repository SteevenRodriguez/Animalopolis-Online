import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require
from app.core.permissions import Capability
from app.core.security import hash_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction
from app.schemas.common import Page, PageParams
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.audit_service import log_event
from app.services.auth_service import create_user

router = APIRouter()


@router.get("", response_model=Page[UsuarioOut])
def list_usuarios(
    params: PageParams = Depends(),
    _: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    total = db.execute(select(func.count()).select_from(Usuario)).scalar_one()
    items = db.execute(
        select(Usuario)
        .order_by(Usuario.created_at.desc())
        .offset(params.offset)
        .limit(params.size)
    ).scalars().all()
    return Page[UsuarioOut](
        items=[UsuarioOut.model_validate(u) for u in items],
        total=total,
        page=params.page,
        size=params.size,
    )


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def create_usuario(
    payload: UsuarioCreate,
    request: Request,
    actor: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    try:
        user = create_user(
            db,
            email=str(payload.email),
            password=payload.password,
            nombre=payload.nombre,
            rol=payload.rol.value,
            sede=payload.sede.value if payload.sede else None,
        )
        log_event(
            db,
            action=AuditAction.CREATE_USER,
            user=actor,
            request=request,
            resource_type="usuario",
            resource_id=user.id,
            details={"email": user.email, "rol": user.rol, "sede": user.sede},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email ya existe"
        ) from None
    db.refresh(user)
    return UsuarioOut.model_validate(user)


@router.patch("/{user_id}", response_model=UsuarioOut)
def update_usuario(
    user_id: uuid.UUID,
    payload: UsuarioUpdate,
    request: Request,
    actor: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    changed: dict = {}
    if payload.nombre is not None and payload.nombre != user.nombre:
        changed["nombre"] = {"from": user.nombre, "to": payload.nombre}
        user.nombre = payload.nombre
    if payload.password is not None:
        changed["password"] = "reset"
        user.password_hash = hash_password(payload.password)
    if payload.rol is not None and payload.rol.value != user.rol:
        changed["rol"] = {"from": user.rol, "to": payload.rol.value}
        user.rol = payload.rol.value
    if payload.sede is not None and payload.sede.value != user.sede:
        changed["sede"] = {"from": user.sede, "to": payload.sede.value}
        user.sede = payload.sede.value
    if payload.is_active is not None and payload.is_active != user.is_active:
        changed["is_active"] = {"from": user.is_active, "to": payload.is_active}
        user.is_active = payload.is_active
    log_event(
        db,
        action=AuditAction.UPDATE_USER,
        user=actor,
        request=request,
        resource_type="usuario",
        resource_id=user.id,
        details={"diff": changed} if changed else {"diff": "noop"},
    )
    db.commit()
    db.refresh(user)
    return UsuarioOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_usuario(
    user_id: uuid.UUID,
    request: Request,
    actor: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    if user_id == actor.id:
        raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")
    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = False
    log_event(
        db,
        action=AuditAction.DEACTIVATE_USER,
        user=actor,
        request=request,
        resource_type="usuario",
        resource_id=user.id,
        details={"email": user.email},
    )
    db.commit()
    return None
