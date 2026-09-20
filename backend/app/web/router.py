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
templates = Jinja2Templates(directory=str(_DIR_TEMPLATES))


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
