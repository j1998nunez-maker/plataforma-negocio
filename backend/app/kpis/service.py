# service.py = calcula los indicadores (KPIs) para la pantalla simple del
# MVP: ventas de hoy/mes, resumen por producto, jornada por periodos,
# alertas de inventario (vencidos, por vencer, agotados).
#
# Esto es un resumen rápido para la app. El análisis detallado en Power BI
# se hace directo contra las tablas `ventas` y `productos`.
#
# --- Zona horaria ---
# `fecha_venta` se guarda en la base de datos en UTC (server_default con
# func.now()). Pero el negocio piensa en días y horarios de Lima, no de
# UTC. Perú NO usa horario de verano, así que un offset fijo UTC-5 es
# correcto todo el año — evita depender del paquete `tzdata` que hace falta
# para `zoneinfo.ZoneInfo()` en Windows (que no trae base de datos de
# husos horarios del sistema operativo).
#
# Todo el bucketeo por día/periodo se hace en PYTHON (no en SQL) sobre los
# timestamps ya traídos de la base de datos: así el mismo código funciona
# igual en SQLite (pruebas) y PostgreSQL (real), sin funciones de fecha
# específicas de cada motor.

from datetime import date, timedelta
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.tiempo import ZONA_LIMA
from app.core.tiempo import a_hora_lima as _a_hora_lima
from app.core.tiempo import hoy_lima as _hoy
from app.core.tiempo import inicio_utc_de_fecha_lima as _inicio_utc_de_fecha_lima
from app.kpis.schemas import (
    HistoricoProductoItem,
    JornadaHoy,
    ProductoAgotado,
    ProductoTop,
    ProductoVencido,
    PuntoDiario,
    PuntoHistoricoDiario,
    ResumenDiaItem,
    ResumenFueraDeHorario,
    ResumenKPIs,
    ResumenMesItem,
    UnidadesPorProductoPeriodo,
)
from app.productos.models import Producto
from app.ventas.models import Venta

DIAS_ALERTA_VENCIMIENTO = 30
DIAS_ROTACION = 30
DIAS_HISTORICO = 30

# Horario provisional del piloto: 08:00-20:00, en 4 bloques de 3 horas
# (hora local de Lima). Una venta fuera de este rango no se descarta: se
# reporta aparte en `fuera_de_horario`.
PERIODOS_JORNADA = [(8, 11), (11, 14), (14, 17), (17, 20)]


def _rango_resumen(db: Session, desde_lima: date, hasta_lima: date | None = None) -> tuple[int, float, int]:
    """Cantidad, subtotal y número de operaciones (ventas individuales)
    entre `desde_lima` y `hasta_lima` (ambos inclusive, en fechas de Lima).
    `hasta_lima=None` = sin límite superior (hasta ahora mismo)."""
    condiciones = [Venta.fecha_venta >= _inicio_utc_de_fecha_lima(desde_lima)]
    if hasta_lima is not None:
        condiciones.append(Venta.fecha_venta < _inicio_utc_de_fecha_lima(hasta_lima + timedelta(days=1)))

    fila = db.execute(
        select(
            func.coalesce(func.sum(Venta.cantidad), 0),
            func.coalesce(func.sum(Venta.subtotal), 0),
            func.count(Venta.id),
        ).where(*condiciones)
    ).one()
    return int(fila[0]), float(fila[1]), int(fila[2])


