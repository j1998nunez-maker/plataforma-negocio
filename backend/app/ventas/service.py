# service.py = lógica de negocio de ventas: registrar la venta "con un
# clic", descontando stock del producto y guardando el precio histórico.
# También arma la lista de ventas (con nombre de producto y de vendedor ya
# resueltos, para que el frontend no tenga que hacer más consultas).

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.productos.models import Producto
from app.usuarios.models import Usuario
from app.ventas.models import Venta
from app.ventas.schemas import VentaCreate, VentaOut


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
