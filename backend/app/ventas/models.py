# models.py = el diseño de la tabla "ventas": el registro de cada venta,
# ligado a un producto del catálogo (`producto_id`) y a quién la vendió
# (`usuario_id`). `precio_unitario` y `subtotal` se copian al momento de
# vender para conservar el precio histórico real, aunque el precio de
# lista del producto cambie después (decisión confirmada contigo).

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_venta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    producto = relationship("Producto")
    usuario = relationship("Usuario")
