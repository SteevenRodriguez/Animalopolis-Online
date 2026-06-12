from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.audit import AuditAction
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse
from app.services.audit_service import log_event
from app.services.auth_service import authenticate, issue_token

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, payload.email, payload.password)
    if not user:
        # Log the failed attempt — no user attached.
        log_event(
            db,
            action=AuditAction.LOGIN_FAILED,
            request=request,
            success=False,
            details={"email": str(payload.email)},
        )
        db.commit()
        # Same message for unknown user and wrong password (avoid enumeration).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )
    token = issue_token(user)
    log_event(db, action=AuditAction.LOGIN, user=user, request=request)
    db.commit()
    return TokenResponse(
        access_token=token, rol=user.rol, sede=user.sede, nombre=user.nombre
    )


@router.get("/me", response_model=MeResponse)
def me(user: Usuario = Depends(get_current_user)):
    return MeResponse(
        id=str(user.id),
        email=user.email,
        nombre=user.nombre,
        rol=user.rol,
        sede=user.sede,
        is_active=user.is_active,
    )
