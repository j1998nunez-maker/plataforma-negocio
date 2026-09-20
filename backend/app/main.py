# main.py = el "encendido" de la aplicación. Es el archivo que se ejecuta
# para levantar el servidor backend. Aquí se crea la app de FastAPI, se
# conectan ("enchufan") los endpoints de cada módulo (usuarios, productos,
# ventas, KPIs) y se sirve el frontend simple (páginas HTML + JS/CSS).
#
# Para correrlo: uvicorn app.main:app --reload  (ver README para el detalle)

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.kpis.router import router as kpis_router
from app.productos.router import router as productos_router
from app.usuarios.router import auth_router, usuarios_router
from app.ventas.router import router as ventas_router
from app.web.router import router as web_router

app = FastAPI(title="Plataforma Negocio - MVP")


@app.get("/salud", tags=["sistema"])
def salud():
    """Endpoint simple para comprobar que el servidor está vivo."""
    return {"estado": "ok"}


# --- API (bajo /api para no chocar con las páginas HTML de abajo, que
#     usan las mismas rutas "bonitas": /productos, /usuarios, etc.) ---
app.include_router(auth_router, prefix="/api")
app.include_router(usuarios_router, prefix="/api")
app.include_router(productos_router, prefix="/api")
app.include_router(ventas_router, prefix="/api")
app.include_router(kpis_router, prefix="/api")

# --- Frontend simple (HTML servido por el mismo backend) ---
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "web" / "static")),
    name="static",
)
app.include_router(web_router)
