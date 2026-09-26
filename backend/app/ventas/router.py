# router.py = endpoints de ventas.
#
# POST /ventas               -> registrar una venta con un clic (dueño, contador o vendedor)
# GET  /ventas                -> historial completo (solo dueño y contador, ven ingresos totales)
# GET  /ventas/mias           -> mis propias ventas (cualquier sesión, útil para el vendedor)
# GET  /ventas/resumen-hoy    -> total y operaciones de HOY, todo el negocio (cualquier sesión)
# GET  /ventas/mas-vendidos-mes -> IDs de productos más vendidos este mes (cualquier sesión)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, requiere_rol
from app.db.session import get_db
from app.usuarios.models import Usuario
from app.ventas import service
from app.ventas.schemas import ResumenVentasHoy, VentaCreate, VentaOut

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("", response_model=VentaOut, status_code=201)
def registrar_venta(
    datos: VentaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return service.registrar_venta(db, datos, usuario)


@router.get("", response_model=list[VentaOut])
def listar_ventas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.listar_ventas(db)


@router.get("/mias", response_model=list[VentaOut])
def mis_ventas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return service.listar_ventas(db, usuario_id=usuario.id)


@router.get("/resumen-hoy", response_model=ResumenVentasHoy)
def resumen_hoy(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return service.resumen_ventas_hoy(db)


@router.get("/mas-vendidos-mes", response_model=list[int])
def mas_vendidos_mes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return service.productos_mas_vendidos_mes(db)
