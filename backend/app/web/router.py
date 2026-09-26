# router.py (web) = sirve las páginas HTML del frontend simple. No hace
# consultas a la base de datos aquí: cada página trae su propio JavaScript
# (static/app.js) que llama a la API real (los endpoints /auth, /ventas,
# /productos, /usuarios, /kpis) usando fetch(), igual que lo haría una app
# de celular. Este módulo solo entrega el HTML/CSS/JS al navegador.

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["frontend"])

_DIR_TEMPLATES = Path(__file__).parent / "templates"
_DIR_STATIC = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(_DIR_TEMPLATES))


def _version_estatica(nombre_archivo: str) -> int:
    """Fecha de modificación de un archivo en static/, para usarla como
    "?v=..." en su URL (ej. /static/app.js?v=1758...). Así, cada vez que se
    edita app.js o style.css, la URL cambia y el navegador pide la versión
    nueva en vez de quedarse con una copia vieja en caché — esto es lo que
    causó que /venta y /kpis se rompieran después de agregar funciones
    nuevas a app.js: el navegador siguió usando el app.js de antes."""
    try:
        return int((_DIR_STATIC / nombre_archivo).stat().st_mtime)
    except FileNotFoundError:
        return 0


templates.env.globals["version_estatica"] = _version_estatica


@router.get("/")
def raiz(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/login")
def pagina_login(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.get("/venta")
def pagina_venta(request: Request):
    return templates.TemplateResponse(request, "venta.html")


@router.get("/productos")
def pagina_productos(request: Request):
    return templates.TemplateResponse(request, "productos.html")


@router.get("/usuarios")
def pagina_usuarios(request: Request):
    return templates.TemplateResponse(request, "usuarios.html")


@router.get("/kpis")
def pagina_kpis(request: Request):
    return templates.TemplateResponse(request, "kpis.html")


@router.get("/caja")
def pagina_caja(request: Request):
    return templates.TemplateResponse(request, "caja.html")