def _producto_menor_rotacion(db: Session, desde_lima: date) -> ProductoTop | None:
    """El producto activo con menos unidades vendidas desde `desde_lima`
    (0 si no tuvo ninguna venta en ese periodo). Usa un LEFT JOIN con la
    condición de fecha puesta en el propio JOIN (no en un WHERE) para que
    los productos sin ventas recientes no queden excluidos — si no, un
    producto sin ninguna venta jamás podría aparecer como "el de menor
    rotación", que es justo el caso que más le interesa ver al dueño."""
    desde_utc = _inicio_utc_de_fecha_lima(desde_lima)
    fila = db.execute(
        select(
            Producto.nombre,
            func.coalesce(func.sum(Venta.cantidad), 0).label("unidades"),
            func.coalesce(func.sum(Venta.subtotal), 0).label("total"),
        )
        .select_from(Producto)
        .outerjoin(Venta, and_(Venta.producto_id == Producto.id, Venta.fecha_venta >= desde_utc))
        .where(Producto.activo.is_(True))
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.coalesce(func.sum(Venta.cantidad), 0).asc(), Producto.nombre.asc())
        .limit(1)
    ).first()

    if fila is None:
        return None
    return ProductoTop(nombre=fila.nombre, unidades_vendidas=int(fila.unidades), total_vendido=float(fila.total))


def _productos_ya_vencidos(db: Session, hoy: date) -> list[ProductoVencido]:
    """Productos activos cuya fecha de vencimiento ya pasó — alerta separada
    de "por vencer" (que solo mira los próximos 30 días). Se ignora el stock
    a propósito: incluso con stock 0 el dueño necesita verlo para darlo de
    baja del catálogo. `fecha_vencimiento` es un DATE simple (sin hora), así
    que no le afecta la conversión de huso horario."""
    filas = db.execute(
        select(Producto.id, Producto.nombre, Producto.fecha_vencimiento, Producto.stock_actual)
        .where(
            Producto.activo.is_(True),
            Producto.fecha_vencimiento.is_not(None),
            Producto.fecha_vencimiento < hoy,
        )
        .order_by(Producto.fecha_vencimiento.asc())
    ).all()
    return [
        ProductoVencido(
            producto_id=fila.id,
            nombre=fila.nombre,
            fecha_vencimiento=fila.fecha_vencimiento,
            stock_actual=fila.stock_actual,
        )
        for fila in filas
    ]


def _productos_agotados(db: Session) -> list[ProductoAgotado]:
    """Productos activos con stock 0 — alerta independiente de vencidos y
    por vencer. Un producto vencido Y agotado a la vez aparece en AMBAS
    listas (no se excluye de ninguna): son alertas distintas y el dueño
    necesita ver las dos razones."""
    filas = db.execute(
        select(Producto.id, Producto.nombre, Producto.fecha_vencimiento)
        .where(Producto.activo.is_(True), Producto.stock_actual <= 0)
        .order_by(Producto.nombre)
    ).all()
    return [
        ProductoAgotado(producto_id=fila.id, nombre=fila.nombre, fecha_vencimiento=fila.fecha_vencimiento)
        for fila in filas
    ]


def obtener_resumen(db: Session) -> ResumenKPIs:
    hoy = _hoy()
    inicio_mes = hoy.replace(day=1)

    ventas_hoy_cantidad, ventas_hoy_total, ventas_hoy_operaciones = _rango_resumen(db, hoy, hoy)
    ventas_mes_cantidad, ventas_mes_total, ventas_mes_operaciones = _rango_resumen(db, inicio_mes)

    top_productos = db.execute(
        select(
            Producto.nombre,
            func.sum(Venta.cantidad).label("unidades"),
            func.sum(Venta.subtotal).label("total"),
        )
        .join(Producto, Producto.id == Venta.producto_id)
        .group_by(Producto.nombre)
        .order_by(func.sum(Venta.cantidad).desc())
        .limit(5)
    ).all()

    # Solo cuenta lo que vence ENTRE hoy y los próximos 30 días — lo que ya
    # venció se reporta aparte en `productos_ya_vencidos`, para que las dos
    # alertas no se dupliquen entre sí.
    productos_por_vencer = db.scalar(
        select(func.count(Producto.id)).where(
            Producto.activo.is_(True),
            Producto.fecha_vencimiento.is_not(None),
            Producto.fecha_vencimiento >= hoy,
            Producto.fecha_vencimiento <= hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO),
        )
    )

    producto_menor_rotacion = _producto_menor_rotacion(db, hoy - timedelta(days=DIAS_ROTACION))

    return ResumenKPIs(
        ventas_hoy_cantidad=ventas_hoy_cantidad,
        ventas_hoy_total=ventas_hoy_total,
        ventas_hoy_operaciones=ventas_hoy_operaciones,
        ventas_mes_cantidad=ventas_mes_cantidad,
        ventas_mes_total=ventas_mes_total,
        ventas_mes_operaciones=ventas_mes_operaciones,
        productos_mas_vendidos=[
            ProductoTop(nombre=fila.nombre, unidades_vendidas=int(fila.unidades), total_vendido=float(fila.total))
            for fila in top_productos
        ],
        productos_por_vencer=productos_por_vencer or 0,
        productos_ya_vencidos=_productos_ya_vencidos(db, hoy),
        productos_agotados=_productos_agotados(db),
        producto_menor_rotacion=producto_menor_rotacion,
    )


