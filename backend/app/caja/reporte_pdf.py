# reporte_pdf.py = arma un PDF corto del cierre de caja, pensado para que lo
# lea el dueño sin conocimientos de sistemas: fecha, cuánto se vendió, lo
# que más se vendió, el dinero que se sacó de la caja y si la caja cuadró.
# Se adjunta al mismo correo que ya envía el cierre (ver service.py).
#
# Usa las fuentes base del PDF (Helvetica), que solo aceptan caracteres
# latinos (tildes y ñ sí); cualquier otro símbolo (ej. emojis en el nombre
# de un producto) se reemplaza por "?" para que el PDF nunca falle.

from datetime import date

from fpdf import FPDF
from sqlalchemy.orm import Session

from app.caja.models import CierreCaja
from app.caja.service import _retiros_de_fecha
from app.ventas.service import productos_vendidos_fecha, resumen_ventas_fecha

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_MAX_PRODUCTOS = 5


def _texto(valor: str) -> str:
    return valor.encode("latin-1", "replace").decode("latin-1")


def _soles(monto: float) -> str:
    return f"S/ {monto:,.2f}"


def fecha_en_palabras(fecha: date) -> str:
    """Ej.: date(2026, 9, 25) -> "Viernes 25 de septiembre de 2026"."""
    dia = _DIAS[fecha.weekday()].capitalize()
    return f"{dia} {fecha.day} de {_MESES[fecha.month - 1]} de {fecha.year}"


def frase_cuadre(diferencia: float) -> str:
    """diferencia = efectivo contado - efectivo esperado."""
    diferencia = round(diferencia, 2)
    if diferencia == 0:
        return "La caja cuadró correctamente."
    if diferencia < 0:
        return f"Falta {_soles(-diferencia)} por verificar."
    return f"Sobra {_soles(diferencia)} por verificar."


def nombre_archivo_pdf(cierre: CierreCaja) -> str:
    return f"cierre-de-caja-{cierre.fecha.isoformat()}.pdf"


def generar_reporte_pdf(db: Session, cierre: CierreCaja) -> bytes:
    total_vendido, cantidad_ventas = resumen_ventas_fecha(db, cierre.fecha)
    productos = sorted(
        productos_vendidos_fecha(db, cierre.fecha),
        key=lambda p: (p.cantidad, p.subtotal),
        reverse=True,
    )[:_MAX_PRODUCTOS]
    retiros = _retiros_de_fecha(db, cierre.fecha)

    pdf = FPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    def titulo_seccion(texto: str) -> None:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 8, _texto(texto), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)

    def parrafo(texto: str) -> None:
        pdf.multi_cell(0, 7, _texto(texto), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Resumen del día", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, _texto(fecha_en_palabras(cierre.fecha)), new_x="LMARGIN", new_y="NEXT")

    titulo_seccion("Ventas")
    if cantidad_ventas:
        palabra = "venta" if cantidad_ventas == 1 else "ventas"
        parrafo(f"Hoy se vendió {_soles(total_vendido)} en total, en {cantidad_ventas} {palabra}.")
    else:
        parrafo("Hoy no se registraron ventas.")

    titulo_seccion("Lo que más se vendió")
    if productos:
        for posicion, producto in enumerate(productos, start=1):
            unidades = "unidad" if producto.cantidad == 1 else "unidades"
            parrafo(f"{posicion}. {producto.nombre}: {producto.cantidad} {unidades}")
    else:
        parrafo("No hubo productos vendidos.")

    titulo_seccion("Dinero que se sacó de la caja")
    if retiros:
        for retiro in retiros:
            parrafo(f"- {_soles(float(retiro.monto))} para: {retiro.motivo}")
        total_retiros = sum(float(r.monto) for r in retiros)
        parrafo(f"Total sacado: {_soles(total_retiros)}")
    else:
        parrafo("Hoy no se sacó dinero de la caja.")

    titulo_seccion("¿Cuadró la caja?")
    pdf.set_font("Helvetica", "B", 13)
    parrafo(frase_cuadre(float(cierre.diferencia)))
    pdf.set_font("Helvetica", "", 12)
    parrafo(
        f"Debía haber {_soles(float(cierre.efectivo_esperado))} en la caja "
        f"y se contó {_soles(float(cierre.efectivo_contado))}."
    )

    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    parrafo(f"Caja cerrada por: {cierre.usuario.nombre_completo}")

    return bytes(pdf.output())
