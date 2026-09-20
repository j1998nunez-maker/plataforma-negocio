# schemas.py = la "forma" que deben tener los datos que entran y salen por
# la API. Son distintos de models.py: los modelos son la tabla en la base
# de datos, los schemas son el JSON que viaja por internet. Por ejemplo,
# `UsuarioOut` nunca incluye la contraseña, aunque la tabla sí la tenga.

from pydantic import BaseModel, EmailStr, Field

from app.usuarios.models import ROLES_VALIDOS


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    nombre_completo: str


class UsuarioCreate(BaseModel):
    nombre_completo: str = Field(min_length=1, max_length=150)
    correo: EmailStr
    contrasena: str = Field(min_length=6, max_length=100)
    rol: str = Field(description=f"Uno de: {', '.join(ROLES_VALIDOS)}")


class UsuarioOut(BaseModel):
    id: int
    nombre_completo: str
    correo: EmailStr
    rol: str
    activo: bool

    model_config = {"from_attributes": True}
