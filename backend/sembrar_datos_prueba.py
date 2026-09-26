# sembrar_datos_prueba.py = un script APARTE del arranque normal de la
# app. No se ejecuta solo ni se llama desde main.py — lo corres tú a mano,
# solo cuando quieras tener productos y ventas de ejemplo para probar la
# plataforma (por ejemplo, para ver cómo se ve el catálogo lleno, o cómo
# se ven los KPIs con varias ventas).
#
# Para que nunca se confunda con datos reales del negocio, todo lo que crea
# este script queda marcado con el prefijo "DEMO - " en el nombre del
# producto. Así:
#   - Se distingue a simple vista en el catálogo.
#   - Se puede borrar SOLO lo de prueba (sin tocar productos/ventas reales)
#     corriendo este mismo script con --limpiar.
#
# Cómo usarlo (desde backend/, con el entorno virtual activado):
#   python sembrar_datos_prueba.py             -> siembra datos de ejemplo
#   python sembrar_datos_prueba.py --limpiar   -> borra SOLO lo sembrado (DEMO - ...)

import argparse
import random
from datetime import date, datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.productos.models import Producto
from app.usuarios.models import Usuario
from app.ventas.models import Venta

PREFIJO_DEMO = "DEMO - "

PRODUCTOS_DEMO = [
    {"nombre": "Paracetamol 500mg", "categoria": "medicamento", "precio_venta": 5.50, "stock_actual": 40, "dias_vencimiento": 200},
    {"nombre": "Ibuprofeno 400mg", "categoria": "medicamento", "precio_venta": 7.90, "stock_actual": 25, "dias_vencimiento": 15},
    {"nombre": "Alcohol en gel 250ml", "categoria": "higiene", "precio_venta": 9.00, "stock_actual": 60, "dias_vencimiento": None},
    {"nombre": "Vitamina C efervescente", "categoria": "suplemento", "precio_venta": 12.50, "stock_actual": 30, "dias_vencimiento": 400},
    {"nombre": "Antiparasitario para perro", "categoria": "veterinaria", "precio_venta": 22.00, "stock_actual": 12, "dias_vencimiento": 25},
    {"nombre": "Lentes de sol UV400", "categoria": "óptica", "precio_venta": 45.00, "stock_actual": 8, "dias_vencimiento": None},
]


def _fecha_vencimiento(dias: int | None) -> date | None:
    if dias is None:
        return None
    return date.today() + timedelta(days=dias)


def sembrar() -> None:
    db = SessionLocal()
    try:
        usuario = db.query(Usuario).filter(Usuario.activo.is_(True)).first()
        if usuario is None:
            print(
                "No hay ningún usuario en la base de datos todavía. "
                "Corre primero: python crear_dueno_inicial.py"
            )
            return

        productos = []
        for datos in PRODUCTOS_DEMO:
            producto = Producto(
                nombre=PREFIJO_DEMO + datos["nombre"],
                categoria=datos["categoria"],
                precio_venta=datos["precio_venta"],
                stock_actual=datos["stock_actual"],
                fecha_vencimiento=_fecha_vencimiento(datos["dias_vencimiento"]),
            )
            db.add(producto)
            productos.append(producto)
        db.flush()  # asigna los IDs sin cerrar la transacción todavía

        ahora = datetime.now(timezone.utc)
        # Ventas repartidas en los últimos 20 días, para que "ventas de hoy",
        # "ventas del mes" y "productos más vendidos" tengan datos con los
        # que probar de verdad.
        for dias_atras in range(20):
            fecha = ahora - timedelta(days=dias_atras)
            cantidad_ventas_ese_dia = random.randint(0, 3)
            for _ in range(cantidad_ventas_ese_dia):
                producto = random.choice(productos)
                cantidad = random.randint(1, 3)
                venta = Venta(
                    producto_id=producto.id,
                    usuario_id=usuario.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio_venta,
                    subtotal=float(producto.precio_venta) * cantidad,
                    fecha_venta=fecha,
                )
                db.add(venta)

        db.commit()
        print(f"Listo: {len(productos)} productos de prueba y varias ventas de ejemplo sembradas.")
        print('Todos los productos de prueba empiezan con "DEMO - " en el nombre.')
        print("Para borrarlos después: python sembrar_datos_prueba.py --limpiar")
    finally:
        db.close()


def limpiar() -> None:
    db = SessionLocal()
    try:
        productos_demo = db.query(Producto).filter(Producto.nombre.like(f"{PREFIJO_DEMO}%")).all()
        ids_productos_demo = [p.id for p in productos_demo]

        if not ids_productos_demo:
            print("No hay datos de prueba (DEMO -) para borrar.")
            return

        ventas_borradas = (
            db.query(Venta)
            .filter(Venta.producto_id.in_(ids_productos_demo))
            .delete(synchronize_session=False)
        )
        for producto in productos_demo:
            db.delete(producto)
        db.commit()
        print(f"Borrados {len(productos_demo)} productos de prueba y {ventas_borradas} ventas asociadas.")
        print("Los productos y ventas reales (sin el prefijo DEMO -) no se tocaron.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Siembra o limpia datos de prueba (marcados como 'DEMO - ').")
    parser.add_argument("--limpiar", action="store_true", help="Borra solo los datos de prueba sembrados antes.")
    args = parser.parse_args()

    if args.limpiar:
        limpiar()
    else:
        respuesta = input(
            "Esto va a crear productos y ventas de EJEMPLO (marcados 'DEMO - ') en tu base de datos actual.\n"
            "¿Continuar? (escribe 'si' para confirmar): "
        ).strip().lower()
        if respuesta == "si":
            sembrar()
        else:
            print("Cancelado. No se creó nada.")
