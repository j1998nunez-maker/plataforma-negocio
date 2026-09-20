# security.py = todo lo relacionado a "candados":
#
# 1. Contraseñas: `hashear_contrasena` las encripta antes de guardarlas;
#    `verificar_contrasena` compara una contraseña escrita en el login
#    contra esa versión encriptada (nunca se guarda ni se compara texto
#    plano).
# 2. Tokens JWT: `crear_token` genera la "credencial digital" que recibe un
#    usuario al hacer login (incluye su id y su rol). `decodificar_token` la
#    lee de vuelta en cada request para saber quién eres y qué puedes hacer.
# 3. Dependencias de FastAPI (`get_current_user`, `requiere_rol`): se ponen
#    en los endpoints para exigir "debes tener sesión" o "debes ser dueño",
#    por ejemplo.

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.usuarios.models import Usuario

# Le dice a FastAPI/Swagger dónde está el endpoint de login, para que el
# botón "Authorize" de la documentación automática (/docs) funcione.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hashear_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_contrasena(contrasena: str, contrasena_hash: str) -> bool:
    return bcrypt.checkpw(contrasena.encode("utf-8"), contrasena_hash.encode("utf-8"))


def crear_token(usuario_id: int, rol: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRACION_MINUTOS)
    payload = {"sub": str(usuario_id), "rol": rol, "exp": expira}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión. Vuelve a iniciar sesión.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Usuario:
    """Lee el token JWT que envía el navegador y devuelve el usuario real
    de la base de datos. Si el token es inválido, expiró, o el usuario ya
    no existe/está inactivo, corta el request con un error 401."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        usuario_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _credenciales_invalidas()

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise _credenciales_invalidas()
    return usuario


def requiere_rol(*roles_permitidos: str):
    """Genera una dependencia que exige que el usuario logueado tenga uno
    de los roles indicados. Uso en un endpoint:

        @router.post("/productos")
        def crear_producto(usuario: Usuario = Depends(requiere_rol("dueno"))):
            ...
    """

    def verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu rol no tiene permiso para hacer esto.",
            )
        return usuario

    return verificar