def resumen_dia(db: Session) -> list[ResumenDiaItem]:
    """Ventas de hoy (día de Lima) agrupadas por producto — para que el
    dueño vea de un vistazo qué se vendió hoy sin desplazarse por un
    historial largo. Incluye número de operaciones, no solo unidades."""
    hoy = _hoy()
    desde_utc = _inicio_utc_de_fecha_lima(hoy)
    hasta_utc = _inicio_utc_de_fecha_lima(hoy + timedelta(days=1))

    filas = db.execute(
        select(
            Producto.id,
            Producto.nombre,
            func.sum(Venta.cantidad).label("cantidad_total"),
            func.sum(Venta.subtotal).label("subtotal_total"),
            func.count(Venta.id).label("operaciones"),
        )
        .join(Producto, Producto.id == Venta.producto_id)
        .where(Venta.fecha_venta >= desde_utc, Venta.fecha_venta < hasta_utc)
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(Venta.subtotal).desc())
    ).all()
    return [
        ResumenDiaItem(
            producto_id=fila.id,
            nombre=fila.nombre,
            cantidad_total=int(fila.cantidad_total),
            subtotal_total=float(fila.subtotal_total),
            operaciones=int(fila.operaciones),
        )
        for fila in filas
    ]


def resumen_mes(db: Session) -> list[ResumenMesItem]:
    """Unidades, soles y operaciones del mes actual (mes de Lima), agrupado
    por producto (un producto = una fila) — se acumula solo con que haya
    ventas nuevas, no guarda nada aparte."""
    hoy = _hoy()
    inicio_mes = hoy.replace(day=1)
    desde_utc = _inicio_utc_de_fecha_lima(inicio_mes)

    filas = db.execute(
        select(
            Producto.id,
            Producto.nombre,
            func.sum(Venta.cantidad).label("unidades"),
            func.sum(Venta.subtotal).label("total"),
            func.count(Venta.id).label("operaciones"),
        )
        .join(Producto, Producto.id == Venta.producto_id)
        .where(Venta.fecha_venta >= desde_utc)
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(Venta.subtotal).desc())
    ).all()
    return [
        ResumenMesItem(
            producto_id=fila.id,
            nombre=fila.nombre,
            unidades_vendidas=int(fila.unidades),
            total_vendido=float(fila.total),
            operaciones=int(fila.operaciones),
        )
        for fila in filas
    ]


