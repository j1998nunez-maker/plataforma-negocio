# schemas.py = la forma de los datos del cierre de caja: registrar un
# retiro, cerrar el día, y consultar el estado (de hoy o del historial).

from datetime import date, datetime

from pydantic import BaseModel, Field


class RetiroCreate(BaseModel):
    monto: float = Field(gt=0)
    motivo: str = Field(min_length=1, max_length=200)


class RetiroOut(BaseModel):
    id: int
    fecha: date
    monto: float
    motivo: str
    usuario_id: int
    nombre_usuario: str
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class CierreCreate(BaseModel):
    efectivo_contado: float = Field(ge=0)


class CierreOut(BaseModel):
    id: int
    fecha: date
    efectivo_esperado: float
    efectivo_contado: float
    diferencia: float
    usuario_id: int
    nombre_usuario: str
    estado: str
    revisado_por_id: int | None = None
    nombre_revisor: str | None = None
    fecha_revision: datetime | None = None
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class EstadoCajaHoy(BaseModel):
    fecha: date
    cerrado: bool
    # Total vendido en efectivo hoy, menos retiros de hoy, hasta este
    # momento — se recalcula cada vez que se consulta (no se guarda hasta
    # el cierre).
    efectivo_esperado_hasta_ahora: float
    retiros: list[RetiroOut]
    cierre: CierreOut | None = None
