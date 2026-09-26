# router.py = endpoints del cierre de caja diario.
#
# GET   /caja/hoy               -> estado de hoy (cerrada o no, retiros, efectivo esperado hasta ahora)
# POST  /caja/retiros           -> registrar un retiro de efectivo de hoy
# POST  /caja/cerrar            -> cerrar la caja de hoy (dispara el correo al dueño)
# GET   /caja/cierres           -> historial de cierres (solo dueño y contador)
# PATCH /caja/cierres/{id}/revisar -> marcar un cierre como revisado (SOLO dueño)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.caja import service
from app.caja.schemas import CierreCreate, CierreOut, EstadoCajaHoy, RetiroCreate, RetiroOut
from app.core.security import get_current_user, requiere_rol
from app.db.session import get_db
from app.usuarios.models import Usuario

router = APIRouter(prefix="/caja", tags=["caja"])


@router.get("/hoy", response_model=EstadoCajaHoy)
def estado_hoy(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return service.estado_hoy(db)


@router.post("/retiros", response_model=RetiroOut, status_code=201)
def registrar_retiro(
    datos: RetiroCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return service.registrar_retiro(db, datos, usuario)


@router.post("/cerrar", response_model=CierreOut, status_code=201)
def cerrar_caja(
    datos: CierreCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return service.cerrar_caja(db, datos, usuario)


@router.get("/cierres", response_model=list[CierreOut])
def listar_cierres(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.listar_cierres(db)


@router.patch("/cierres/{cierre_id}/revisar", response_model=CierreOut)
def marcar_revisado(
    cierre_id: int,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(requiere_rol("dueno")),
):
    return service.marcar_revisado(db, cierre_id, dueno)