def historico_diario(db: Session) -> list[PuntoHistoricoDiario]:
    """Total vendido (soles) por día de Lima en los últimos `DIAS_HISTORICO`
    días, incluyendo los días sin ninguna venta (0), para que el gráfico no
    salte fechas. El bucketeo por día se hace en Python (no SQL) para que
    el mismo código sea correcto en SQLite y PostgreSQL."""
    hoy = _hoy()
    desde = hoy - timedelta(days=DIAS_HISTORICO - 1)
    desde_utc = _inicio_utc_de_fecha_lima(desde)

    filas = db.execute(
        select(Venta.fecha_venta, Venta.subtotal).where(Venta.fecha_venta >= desde_utc)
    ).all()

    totales_por_fecha: dict[date, float] = {}
    for fila in filas:
        fecha_lima = _a_hora_lima(fila.fecha_venta).date()
        totales_por_fecha[fecha_lima] = totales_por_fecha.get(fecha_lima, 0.0) + float(fila.subtotal)

    return [
        PuntoHistoricoDiario(
            fecha=desde + timedelta(days=i),
            total=totales_por_fecha.get(desde + timedelta(days=i), 0.0),
        )
        for i in range(DIAS_HISTORICO)
    ]


def historico_productos_diario(db: Session) -> list[HistoricoProductoItem]:
    """Igual que `historico_diario`, pero desglosado por producto y en
    UNIDADES (no soles), por día de Lima — para comparar tendencias de venta
    entre productos en el gráfico de línea de /kpis.

    Incluye productos activos Y los que se desactivaron pero tuvieron
    ventas dentro de la ventana de 30 días: si no fuera así, desactivar un
    producto borraría de golpe su línea del gráfico aunque haya vendido
    ayer mismo — justo lo que NO debe pasar al desactivar (ver
    `app.productos.service.desactivar_producto`)."""
    hoy = _hoy()
    desde = hoy - timedelta(days=DIAS_HISTORICO - 1)
    desde_utc = _inicio_utc_de_fecha_lima(desde)

    filas = db.execute(
        select(Venta.producto_id, Venta.fecha_venta, Venta.cantidad).where(Venta.fecha_venta >= desde_utc)
    ).all()

    ids_con_ventas_recientes = {fila.producto_id for fila in filas}

    productos_relevantes = db.execute(
        select(Producto.id, Producto.nombre)
        .where(or_(Producto.activo.is_(True), Producto.id.in_(ids_con_ventas_recientes)))
        .order_by(Producto.nombre)
    ).all()

    cantidades_por_producto_fecha: dict[tuple[int, date], int] = {}
    for fila in filas:
        fecha_lima = _a_hora_lima(fila.fecha_venta).date()
        clave = (fila.producto_id, fecha_lima)
        cantidades_por_producto_fecha[clave] = cantidades_por_producto_fecha.get(clave, 0) + fila.cantidad

    return [
        HistoricoProductoItem(
            producto_id=producto.id,
            nombre=producto.nombre,
            puntos=[
                PuntoDiario(
                    fecha=desde + timedelta(days=i),
                    cantidad=cantidades_por_producto_fecha.get((producto.id, desde + timedelta(days=i)), 0),
                )
                for i in range(DIAS_HISTORICO)
            ],
        )
        for producto in productos_relevantes
    ]


