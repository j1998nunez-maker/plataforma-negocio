# models.py = el diseño de las tablas del cierre de caja diario: una sola
# caja para todo el negocio por día (no una caja por vendedor — decisión
# confirmada con el dueño).
#
# `RetiroCaja` = cada retiro de efectivo que alguien hizo durante el día
# (monto + motivo), antes de cerrar. `CierreCaja` = el cierre del día: lo
# que debería haber en caja (ventas en efectivo - retiros) contra lo que se
# contó físicamente, y el estado de revisión del dueño (punto 5).

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ESTADO_PENDIENTE_REVISION = "pendiente_revision"
ESTADO_REVISADO = "revisado"


class RetiroCaja(Base):
    __tablename__ = "retiros_caja"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    motivo: Mapped[str] = mapped_column(String(200), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class CierreCaja(Base):
    __tablename__ = "cierres_caja"
    __table_args__ = (UniqueConstraint("fecha", name="uq_cierres_caja_fecha"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    efectivo_esperado: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    efectivo_contado: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    diferencia: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ESTADO_PENDIENTE_REVISION
    )
    revisado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    revisado_por = relationship("Usuario", foreign_keys=[revisado_por_id])
