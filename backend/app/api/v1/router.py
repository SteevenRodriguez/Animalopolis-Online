from fastapi import APIRouter

from app.api.v1 import (
    altas,
    auditoria,
    auth,
    envios,
    examenes,
    mascotas,
    propietarios,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(altas.router, prefix="/altas", tags=["altas"])
api_router.include_router(examenes.router, prefix="/examenes", tags=["examenes"])
api_router.include_router(propietarios.router, prefix="/propietarios", tags=["propietarios"])
api_router.include_router(mascotas.router, prefix="/mascotas", tags=["mascotas"])
api_router.include_router(auditoria.router, prefix="/auditoria", tags=["auditoria"])
api_router.include_router(envios.router, prefix="/envios", tags=["envios"])
