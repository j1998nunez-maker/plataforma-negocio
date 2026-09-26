# email.py = envío de correo por SMTP (librería estándar de Python, sin
# dependencias nuevas). Se usa para el reporte diario de cierre de caja.
#
# Si SMTP_USER/SMTP_PASSWORD no están configurados en .env, `enviar_correo`
# no intenta conectarse a nada: solo deja un aviso en el log. Así el cierre
# de caja funciona igual (con o sin correo configurado) mientras el dueño
# no haya puesto sus credenciales reales todavía.

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def enviar_correo(
    destinatario: str,
    asunto: str,
    cuerpo_html: str,
    adjuntos: list[tuple[str, bytes, str]] | None = None,
) -> None:
    """`adjuntos` es opcional: lista de (nombre_archivo, contenido, tipo_mime),
    ej. [("cierre.pdf", pdf_bytes, "application/pdf")]."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "Envío de correo desactivado (falta SMTP_USER/SMTP_PASSWORD en .env). "
            "No se envió: '%s' a %s.",
            asunto,
            destinatario,
        )
        return

    mensaje = MIMEMultipart("mixed" if adjuntos else "alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = settings.SMTP_FROM or settings.SMTP_USER
    mensaje["To"] = destinatario
    mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))
    for nombre, contenido, tipo_mime in adjuntos or []:
        principal, secundario = tipo_mime.split("/", 1)
        parte = MIMEBase(principal, secundario)
        parte.set_payload(contenido)
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", "attachment", filename=nombre)
        mensaje.attach(parte)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as servidor:
        servidor.starttls()
        servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        servidor.sendmail(mensaje["From"], [destinatario], mensaje.as_string())
