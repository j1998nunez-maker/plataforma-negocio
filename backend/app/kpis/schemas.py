# schemas.py = la forma del resumen de indicadores que devuelve la API
# para la pantalla de KPIs simple del MVP. El análisis a fondo lo hará
# Power BI directo contra la base de datos; esto es solo un vistazo rápido.

from pydantic import BaseModel


class ProductoTop(BaseModel):
    nombre: str
    unidades_vendidas: int
    total_vendido: float


class ResumenKPIs(BaseModel):
    ventas_hoy_cantidad: int
    ventas_hoy_total: float
    ventas_mes_cantidad: int
    ventas_mes_total: float
    productos_mas_vendidos: list[ProductoTop]
    productos_por_vencer: int
