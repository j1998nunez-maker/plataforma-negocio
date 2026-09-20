# service.py = calcula los indicadores (KPIs) para la pantalla simple del
# MVP: ventas de hoy, ventas del mes, productos más vendidos, y cuántos
# productos están por vencer pronto (alerta útil para farmacia/botica).
#
# Esto es un resumen rápido para la app. El análisis detallado en Power BI
# se hace directo contra las tablas `ventas` y `productos`.

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.kpis.schemas import ProductoTop, ResumenKPIs
from app.productos.models import Producto
from app.ventas.models import Venta

DIAS_ALERTA_VENCIMIENTO = 30


def _rango_cantidad_total(db: Session, desde: date) -> tuple[int, float]:
    fila = db.execute(
        select(func.coalesce(func.sum(Venta.cantidad), 0), func.coalesce(func.sum(Venta.subtotal), 0))
        .where(func.date(Venta.fecha_venta) >= desde)
    ).one()
    return int(fila[0]), float(fila[1])


def obtener_resumen(db: Session) -> ResumenKPIs:
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    ventas_hoy_cantidad, ventas_hoy_total = _rango_cantidad_total(db, hoy)
    ventas_mes_cantidad, ventas_mes_total = _rango_cantidad_total(db, inicio_mes)

    top_productos = db.execute(
        select(
            Producto.nombre,
            func.sum(Venta.cantidad).label("unidades"),
            func.sum(Venta.subtotal).label("total"),
        )
        .join(Producto, Producto.id == Venta.producto_id)
        .group_by(Producto.nombre)
        .order_by(func.sum(Venta.cantidad).desc())
        .limit(5)
    ).all()

    productos_por_vencer = db.scalar(
        select(func.count(Producto.id)).where(
            Producto.activo.is_(True),
            Producto.fecha_vencimiento.is_not(None),
            Producto.fecha_vencimiento <= hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO),
        )
    )

    return ResumenKPIs(
        ventas_hoy_cantidad=ventas_hoy_cantidad,
        ventas_hoy_total=ventas_hoy_total,
        ventas_mes_cantidad=ventas_mes_cantidad,
        ventas_mes_total=ventas_mes_total,
        productos_mas_vendidos=[
            ProductoTop(nombre=fila.nombre, unidades_vendidas=int(fila.unidades), total_vendido=float(fila.total))
            for fila in top_productos
        ],
        productos_por_vencer=productos_por_vencer or 0,
    )
