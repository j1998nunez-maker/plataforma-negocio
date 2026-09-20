# Pruebas del flujo principal del MVP: login con roles, registrar una
# venta con un clic, permisos por rol, y el cálculo de KPIs.

from tests.conftest import crear_producto_prueba, crear_usuario_prueba, login


def test_login_correcto_devuelve_token(client, db_session):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    respuesta = client.post(
        "/api/auth/login", data={"username": "duena@negocio.com", "password": "clave123"}
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "dueno"
    assert cuerpo["access_token"]


def test_login_con_contrasena_incorrecta_falla(client, db_session):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    respuesta = client.post(
        "/api/auth/login", data={"username": "duena@negocio.com", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401


def test_vendedor_no_puede_crear_producto(client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    respuesta = client.post(
        "/api/productos",
        json={"nombre": "Ibuprofeno", "precio_venta": 8.0, "stock_actual": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 403


def test_dueno_puede_crear_producto(client, db_session):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    token = login(client, "duena@negocio.com")

    respuesta = client.post(
        "/api/productos",
        json={"nombre": "Ibuprofeno", "precio_venta": 8.0, "stock_actual": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Ibuprofeno"


def test_registrar_venta_descuenta_stock_y_copia_precio(client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, nombre="Paracetamol", stock=10, precio=5.5)
    token = login(client, "vendedor@negocio.com")

    respuesta = client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    venta = respuesta.json()
    assert venta["cantidad"] == 3
    assert venta["precio_unitario"] == 5.5
    assert venta["subtotal"] == 16.5

    # el stock del catálogo debe haber bajado de 10 a 7
    productos = client.get(
        "/api/productos", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert productos[0]["stock_actual"] == 7


def test_no_se_puede_vender_mas_stock_del_disponible(client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, stock=2)
    token = login(client, "vendedor@negocio.com")

    respuesta = client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 400


def test_vendedor_no_puede_ver_historial_completo_de_ventas(client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    respuesta = client.get("/api/ventas", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 403

    respuesta_propias = client.get(
        "/api/ventas/mias", headers={"Authorization": f"Bearer {token}"}
    )
    assert respuesta_propias.status_code == 200


def test_kpis_resumen_refleja_las_ventas_del_dia(client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    producto = crear_producto_prueba(db_session, precio=10.0, stock=20)

    token_vendedor = login(client, "vendedor@negocio.com")
    client.post(
        "/api/ventas",
        json={"producto_id": producto.id, "cantidad": 2},
        headers={"Authorization": f"Bearer {token_vendedor}"},
    )

    token_dueno = login(client, "duena@negocio.com")
    respuesta = client.get(
        "/api/kpis/resumen", headers={"Authorization": f"Bearer {token_dueno}"}
    )
    assert respuesta.status_code == 200
    kpis = respuesta.json()
    assert kpis["ventas_hoy_cantidad"] == 2
    assert kpis["ventas_hoy_total"] == 20.0
    assert kpis["productos_mas_vendidos"][0]["nombre"] == producto.nombre


def test_no_se_puede_repetir_correo_de_usuario(client, db_session):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    token = login(client, "duena@negocio.com")

    respuesta = client.post(
        "/api/usuarios",
        json={
            "nombre_completo": "Otra Persona",
            "correo": "duena@negocio.com",
            "contrasena": "clave123",
            "rol": "vendedor",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 409