def jornada_hoy(db: Session) -> JornadaHoy:
    """Ingresos y operaciones por periodo de 3 horas (hora local de Lima),
    más unidades por producto y periodo, SOLO para el día de hoy — para el
    gráfico de "jornada actual" en /kpis. Las ventas fuera de 08:00-20:00
    no se descartan: se acumulan aparte en `fuera_de_horario`, tal como se
    pidió (horario provisional del piloto)."""
    hoy = _hoy()
    desde_utc = _inicio_utc_de_fecha_lima(hoy)
    hasta_utc = _inicio_utc_de_fecha_lima(hoy + timedelta(days=1))

    ventas_hoy = db.execute(
        select(Venta.producto_id, Venta.fecha_venta, Venta.cantidad, Venta.subtotal).where(
            Venta.fecha_venta >= desde_utc, Venta.fecha_venta < hasta_utc
        )
    ).all()

    # Activos, MÁS cualquiera que ya se haya desactivado pero vendió hoy —
    # mismo criterio que `historico_productos_diario`, para que desactivar
    # un producto a media jornada no le borre del gráfico las ventas que ya
    # hizo hoy.
    ids_con_ventas_hoy = {venta.producto_id for venta in ventas_hoy}
    productos_relevantes = db.execute(
        select(Producto.id, Producto.nombre)
        .where(or_(Producto.activo.is_(True), Producto.id.in_(ids_con_ventas_hoy)))
        .order_by(Producto.nombre)
    ).all()

    num_periodos = len(PERIODOS_JORNADA)
    ingresos_por_periodo = [0.0] * num_periodos
    operaciones_por_periodo = [0] * num_periodos
    unidades: dict[tuple[int, int], int] = {}
    fuera_cantidad = 0
    fuera_subtotal = 0.0
    fuera_operaciones = 0

    for venta in ventas_hoy:
        hora_local = _a_hora_lima(venta.fecha_venta).hour
        indice_periodo = next(
            (i for i, (inicio, fin) in enumerate(PERIODOS_JORNADA) if inicio <= hora_local < fin),
            None,
        )
        if indice_periodo is None:
            fuera_cantidad += venta.cantidad
            fuera_subtotal += float(venta.subtotal)
            fuera_operaciones += 1
            continue

        ingresos_por_periodo[indice_periodo] += float(venta.subtotal)
        operaciones_por_periodo[indice_periodo] += 1
        clave = (venta.producto_id, indice_periodo)
        unidades[clave] = unidades.get(clave, 0) + venta.cantidad

    etiquetas = [f"{inicio:02d}:00–{fin:02d}:00" for inicio, fin in PERIODOS_JORNADA]

    return JornadaHoy(
        fecha=hoy,
        periodos=etiquetas,
        ingresos_por_periodo=ingresos_por_periodo,
        operaciones_por_periodo=operaciones_por_periodo,
        unidades_por_producto=[
            UnidadesPorProductoPeriodo(
                producto_id=producto.id,
                nombre=producto.nombre,
                unidades_por_periodo=[unidades.get((producto.id, i), 0) for i in range(num_periodos)],
            )
            for producto in productos_relevantes
        ],
        fuera_de_horario=ResumenFueraDeHorario(
            cantidad=fuera_cantidad, subtotal=fuera_subtotal, operaciones=fuera_operaciones
        ),
    )


def exportar_ventas_dia(db: Session, fecha_lima: date) -> bytes:
    """Arma un archivo .xlsx con el historial COMPLETO de ventas de un día
    (hora de Lima) elegido por el dueño — venta por venta, no agrupado.
    Se genera al vuelo en memoria, no se guarda nada en el servidor y no
    toca ningún otro dato."""
    desde_utc = _inicio_utc_de_fecha_lima(fecha_lima)
    hasta_utc = _inicio_utc_de_fecha_lima(fecha_lima + timedelta(days=1))

    filas = db.execute(
        select(Venta.fecha_venta, Producto.nombre, Venta.cantidad, Venta.subtotal)
        .join(Producto, Producto.id == Venta.producto_id)
        .where(Venta.fecha_venta >= desde_utc, Venta.fecha_venta < hasta_utc)
        .order_by(Venta.fecha_venta.asc())
    ).all()

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Ventas"
    hoja.append(["Fecha", "Hora", "Producto", "Cantidad", "Subtotal (S/)"])
    anchos = (12, 10, 32, 10, 14)
    for columna, ancho in zip("ABCDE", anchos):
        hoja.column_dimensions[columna].width = ancho

    for fila in filas:
        momento_lima = _a_hora_lima(fila.fecha_venta)
        hoja.append(
            [
                momento_lima.strftime("%Y-%m-%d"),
                momento_lima.strftime("%H:%M:%S"),
                fila.nombre,
                fila.cantidad,
                float(fila.subtotal),
            ]
        )

    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue()
