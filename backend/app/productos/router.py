# router.py = endpoints del catálogo de productos.
#
# GET  /productos            -> cualquier sesión (el vendedor necesita ver
#                                el catálogo para registrar una venta)
# POST /productos            -> dueño y contador
# PATCH /productos/{id}       -> dueño y contador (editar precio/stock/etc.)
# PATCH /productos/{id}/desactivar -> dueño y contador

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, requiere_rol
from app.db.session import get_db
from app.productos import service
from app.productos.schemas import ProductoCreate, ProductoOut, ProductoUpdate
from app.usuarios.models import Usuario

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get("", response_model=list[ProductoOut])
def listar_productos(
    db: Session = Depends(get_db), _: Usuario = Depends(get_current_user)
) -> list:
    return service.listar_productos(db)


@router.post("", response_model=ProductoOut, status_code=201)
def crear_producto(
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.crear_producto(db, datos)


@router.patch("/{producto_id}", response_model=ProductoOut)
def actualizar_producto(
    producto_id: int,
    datos: ProductoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.actualizar_producto(db, producto_id, datos)


@router.patch("/{producto_id}/desactivar", response_model=ProductoOut)
def desactivar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.desactivar_producto(db, producto_id)
