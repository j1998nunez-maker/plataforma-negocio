# router.py = endpoints del resumen de indicadores (dueño y contador).
# GET /kpis/resumen                     -> tarjetas de resumen (hoy, mes, alertas)
# GET /kpis/resumen-dia                 -> ventas de hoy agrupadas por producto
# GET /kpis/resumen-mes                 -> ventas del mes agrupadas por producto
# GET /kpis/historico-diario            -> total vendido (soles) por día, últimos 30 días
# GET /kpis/historico-productos-diario  -> unidades vendidas por día y por producto, últimos 30 días
# GET /kpis/jornada-hoy                 -> ingresos/operaciones por periodo de 3h y unidades por producto, solo hoy
# GET /kpis/exportar-dia?fecha=...      -> descarga .xlsx con el historial completo de ventas de esa fecha

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import requiere_rol
from app.db.session import get_db
from app.kpis import service
from app.kpis.schemas import (
    HistoricoProductoItem,
    JornadaHoy,
    PuntoHistoricoDiario,
    ResumenDiaItem,
    ResumenKPIs,
    ResumenMesItem,
)
from app.usuarios.models import Usuario

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/resumen", response_model=ResumenKPIs)
def resumen_kpis(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.obtener_resumen(db)


@router.get("/resumen-dia", response_model=list[ResumenDiaItem])
def resumen_dia(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.resumen_dia(db)


@router.get("/resumen-mes", response_model=list[ResumenMesItem])
def resumen_mes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.resumen_mes(db)


@router.get("/historico-diario", response_model=list[PuntoHistoricoDiario])
def historico_diario(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.historico_diario(db)


@router.get("/historico-productos-diario", response_model=list[HistoricoProductoItem])
def historico_productos_diario(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.historico_productos_diario(db)


@router.get("/jornada-hoy", response_model=JornadaHoy)
def jornada_hoy(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.jornada_hoy(db)


@router.get("/exportar-dia")
def exportar_dia(
    fecha: date = Query(..., description="Fecha (hora de Lima) a exportar, formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    contenido = service.exportar_ventas_dia(db, fecha)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="ventas_{fecha.isoformat()}.xlsx"'},
    )
