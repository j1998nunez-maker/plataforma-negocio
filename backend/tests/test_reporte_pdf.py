# Pruebas del PDF del cierre de caja: que se adjunte al mismo correo del
# cierre, que su texto sea simple (frases del cuadre y fecha en palabras),
# que el correo sin adjuntos siga saliendo igual que antes, y que si el PDF
# falla el correo se envíe de todas formas.

from datetime import date
from email import message_from_string
from unittest.mock import patch

from app.caja.reporte_pdf import fecha_en_palabras, frase_cuadre
from app.core import email as modulo_email
from tests.conftest import crear_producto_prueba, crear_usuario_prueba, login


def _cerrar_con_una_venta(client, db_session, efectivo_contado):
    crear_usuario_prueba(db_session, "duena@negocio.com", "dueno")
    crear_usuario_prueba(db_session, "vendedor@negocio.com", "vendedor")
    producto = crear_producto_prueba(db_session, precio=10.0, stock=20)
    token = login(client, "vendedor@negocio.com")
    cabeceras = {"Authorization": f"Bearer {token}"}

    client.post("/api/ventas", json={"producto_id": producto.id, "cantidad": 3}, headers=cabeceras)
    client.post("/api/caja/retiros", json={"monto": 5.0, "motivo": "Compra de bolsas"}, headers=cabeceras)
    respuesta = client.post(
        "/api/caja/cerrar", json={"efectivo_contado": efectivo_contado}, headers=cabeceras
    )
    assert respuesta.status_code == 201, respuesta.text


@patch("app.core.email.enviar_correo")
def test_cierre_adjunta_pdf_al_mismo_correo(mock_enviar, client, db_session):
    _cerrar_con_una_venta(client, db_session, efectivo_contado=20.0)

    mock_enviar.assert_called_once()
    _, asunto, cuerpo_html = mock_enviar.call_args[0]
    assert "Cierre de caja" in asunto
    assert "Cuadre de caja" in cuerpo_html

    adjuntos = mock_enviar.call_args.kwargs["adjuntos"]
    assert len(adjuntos) == 1
    nombre, contenido, tipo_mime = adjuntos[0]
    assert nombre.startswith("cierre-de-caja-") and nombre.endswith(".pdf")
    assert tipo_mime == "application/pdf"
    assert contenido.startswith(b"%PDF")


@patch("app.caja.reporte_pdf.generar_reporte_pdf", side_effect=RuntimeError("falla simulada"))
@patch("app.core.email.enviar_correo")
def test_si_el_pdf_falla_el_correo_sale_igual_sin_adjunto(mock_enviar, _mock_pdf, client, db_session):
    _cerrar_con_una_venta(client, db_session, efectivo_contado=25.0)

    mock_enviar.assert_called_once()
    assert mock_enviar.call_args.kwargs["adjuntos"] == []


def test_frase_del_cuadre_es_simple():
    assert frase_cuadre(0) == "La caja cuadró correctamente."
    assert frase_cuadre(0.001) == "La caja cuadró correctamente."
    assert frase_cuadre(-5) == "Falta S/ 5.00 por verificar."
    assert frase_cuadre(12.5) == "Sobra S/ 12.50 por verificar."


def test_fecha_en_palabras():
    assert fecha_en_palabras(date(2026, 9, 25)) == "Viernes 25 de septiembre de 2026"


class _SMTPFalso:
    enviados: list[str] = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, *args):
        pass

    def sendmail(self, remitente, destinatarios, texto):
        _SMTPFalso.enviados.append(texto)


def _enviar_y_capturar(**kwargs):
    _SMTPFalso.enviados = []
    with (
        patch.object(modulo_email.settings, "SMTP_USER", "negocio@gmail.com"),
        patch.object(modulo_email.settings, "SMTP_PASSWORD", "clave"),
        patch.object(modulo_email.smtplib, "SMTP", _SMTPFalso),
    ):
        modulo_email.enviar_correo("duena@negocio.com", "Asunto", "<p>Hola</p>", **kwargs)
    return message_from_string(_SMTPFalso.enviados[0])


def test_correo_sin_adjuntos_sigue_igual_que_antes():
    mensaje = _enviar_y_capturar()
    assert mensaje.get_content_type() == "multipart/alternative"
    partes = [p.get_content_type() for p in mensaje.walk() if not p.is_multipart()]
    assert partes == ["text/html"]


def test_correo_con_pdf_adjunto():
    mensaje = _enviar_y_capturar(adjuntos=[("cierre.pdf", b"%PDF-1.4 prueba", "application/pdf")])
    assert mensaje.get_content_type() == "multipart/mixed"
    partes = [p for p in mensaje.walk() if not p.is_multipart()]
    assert [p.get_content_type() for p in partes] == ["text/html", "application/pdf"]
    assert partes[1].get_filename() == "cierre.pdf"
    assert partes[1].get_payload(decode=True) == b"%PDF-1.4 prueba"
