# router.py = endpoint del resumen de indicadores (dueño y contador).
# GET /kpis/resumen

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import requiere_rol
from app.db.session import get_db
from app.kpis import service
from app.kpis.schemas import ResumenKPIs
from app.usuarios.models import Usuario

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/resumen", response_model=ResumenKPIs)
def resumen_kpis(
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_rol("dueno", "contador")),
):
    return service.obtener_resumen(db)
