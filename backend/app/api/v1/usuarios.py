import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require
from app.core.permissions import Capability
from app.core.security import hash_password
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.common import Page, PageParams
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
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
    _: Usuario = Depends(require(Capability.USER_MANAGE)),
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
    _: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if payload.nombre is not None:
        user.nombre = payload.nombre
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.rol is not None:
        user.rol = payload.rol.value
    if payload.sede is not None:
        user.sede = payload.sede.value
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return UsuarioOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_usuario(
    user_id: uuid.UUID,
    me: Usuario = Depends(require(Capability.USER_MANAGE)),
    db: Session = Depends(get_db),
):
    if user_id == me.id:
        raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")
    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.is_active = False
    db.commit()
    return None
