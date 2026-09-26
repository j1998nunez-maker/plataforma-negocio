# config.py = el "panel de configuración" del proyecto. En vez de escribir
# contraseñas o direcciones de base de datos directo en el código (¡mala
# práctica, es un riesgo de seguridad!), este archivo las lee desde el
# archivo .env (que NO se sube a git).
#
# `Settings` se llena sola leyendo las variables de entorno / el .env.
# La usamos en todo el proyecto como: from app.core.config import settings

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def database_url(self) -> str:
        """Arma la cadena de conexión que SQLAlchemy necesita para hablar
        con PostgreSQL, a partir de las piezas sueltas de arriba."""
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
