# Pruebas de los endpoints nuevos de /ventas para el buscador y el resumen
# rápido de /venta (puntos 1 y 2 del pedido): deben ser accesibles para los
# 3 roles (a diferencia de /kpis, que es solo dueño/contador), y calcular
# los mismos números que ya calcula /kpis para el mismo día/mes.

from datetime import datetime, timedelta, timezone

from app.ventas.models import Venta
from tests.conftest import crear_producto_prueba, crear_usuario_prueba, login


def test_resumen_hoy_accesible_para_vendedor(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, precio=10.0, stock=20)
    token = login(client, "vendedor@negocio.com")

    client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 2},
        headers={"Authorization": f"Bearer {token}"},
    )

    respuesta = client.get("/api/ventas/resumen-hoy", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 20.0
    assert cuerpo["operaciones"] == 1


def test_resumen_hoy_coincide_con_kpis_resumen(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    producto = crear_producto_prueba(db_session, precio=7.5, stock=20)

    token_vendedor = login(client, "vendedor@negocio.com")
    client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 3},
        headers={"Authorization": f"Bearer {token_vendedor}"},
    )

    token_dueno = login(client, "duena@negocio.com")
    resumen_ventas = client.get(
        "/api/ventas/resumen-hoy", headers={"Authorization": f"Bearer {token_vendedor}"}
    ).json()
    resumen_kpis = client.get(
        "/api/kpis/resumen", headers={"Authorization": f"Bearer {token_dueno}"}
    ).json()

    assert resumen_ventas["total"] == resumen_kpis["ventas_hoy_total"]
    assert resumen_ventas["operaciones"] == resumen_kpis["ventas_hoy_operaciones"]


def test_mas_vendidos_mes_accesible_para_vendedor_y_ordenado(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    mas_vendido = crear_producto_prueba(db_session, nombre="MasVendido", stock=50, precio=5.0)
    menos_vendido = crear_producto_prueba(db_session, nombre="MenosVendido", stock=50, precio=5.0)
    token = login(client, "vendedor@negocio.com")

    client.post(
        "/api/ventas",
        json={"producto_id": mas_vendido.id, "cantidad": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/ventas",
        json={"producto_id": menos_vendido.id, "cantidad": 1},
        headers={"Authorization": f"Bearer {token}"},
    )

    respuesta = client.get(
        "/api/ventas/mas-vendidos-mes", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.status_code == 200
    ids = respuesta.json()
    assert ids == [mas_vendido.id, menos_vendido.id]


def test_mas_vendidos_mes_ignora_ventas_del_mes_pasado(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, nombre="SoloMesPasado", stock=50, precio=5.0)
    db_session.add(
        Venta(
            producto_id=producto.id,
            usuario_id=vendedor.id,
            cantidad=10,
            precio_unitario=5.0,
            subtotal=50.0,
            fecha_venta=datetime.now(timezone.utc) - timedelta(days=45),
        )
    )
    db_session.commit()

    token = login(client, "vendedor@negocio.com")
    respuesta = client.get(
        "/api/ventas/mas-vendidos-mes", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta.json() == []


def test_mas_vendidos_mes_excluye_productos_inactivos(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    producto = crear_producto_prueba(db_session, nombre="Descontinuado", stock=50, precio=5.0)

    token_vendedor = login(client, "vendedor@negocio.com")
    client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 5},
        headers={"Authorization": f"Bearer {token_vendedor}"},
    )

    token_dueno = login(client, "duena@negocio.com")
    client.patch(
        f"/api/productos/{producto.id}/desactivar", headers={"Authorization": f"Bearer {token_dueno}"}
    )

    respuesta = client.get(
        "/api/ventas/mas-vendidos-mes", headers={"Authorization": f"Bearer {token_vendedor}"}
    )
    assert respuesta.json() == []
