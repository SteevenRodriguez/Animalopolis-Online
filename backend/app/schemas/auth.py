from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    sede: str | None
    nombre: str


class MeResponse(BaseModel):
    id: str
    email: EmailStr
    nombre: str
    rol: str
    sede: str | None
    is_active: bool
