# config.py = el "panel de configuración" del proyecto. En vez de escribir
# contraseñas o direcciones de base de datos directo en el código (¡mala
# práctica, es un riesgo de seguridad!), este archivo las lee desde el
# archivo .env (que NO se sube a git).
#
# `Settings` se llena sola leyendo las variables de entorno / el .env.
# La usamos en todo el proyecto como: from app.core.config import settings

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Base de datos ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "plataforma_negocio"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # --- JWT (tokens de sesión) ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRACION_MINUTOS: int = 480  # 8 horas de turno

    # --- Correo (reporte diario de cierre de caja al dueño) ---
    # Vacíos = envío desactivado (el cierre de caja funciona igual sin
    # correo configurado, solo no se notifica por email). Con Gmail, SMTP_USER
    # es tu correo completo y SMTP_PASSWORD es una "contraseña de aplicación"
    # (no tu contraseña normal) generada en myaccount.google.com/apppasswords.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # SSL: vacío = automático ("prefer" para localhost/Docker, que no tiene
    # SSL; "require" para cualquier servidor externo como Supabase, que lo
    # exige). Se puede forzar con DB_SSLMODE=disable|prefer|require|...
    DB_SSLMODE: str = ""
    # Segundos máximos esperando a que el servidor responda al conectar.
    # Sin esto, una conexión que no avanza se queda colgada para siempre.
    DB_CONNECT_TIMEOUT: int = 10

    @property
    def db_sslmode(self) -> str:
        if self.DB_SSLMODE:
            return self.DB_SSLMODE
        es_local = self.DB_HOST in ("localhost", "127.0.0.1", "::1", "db")
        return "prefer" if es_local else "require"

    @property
    def database_url(self) -> URL:
        """Arma la cadena de conexión que SQLAlchemy necesita para hablar
        con PostgreSQL, a partir de las piezas sueltas de arriba.

        Se usa URL.create (en vez de pegar texto con f-strings) para que
        una contraseña con caracteres especiales (@ : / # %) se escape bien
        y no rompa la URL."""
        return URL.create(
            "postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={
                "sslmode": self.db_sslmode,
                "connect_timeout": str(self.DB_CONNECT_TIMEOUT),
            },
        )


settings = Settings()
