# models.py = el diseño de la tabla "usuarios" en PostgreSQL: quién puede
# entrar al sistema, con qué contraseña (encriptada) y qué rol tiene.
#
# `rol` es un texto limitado a 3 valores (CHECK constraint) en vez de una
# tabla aparte de roles: con solo 3 roles fijos para el MVP, una tabla extra
# sería sobre-diseño. Si en el futuro los roles se vuelven dinámicos,
# migrar a una tabla es un cambio sencillo.

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ROLES_VALIDOS = ("dueno", "contador", "vendedor")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(f"rol IN {ROLES_VALIDOS}", name="ck_usuarios_rol_valido"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
