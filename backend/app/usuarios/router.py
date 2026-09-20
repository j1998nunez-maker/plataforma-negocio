# router.py = las puertas de entrada (endpoints) de sesión y usuarios.
#
# `auth_router`  -> POST /auth/login              (cualquiera con credenciales válidas)
# `usuarios_router` -> POST   /usuarios            (crear usuario, solo dueño)
#                   -> GET    /usuarios            (listar, dueño y contador)
#                   -> GET    /usuarios/me         (mis propios datos, cualquier sesión)
#                   -> PATCH  /usuarios/{id}/desactivar (solo dueño)

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import crear_token, get_current_user, requiere_rol
from app.db.session import get_db
from app.usuarios import service
from app.usuarios.models import Usuario
from app.usuarios.schemas import TokenResponse, UsuarioCreate, UsuarioOut

auth_router = APIRouter(prefix="/auth", tags=["autenticación"])
usuarios_router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@auth_router.post("/login", response_model=TokenResponse)
def login(
    formulario: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenResponse:
    """Recibe correo (en el campo `username`) y contraseña, y si son
    correctos devuelve un token JWT que el usuario usará en cada request
    siguiente (header: Authorization: Bearer <token>)."""
    usuario = service.autenticar_usuario(db, formulario.username, formulario.password)
    token = crear_token(usuario_id=usuario.id, rol=usuario.rol)
    return TokenResponse(
        access_token=token, rol=usuario.rol, nombre_completo=usuario.nombre_completo
    )


@usuarios_router.post("", response_model=UsuarioOut, status_code=201)
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno")),
) -> Usuario:
    return service.crear_usuario(db, datos)


@usuarios_router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
) -> list[Usuario]:
    return service.listar_usuarios(db)


@usuarios_router.get("/me", response_model=UsuarioOut)
def mis_datos(usuario_actual: Usuario = Depends(get_current_user)) -> Usuario:
    return usuario_actual


@usuarios_router.patch("/{usuario_id}/desactivar", response_model=UsuarioOut)
def desactivar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno")),
) -> Usuario:
    return service.desactivar_usuario(db, usuario_id)
