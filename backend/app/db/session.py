# session.py = el "cable" que conecta el backend con PostgreSQL.
#
# - `engine`: la conexión real a la base de datos (se crea una sola vez).
# - `SessionLocal`: una "fábrica" de sesiones. Una sesión es como una
#   conversación temporal con la base de datos (leer, guardar, etc.).
# - `get_db()`: una función que cada endpoint pide prestada para hablar con
#   la base de datos, y que se asegura de cerrar la conversación al terminar
#   (incluso si algo falla). FastAPI la usa automáticamente vía "Depends".

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
