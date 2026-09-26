# service.py = lógica de negocio del cierre de caja diario: una sola caja
# para todo el negocio por día. Cualquiera de los roles que vende (dueño,
# contador, vendedor) puede registrar retiros y cerrar; una vez cerrado el
# día, no se pueden agregar más retiros ni cerrar de nuevo (409).

import logging
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.caja.models import ESTADO_PENDIENTE_REVISION, ESTADO_REVISADO, CierreCaja, RetiroCaja
from app.caja.schemas import CierreCreate, CierreOut, EstadoCajaHoy, RetiroCreate, RetiroOut
from app.core.tiempo import hoy_lima
from app.usuarios.models import Usuario
from app.ventas.service import resumen_ventas_fecha

logger = logging.getLogger(__name__)


def _a_retiro_out(retiro: RetiroCaja) -> RetiroOut:
    return RetiroOut(
        id=retiro.id,
        fecha=retiro.fecha,
        monto=float(retiro.monto),
        motivo=retiro.motivo,
        usuario_id=retiro.usuario_id,
        nombre_usuario=retiro.usuario.nombre_completo,
        fecha_creacion=retiro.fecha_creacion,
    )


def _a_cierre_out(cierre: CierreCaja) -> CierreOut:
    return CierreOut(
        id=cierre.id,
        fecha=cierre.fecha,
        efectivo_esperado=float(cierre.efectivo_esperado),
        efectivo_contado=float(cierre.efectivo_contado),
        diferencia=float(cierre.diferencia),
        usuario_id=cierre.usuario_id,
        nombre_usuario=cierre.usuario.nombre_completo,
        estado=cierre.estado,
        revisado_por_id=cierre.revisado_por_id,
        nombre_revisor=cierre.revisado_por.nombre_completo if cierre.revisado_por else None,
        fecha_revision=cierre.fecha_revision,
        fecha_creacion=cierre.fecha_creacion,
    )


def _cierre_de_fecha(db: Session, fecha: date) -> CierreCaja | None:
    return db.scalar(select(CierreCaja).where(CierreCaja.fecha == fecha))


def _retiros_de_fecha(db: Session, fecha: date) -> list[RetiroCaja]:
    return list(
        db.scalars(
            select(RetiroCaja).where(RetiroCaja.fecha == fecha).order_by(RetiroCaja.fecha_creacion)
        )
    )


def estado_hoy(db: Session) -> EstadoCajaHoy:
    hoy = hoy_lima()
    retiros = _retiros_de_fecha(db, hoy)
    cierre = _cierre_de_fecha(db, hoy)

    total_ventas_efectivo, _ = resumen_ventas_fecha(db, hoy)
    total_retiros = sum(float(r.monto) for r in retiros)

    return EstadoCajaHoy(
        fecha=hoy,
        cerrado=cierre is not None,
        efectivo_esperado_hasta_ahora=total_ventas_efectivo - total_retiros,
        retiros=[_a_retiro_out(r) for r in retiros],
        cierre=_a_cierre_out(cierre) if cierre else None,
    )


def _verificar_caja_abierta(db: Session, fecha: date) -> None:
    if _cierre_de_fecha(db, fecha) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La caja de hoy ya está cerrada. No se pueden registrar más retiros.",
        )


def registrar_retiro(db: Session, datos: RetiroCreate, usuario: Usuario) -> RetiroOut:
    hoy = hoy_lima()
    _verificar_caja_abierta(db, hoy)

    retiro = RetiroCaja(fecha=hoy, monto=datos.monto, motivo=datos.motivo, usuario_id=usuario.id)
    db.add(retiro)
    db.commit()
    db.refresh(retiro)
    return _a_retiro_out(retiro)


def cerrar_caja(db: Session, datos: CierreCreate, usuario: Usuario) -> CierreOut:
    hoy = hoy_lima()
    if _cierre_de_fecha(db, hoy) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="La caja de hoy ya se cerró."
        )

    total_ventas_efectivo, _ = resumen_ventas_fecha(db, hoy)
    total_retiros = sum(float(r.monto) for r in _retiros_de_fecha(db, hoy))
    efectivo_esperado = total_ventas_efectivo - total_retiros

    cierre = CierreCaja(
        fecha=hoy,
        efectivo_esperado=efectivo_esperado,
        efectivo_contado=datos.efectivo_contado,
        diferencia=datos.efectivo_contado - efectivo_esperado,
        usuario_id=usuario.id,
        estado=ESTADO_PENDIENTE_REVISION,
    )
    db.add(cierre)
    db.commit()
    db.refresh(cierre)

    _notificar_cierre(db, cierre)
    return _a_cierre_out(cierre)


def _notificar_cierre(db: Session, cierre: CierreCaja) -> None:
    """Envía el reporte del día por correo a todos los dueños activos. El
    cierre ya está guardado en este punto — si el correo falla (SMTP no
    configurado, sin red, etc.) se loguea pero NO se revierte el cierre: el
    cierre es la fuente de verdad, el correo es solo una notificación."""
    from app.caja.reporte_pdf import generar_reporte_pdf, nombre_archivo_pdf
    from app.caja.reportes import generar_reporte_html
    from app.core.email import enviar_correo

    duenos = db.scalars(select(Usuario).where(Usuario.rol == "dueno", Usuario.activo.is_(True))).all()
    if not duenos:
        logger.warning("Cierre de caja %s: no hay ningún dueño activo a quien avisar.", cierre.fecha)
        return

    try:
        cuerpo_html = generar_reporte_html(db, cierre)
    except Exception:
        logger.exception("No se pudo generar el reporte HTML del cierre %s.", cierre.fecha)
        return

    # El PDF es un extra: si falla, el correo sale igual, solo sin adjunto.
    adjuntos = []
    try:
        adjuntos.append(
            (nombre_archivo_pdf(cierre), generar_reporte_pdf(db, cierre), "application/pdf")
        )
    except Exception:
        logger.exception("No se pudo generar el PDF del cierre %s; se envía sin adjunto.", cierre.fecha)

    asunto = f"Cierre de caja {cierre.fecha.isoformat()} - Plataforma Negocio"
    for dueno in duenos:
        try:
            enviar_correo(dueno.correo, asunto, cuerpo_html, adjuntos=adjuntos)
        except Exception:
            logger.exception("No se pudo enviar el correo de cierre de caja a %s.", dueno.correo)


def listar_cierres(db: Session, limite: int = 60) -> list[CierreOut]:
    cierres = db.scalars(select(CierreCaja).order_by(CierreCaja.fecha.desc()).limit(limite)).all()
    return [_a_cierre_out(c) for c in cierres]


def marcar_revisado(db: Session, cierre_id: int, dueno: Usuario) -> CierreOut:
    from datetime import datetime, timezone

    cierre = db.get(CierreCaja, cierre_id)
    if cierre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cierre no encontrado.")
    if cierre.estado == ESTADO_REVISADO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este cierre ya fue revisado."
        )

    cierre.estado = ESTADO_REVISADO
    cierre.revisado_por_id = dueno.id
    cierre.fecha_revision = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cierre)
    return _a_cierre_out(cierre)
