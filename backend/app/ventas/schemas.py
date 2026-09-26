# schemas.py = la forma de los datos que llegan al registrar una venta
# (solo el producto y, opcionalmente, la cantidad) y lo que se devuelve
# como comprobante.

from datetime import datetime

from pydantic import BaseModel, Field


class VentaCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(default=1, gt=0)


class VentaOut(BaseModel):
    id: int
    producto_id: int
    nombre_producto: str
    usuario_id: int
    nombre_vendedor: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    fecha_venta: datetime

    model_config = {"from_attributes": True}


class ResumenVentasHoy(BaseModel):
    """Total y operaciones de HOY para todo el negocio (no solo del usuario
    que consulta) — mismo cálculo que /kpis "Resumen de hoy", pero abierto a
    los 3 roles para el resumen rápido de /venta."""

    total: float
    operaciones: int


class ProductoVendidoFecha(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    subtotal: float
