# conftest.py = la preparación que pytest corre antes de cada prueba.
#
# En vez de conectarnos a PostgreSQL real, para las pruebas automáticas
# usamos SQLite en memoria (una base de datos temporal que vive solo
# mientras corre el test y desaparece después). Esto prueba toda nuestra
# lógica (endpoints, permisos, cálculos) sin necesitar Postgres corriendo.
# La prueba "de verdad" contra PostgreSQL se hace aparte, manualmente,
# antes de entregar a un cliente piloto (ver README.md).

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hashear_contrasena
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.productos.models import Producto
from app.usuarios.models import Usuario

engine_prueba = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionPrueba = sessionmaker(bind=engine_prueba)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(engine_prueba)
    sesion = SessionPrueba()
    try:
        yield sesion
    finally:
        sesion.close()
        Base.metadata.drop_all(engine_prueba)


@pytest.fixture()
def client(db_session):
    def _get_db_prueba():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_prueba
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def crear_usuario_prueba(db_session, correo: str, rol: str, contrasena: str = "clave123") -> Usuario:
    usuario = Usuario(
        nombre_completo=f"Usuario {rol}",
        correo=correo,
        contrasena_hash=hashear_contrasena(contrasena),
        rol=rol,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def crear_producto_prueba(db_session, nombre="Paracetamol 500mg", stock=10, precio=5.5) -> Producto:
    producto = Producto(nombre=nombre, precio_venta=precio, stock_actual=stock)
    db_session.add(producto)
    db_session.commit()
    db_session.refresh(producto)
    return producto


def login(client, correo: str, contrasena: str = "clave123") -> str:
    respuesta = client.post(
        "/api/auth/login", data={"username": correo, "password": contrasena}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]
