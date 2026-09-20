# models.py = el diseño de la tabla "productos": el catálogo del negocio.
# Esta tabla es la fuente única del nombre de cada producto — ventas nunca
# guarda texto libre, siempre apunta aquí por `producto_id`. Así Power BI
# no se topa con "Paracetamol" vs "paracetamol 500mg" como si fueran cosas
# distintas.

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    categoria: Mapped[str] = mapped_column(String(80), nullable=True)
    precio_venta: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
