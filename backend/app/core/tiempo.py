# tiempo.py = matemática de fechas en hora de Lima, compartida por los
# módulos que necesitan saber "qué día es hoy" o "a qué instante UTC
# corresponde la medianoche de tal fecha" para el negocio (no del servidor).
#
# Perú NO usa horario de verano, así que un offset fijo UTC-5 es correcto
# todo el año — evita depender del paquete `tzdata` que hace falta para
# `zoneinfo.ZoneInfo()` en Windows (que no trae base de datos de husos
# horarios del sistema operativo).
#
# Antes vivía duplicado (con nombres privados) dentro de app.kpis.service;
# se extrajo aquí porque ventas y caja necesitan la misma matemática.

from datetime import date, datetime, time, timedelta, timezone

ZONA_LIMA = timezone(timedelta(hours=-5), name="America/Lima")


def hoy_lima() -> date:
    """La fecha de "hoy" en hora local de Lima (no UTC, no la hora del
    servidor)."""
    return datetime.now(timezone.utc).astimezone(ZONA_LIMA).date()


def a_hora_lima(momento: datetime) -> datetime:
    """Convierte un datetime tal como llega de la base de datos (aware en
    PostgreSQL; puede llegar naive en SQLite, que no tiene tipo con huso
    horario — pero en ambos casos el valor guardado ES UTC) a la hora local
    de Lima."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(ZONA_LIMA)


def inicio_utc_de_fecha_lima(fecha_lima: date) -> datetime:
    """Instante UTC exacto en que empieza (medianoche) una fecha de Lima.
    Sirve para filtrar timestamps guardados en UTC con un simple rango de
    fechas/horas, sin depender de funciones de zona horaria del motor de
    base de datos — así el mismo filtro funciona igual en SQLite (pruebas) y
    PostgreSQL (real)."""
    medianoche_lima = datetime.combine(fecha_lima, time.min, tzinfo=ZONA_LIMA)
    return medianoche_lima.astimezone(timezone.utc)
