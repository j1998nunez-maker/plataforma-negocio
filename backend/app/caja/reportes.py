# reportes.py = arma el HTML del reporte diario que se envía por correo al
# cerrar la caja: total vendido, productos vendidos, retiros con motivos, y
# el resultado del cuadre de caja (punto 5 del pedido).

from sqlalchemy.orm import Session

from app.caja.models import CierreCaja
from app.caja.service import _retiros_de_fecha
from app.ventas.service import productos_vendidos_fecha, resumen_ventas_fecha


def generar_reporte_html(db: Session, cierre: CierreCaja) -> str:
    total_vendido, operaciones = resumen_ventas_fecha(db, cierre.fecha)
    productos = productos_vendidos_fecha(db, cierre.fecha)
    retiros = _retiros_de_fecha(db, cierre.fecha)

    filas_productos = "".join(
        f"<tr><td>{p.nombre}</td><td>{p.cantidad}</td><td>S/ {p.subtotal:.2f}</td></tr>"
        for p in productos
    ) or "<tr><td colspan='3'>Sin ventas registradas.</td></tr>"

    filas_retiros = "".join(
        f"<tr><td>{r.motivo}</td><td>S/ {float(r.monto):.2f}</td><td>{r.usuario.nombre_completo}</td></tr>"
        for r in retiros
    ) or "<tr><td colspan='3'>Sin retiros registrados.</td></tr>"

    resultado_cuadre = (
        "Cuadra ✅" if float(cierre.diferencia) == 0 else f"Diferencia ⚠️ S/ {float(cierre.diferencia):.2f}"
    )

    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2430;">
        <h2>Cierre de caja — {cierre.fecha.isoformat()}</h2>
        <p><strong>Total vendido:</strong> S/ {total_vendido:.2f} ({operaciones} operaciones)</p>

        <h3>Productos vendidos</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
          <tr><th>Producto</th><th>Cantidad</th><th>Subtotal</th></tr>
          {filas_productos}
        </table>

        <h3>Retiros de caja</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
          <tr><th>Motivo</th><th>Monto</th><th>Registrado por</th></tr>
          {filas_retiros}
        </table>

        <h3>Cuadre de caja</h3>
        <p>
          Efectivo esperado: S/ {float(cierre.efectivo_esperado):.2f}<br />
          Efectivo contado: S/ {float(cierre.efectivo_contado):.2f}<br />
          <strong>{resultado_cuadre}</strong>
        </p>

        <p>Cerrado por: {cierre.usuario.nombre_completo}</p>
        <p><a href="/caja">Ver y revisar en la plataforma</a></p>
      </body>
    </html>
    """
