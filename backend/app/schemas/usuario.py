import uuid

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.enums import Rol, Sede


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    nombre: str = Field(min_length=1, max_length=255)
    rol: Rol
    sede: Sede | None = None

    @model_validator(mode="after")
    def validate_rol_sede(self):
        if self.rol in (Rol.staff, Rol.consulta) and self.sede is None:
            raise ValueError(f"{self.rol.value} requiere sede asignada")
        if self.rol == Rol.admin and self.sede is not None:
            # admin has access to all sedes; sede must be null for clarity.
            self.sede = None
        return self


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=10, max_length=128)
    rol: Rol | None = None
    sede: Sede | None = None
    is_active: bool | None = None


class UsuarioOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    nombre: str
    rol: str
    sede: str | None
    is_active: bool

    model_config = {"from_attributes": True}
