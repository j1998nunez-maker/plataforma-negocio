# schemas.py = la forma del resumen de indicadores que devuelve la API
# para la pantalla de KPIs simple del MVP. El análisis a fondo lo hará
# Power BI directo contra la base de datos; esto es solo un vistazo rápido.

from datetime import date

from pydantic import BaseModel


class ProductoTop(BaseModel):
    nombre: str
    unidades_vendidas: int
    total_vendido: float


class ResumenDiaItem(BaseModel):
    producto_id: int
    nombre: str
    cantidad_total: int
    subtotal_total: float
    operaciones: int


class PuntoHistoricoDiario(BaseModel):
    fecha: date
    total: float


class ResumenMesItem(BaseModel):
    producto_id: int
    nombre: str
    unidades_vendidas: int
    total_vendido: float
    operaciones: int


class PuntoDiario(BaseModel):
    fecha: date
    cantidad: int


class HistoricoProductoItem(BaseModel):
    producto_id: int
    nombre: str
    puntos: list[PuntoDiario]


class ProductoVencido(BaseModel):
    producto_id: int
    nombre: str
    fecha_vencimiento: date
    stock_actual: int


class ProductoAgotado(BaseModel):
    producto_id: int
    nombre: str
    # Puede no tener fecha de vencimiento registrada (campo opcional en el
    # catálogo) — no implica que el producto esté vencido, son alertas
    # independientes.
    fecha_vencimiento: date | None = None


class UnidadesPorProductoPeriodo(BaseModel):
    producto_id: int
    nombre: str
    # Alineado con `JornadaHoy.periodos` (mismo índice = mismo periodo).
    unidades_por_periodo: list[int]


class ResumenFueraDeHorario(BaseModel):
    """Ventas registradas fuera de 08:00-20:00 (hora de Lima) — no se
    descartan, se reportan aparte porque el horario del piloto es
    provisional."""

    cantidad: int
    subtotal: float
    operaciones: int


class JornadaHoy(BaseModel):
    fecha: date
    # Etiquetas de los 4 periodos de 3 horas, ej. ["08:00–11:00", ...].
    periodos: list[str]
    # Alineados con `periodos` (mismo índice = mismo periodo).
    ingresos_por_periodo: list[float]
    operaciones_por_periodo: list[int]
    unidades_por_producto: list[UnidadesPorProductoPeriodo]
    fuera_de_horario: ResumenFueraDeHorario


class ResumenKPIs(BaseModel):
    ventas_hoy_cantidad: int
    ventas_hoy_total: float
    ventas_hoy_operaciones: int
    ventas_mes_cantidad: int
    ventas_mes_total: float
    ventas_mes_operaciones: int
    productos_mas_vendidos: list[ProductoTop]
    # Por vencer en los próximos 30 días (sin contar los que ya vencieron —
    # esos tienen su propia alerta separada en `productos_ya_vencidos`).
    productos_por_vencer: int
    # Alerta separada y más urgente: productos activos cuya fecha de
    # vencimiento ya pasó, sin importar el stock (incluso con stock 0, para
    # que el dueño sepa que debe darlos de baja del catálogo).
    productos_ya_vencidos: list[ProductoVencido]
    # Alerta independiente: productos activos con stock 0. Un producto
    # vencido Y agotado aparece en las dos listas a la vez — no se ocultan
    # entre sí.
    productos_agotados: list[ProductoAgotado]
    # El producto activo con menos unidades vendidas en los últimos 30 días
    # (o 0 si no tuvo ninguna venta) — para que el dueño sepa qué producto
    # conviene dejar de comprar. None solo si no hay ningún producto activo.
    producto_menor_rotacion: ProductoTop | None = None
