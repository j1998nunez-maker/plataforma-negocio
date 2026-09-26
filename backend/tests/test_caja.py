# Pruebas del cierre de caja diario (punto 4) y el reporte + aprobación del
# jefe (punto 5): una sola caja para todo el negocio por día, retiros
# bloqueados tras el cierre, cálculo de efectivo esperado/diferencia, y que
# solo el dueño puede marcar un cierre como revisado.

from unittest.mock import patch

from app.caja.models import ESTADO_PENDIENTE_REVISION, ESTADO_REVISADO
from tests.conftest import crear_producto_prueba, crear_usuario_prueba, login


def _vender(client, token, producto_id, cantidad):
    respuesta = client.post(
        "/api/ventas",
        json={"producto_id": producto_id, "cantidad": cantidad},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201, respuesta.text


@patch("app.core.email.enviar_correo")
def test_estado_hoy_antes_de_cualquier_movimiento(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    respuesta = client.get("/api/caja/hoy", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["cerrado"] is False
    assert cuerpo["efectivo_esperado_hasta_ahora"] == 0.0
    assert cuerpo["retiros"] == []
    assert cuerpo["cierre"] is None


@patch("app.core.email.enviar_correo")
def test_registrar_retiro_descuenta_del_efectivo_esperado(mock_enviar, client, db_session):
    vendedor = crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, precio=10.0, stock=20)
    token = login(client, "vendedor@negocio.com")

    _vender(client, token, producto.id, 5)  # S/ 50 vendidos

    respuesta = client.post(
        "/api/caja/retiros",
        json={"monto": 20.0, "motivo": "Pago a proveedor de limpieza"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    retiro = respuesta.json()
    assert retiro["monto"] == 20.0
    assert retiro["motivo"] == "Pago a proveedor de limpieza"
    assert retiro["nombre_usuario"] == vendedor.nombre_completo

    estado = client.get("/api/caja/hoy", headers={"Authorization": f"Bearer {token}"}).json()
    assert estado["efectivo_esperado_hasta_ahora"] == 30.0
    assert len(estado["retiros"]) == 1


@patch("app.core.email.enviar_correo")
def test_cerrar_caja_calcula_efectivo_esperado_y_diferencia(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, precio=10.0, stock=20)
    token = login(client, "vendedor@negocio.com")

    _vender(client, token, producto.id, 5)  # S/ 50
    client.post(
        "/api/caja/retiros",
        json={"monto": 10.0, "motivo": "Compra de bolsas"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # esperado = 50 - 10 = 40

    respuesta = client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 35.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 201
    cierre = respuesta.json()
    assert cierre["efectivo_esperado"] == 40.0
    assert cierre["efectivo_contado"] == 35.0
    assert cierre["diferencia"] == -5.0
    assert cierre["estado"] == ESTADO_PENDIENTE_REVISION


@patch("app.core.email.enviar_correo")
def test_no_se_puede_cerrar_dos_veces_el_mismo_dia(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    respuesta1 = client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta1.status_code == 201

    respuesta2 = client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta2.status_code == 409


@patch("app.core.email.enviar_correo")
def test_no_se_pueden_registrar_retiros_tras_cerrar(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    respuesta = client.post(
        "/api/caja/retiros",
        json={"monto": 5.0, "motivo": "Tarde para el día ya cerrado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 409


@patch("app.core.email.enviar_correo")
def test_cerrar_caja_notifica_por_correo_al_dueno_activo(mock_enviar, client, db_session):
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    mock_enviar.assert_called_once()
    destinatario, asunto, cuerpo_html = mock_enviar.call_args[0]
    assert destinatario == dueno.correo
    assert "Cierre de caja" in asunto
    assert "Cuadre de caja" in cuerpo_html


@patch("app.core.email.enviar_correo")
def test_solo_dueno_puede_marcar_revisado(mock_enviar, client, db_session):
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    contador = crear_usuario_prueba(db_session, "contador@negocio.com", "contador")
    vendedor = crear_usuario_prueba(db_session, "vendedor2@negocio.com", "vendedor")
    token_vendedor = login(client, "vendedor2@negocio.com")

    cierre = client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token_vendedor}"},
    ).json()

    token_contador = login(client, "contador@negocio.com")
    respuesta_contador = client.patch(
        f"/api/caja/cierres/{cierre['id']}/revisar",
        headers={"Authorization": f"Bearer {token_contador}"},
    )
    assert respuesta_contador.status_code == 403

    respuesta_vendedor = client.patch(
        f"/api/caja/cierres/{cierre['id']}/revisar",
        headers={"Authorization": f"Bearer {token_vendedor}"},
    )
    assert respuesta_vendedor.status_code == 403

    token_dueno = login(client, "duena@negocio.com")
    respuesta_dueno = client.patch(
        f"/api/caja/cierres/{cierre['id']}/revisar",
        headers={"Authorization": f"Bearer {token_dueno}"},
    )
    assert respuesta_dueno.status_code == 200
    cuerpo = respuesta_dueno.json()
    assert cuerpo["estado"] == ESTADO_REVISADO
    assert cuerpo["nombre_revisor"] == dueno.nombre_completo
    assert cuerpo["fecha_revision"] is not None


@patch("app.core.email.enviar_correo")
def test_no_se_puede_revisar_dos_veces(mock_enviar, client, db_session):
    dueno = crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    token_dueno = login(client, "duena@negocio.com")

    cierre = client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 0.0},
        headers={"Authorization": f"Bearer {token_dueno}"},
    ).json()

    client.patch(
        f"/api/caja/cierres/{cierre['id']}/revisar",
        headers={"Authorization": f"Bearer {token_dueno}"},
    )
    respuesta = client.patch(
        f"/api/caja/cierres/{cierre['id']}/revisar",
        headers={"Authorization": f"Bearer {token_dueno}"},
    )
    assert respuesta.status_code == 409


@patch("app.core.email.enviar_correo")
def test_listar_cierres_no_accesible_para_vendedor(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    token = login(client, "vendedor@negocio.com")

    respuesta = client.get("/api/caja/cierres", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 403


@patch("app.core.email.enviar_correo")
def test_reporte_incluye_productos_vendidos_y_retiros(mock_enviar, client, db_session):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, nombre="ProductoReporte", precio=10.0, stock=20)
    token = login(client, "vendedor@negocio.com")

    _vender(client, token, producto.id, 2)
    client.post(
        "/api/caja/retiros",
        json={"monto": 5.0, "motivo": "Motivo de prueba"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/caja/cerrar",
        json={"efectivo_contado": 15.0},
        headers={"Authorization": f"Bearer {token}"},
    )

    _destinatario, _asunto, cuerpo_html = mock_enviar.call_args[0]
    assert "ProductoReporte" in cuerpo_html
    assert "Motivo de prueba" in cuerpo_html
    assert "Cuadra" in cuerpo_html
