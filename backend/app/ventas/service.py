# service.py = lógica de negocio de ventas: registrar la venta "con un
# clic", descontando stock del producto y guardando el precio histórico.
# También arma la lista de ventas (con nombre de producto y de vendedor ya
# resueltos, para que el frontend no tenga que hacer más consultas).
#
# Este módulo también concentra las consultas de "ventas agregadas por
# fecha" que necesitan otros módulos aparte de kpis (que está restringido a
# dueño/contador): el buscador de /venta (más vendidos del mes), el resumen
# rápido de /venta (total y operaciones de hoy) y el reporte de cierre de
# caja (total y detalle de un día cualquiera) — todos abiertos a los 3 roles
# o construidos sobre la misma fecha de Lima.

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.tiempo import hoy_lima, inicio_utc_de_fecha_lima
from app.productos.models import Producto
from app.usuarios.models import Usuario
from app.ventas.models import Venta
from app.ventas.schemas import (
    ProductoVendidoFecha,
    ResumenVentasHoy,
    VentaCreate,
    VentaOut,
)

LIMITE_MAS_VENDIDOS_MES = 12


def _a_venta_out(venta: Venta) -> VentaOut:
    return VentaOut(
        id=venta.id,
        producto_id=venta.producto_id,
        nombre_producto=venta.producto.nombre,
        usuario_id=venta.usuario_id,
        nombre_vendedor=venta.usuario.nombre_completo,
        cantidad=venta.cantidad,
        precio_unitario=float(venta.precio_unitario),
        subtotal=float(venta.subtotal),
        fecha_venta=venta.fecha_venta,
    )


def registrar_venta(db: Session, datos: VentaCreate, usuario: Usuario) -> VentaOut:
    producto = db.get(Producto, datos.producto_id)
    if producto is None or not producto.activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado."
        )
    if producto.stock_actual < datos.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Disponible: {producto.stock_actual}.",
        )

    subtotal = float(producto.precio_venta) * datos.cantidad
    venta = Venta(
        producto_id=producto.id,
        usuario_id=usuario.id,
        cantidad=datos.cantidad,
        precio_unitario=producto.precio_venta,
        subtotal=subtotal,
    )
    producto.stock_actual -= datos.cantidad

    db.add(venta)
    db.commit()
    db.refresh(venta)
    return _a_venta_out(venta)


def listar_ventas(
    db: Session, limite: int = 100, usuario_id: int | None = None
) -> list[VentaOut]:
    """Si se pasa `usuario_id`, solo trae las ventas de ese usuario (para
    que un vendedor pueda ver lo que él mismo vendió)."""
    consulta = (
        select(Venta)
        .options(joinedload(Venta.producto), joinedload(Venta.usuario))
        .order_by(Venta.fecha_venta.desc())
        .limit(limite)
    )
    if usuario_id is not None:
        consulta = consulta.where(Venta.usuario_id == usuario_id)
    ventas = db.scalars(consulta).all()
    return [_a_venta_out(v) for v in ventas]


def resumen_ventas_fecha(db: Session, fecha_lima: date) -> tuple[float, int]:
    """Total en soles y número de operaciones (ventas individuales) de un
    día cualquiera (fecha de Lima). Reutilizado por el resumen rápido de
    /venta (día de hoy) y por el reporte de cierre de caja (un día pasado
    cualquiera)."""
    desde_utc = inicio_utc_de_fecha_lima(fecha_lima)
    hasta_utc = inicio_utc_de_fecha_lima(fecha_lima + timedelta(days=1))
    fila = db.execute(
        select(func.coalesce(func.sum(Venta.subtotal), 0), func.count(Venta.id)).where(
            Venta.fecha_venta >= desde_utc, Venta.fecha_venta < hasta_utc
        )
    ).one()
    return float(fila[0]), int(fila[1])


def resumen_ventas_hoy(db: Session) -> ResumenVentasHoy:
    total, operaciones = resumen_ventas_fecha(db, hoy_lima())
    return ResumenVentasHoy(total=total, operaciones=operaciones)


def productos_vendidos_fecha(db: Session, fecha_lima: date) -> list[ProductoVendidoFecha]:
    """Ventas de un día cualquiera (fecha de Lima) agrupadas por producto —
    para el reporte diario de cierre de caja. Misma forma que
    `kpis.service.resumen_dia` (que solo mira "hoy"), pero parametrizada por
    fecha; se deja separada a propósito porque vive en un módulo con otra
    responsabilidad (reporte de cierre, no dashboard de indicadores)."""
    desde_utc = inicio_utc_de_fecha_lima(fecha_lima)
    hasta_utc = inicio_utc_de_fecha_lima(fecha_lima + timedelta(days=1))

    filas = db.execute(
        select(
            Producto.id,
            Producto.nombre,
            func.sum(Venta.cantidad).label("cantidad"),
            func.sum(Venta.subtotal).label("subtotal"),
        )
        .join(Producto, Producto.id == Venta.producto_id)
        .where(Venta.fecha_venta >= desde_utc, Venta.fecha_venta < hasta_utc)
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(Venta.subtotal).desc())
    ).all()
    return [
        ProductoVendidoFecha(
            producto_id=fila.id,
            nombre=fila.nombre,
            cantidad=int(fila.cantidad),
            subtotal=float(fila.subtotal),
        )
        for fila in filas
    ]


def productos_mas_vendidos_mes(db: Session, limite: int = LIMITE_MAS_VENDIDOS_MES) -> list[int]:
    """IDs de los productos activos más vendidos (en unidades) desde el
    inicio del mes de Lima, para la vista por defecto del buscador de
    /venta. Vacío si el negocio no tuvo ventas este mes todavía — el
    frontend cae al catálogo completo en ese caso."""
    hoy = hoy_lima()
    desde_utc = inicio_utc_de_fecha_lima(hoy.replace(day=1))

    filas = db.execute(
        select(Producto.id)
        .join(Venta, Venta.producto_id == Producto.id)
        .where(Producto.activo.is_(True), Venta.fecha_venta >= desde_utc)
        .group_by(Producto.id)
        .order_by(func.sum(Venta.cantidad).desc())
        .limit(limite)
    ).all()
    return [fila[0] for fila in filas]
