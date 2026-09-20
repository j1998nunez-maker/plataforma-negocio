# service.py = la lógica real del módulo de usuarios: verificar login,
# crear usuarios nuevos validando que el correo y el rol sean correctos.
# Se separa del router para que el endpoint solo reciba/responda HTTP, y
# aquí quede la lógica de negocio (más fácil de leer y de probar).

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hashear_contrasena, verificar_contrasena
from app.usuarios.models import ROLES_VALIDOS, Usuario
from app.usuarios.schemas import UsuarioCreate


def autenticar_usuario(db: Session, correo: str, contrasena: str) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo))
    if usuario is None or not usuario.activo or not verificar_contrasena(
        contrasena, usuario.contrasena_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )
    return usuario


def crear_usuario(db: Session, datos: UsuarioCreate) -> Usuario:
    if datos.rol not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rol inválido. Debe ser uno de: {', '.join(ROLES_VALIDOS)}",
        )
    ya_existe = db.scalar(select(Usuario).where(Usuario.correo == datos.correo))
    if ya_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo.",
        )

    usuario = Usuario(
        nombre_completo=datos.nombre_completo,
        correo=datos.correo,
        contrasena_hash=hashear_contrasena(datos.contrasena),
        rol=datos.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def listar_usuarios(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.nombre_completo)))


def desactivar_usuario(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    usuario.activo = False
    db.commit()
    db.refresh(usuario)
    return usuario
