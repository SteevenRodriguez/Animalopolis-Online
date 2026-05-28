from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.usuario import Usuario


def authenticate(db: Session, email: str, password: str) -> Usuario | None:
    user = db.execute(
        select(Usuario).where(Usuario.email == email.lower())
    ).scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def issue_token(user: Usuario) -> str:
    return create_access_token(
        subject=str(user.id),
        extra_claims={"rol": user.rol, "sede": user.sede},
    )


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    nombre: str,
    rol: str,
    sede: str | None,
) -> Usuario:
    user = Usuario(
        email=email.lower(),
        password_hash=hash_password(password),
        nombre=nombre,
        rol=rol,
        sede=sede,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user
