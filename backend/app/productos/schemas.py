# schemas.py = la forma de los datos de producto que entran/salen por la
# API (crear producto, actualizar stock/precio, listar el catálogo).

from datetime import date

from pydantic import BaseModel, Field


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    categoria: str | None = Field(default=None, max_length=80)
    precio_venta: float = Field(gt=0)
    stock_actual: int = Field(ge=0, default=0)
    fecha_vencimiento: date | None = None


class ProductoUpdate(BaseModel):
    """Todos los campos son opcionales: solo se actualiza lo que se envía."""

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    categoria: str | None = None
    precio_venta: float | None = Field(default=None, gt=0)
    stock_actual: int | None = Field(default=None, ge=0)
    fecha_vencimiento: date | None = None
    activo: bool | None = None


class ProductoOut(BaseModel):
    id: int
    nombre: str
    categoria: str | None
    precio_venta: float
    stock_actual: int
    fecha_vencimiento: date | None
    activo: bool

    model_config = {"from_attributes": True}
