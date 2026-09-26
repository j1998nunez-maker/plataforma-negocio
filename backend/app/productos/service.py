# service.py = lógica de negocio de productos: alta, edición, y consulta
# del catálogo. El stock se descuenta desde el módulo de ventas (no aquí),
# porque el stock cambia como consecuencia de vender, no de editar el
# producto directamente.

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.productos.models import Producto
from app.productos.schemas import ProductoCreate, ProductoUpdate


def crear_producto(db: Session, datos: ProductoCreate) -> Producto:
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


def listar_productos(db: Session, solo_activos: bool = True) -> list[Producto]:
    consulta = select(Producto).order_by(Producto.nombre)
    if solo_activos:
        consulta = consulta.where(Producto.activo.is_(True))
    return list(db.scalars(consulta))


def obtener_producto(db: Session, producto_id: int) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    return producto


def actualizar_producto(db: Session, producto_id: int, datos: ProductoUpdate) -> Producto:
    producto = obtener_producto(db, producto_id)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return producto


def desactivar_producto(db: Session, producto_id: int) -> Producto:
    """Desactiva el producto: deja de poder venderse (ver
    `app.ventas.service.registrar_venta`) y de aparecer en el catálogo por
    defecto, pero NO se borra — su historial de ventas pasadas y su lugar
    en los reportes de KPIs quedan intactos, porque esas consultas se hacen
    sobre la tabla `ventas` (que no cambia), no sobre si el producto sigue
    activo."""
    producto = obtener_producto(db, producto_id)
    producto.activo = False
    db.commit()
    db.refresh(producto)
    return producto


def reactivar_producto(db: Session, producto_id: int) -> Producto:
    producto = obtener_producto(db, producto_id)
    producto.activo = True
    db.commit()
    db.refresh(producto)
    return producto
