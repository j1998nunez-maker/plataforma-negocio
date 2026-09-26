# Plataforma Negocio — MVP

Backend (FastAPI + PostgreSQL) y frontend simple (HTML/JS servido por el
mismo backend) para gestión de ventas, productos, usuarios e indicadores
(KPIs) de un negocio pequeño (farmacia, botica, veterinaria, óptica).

## 1. Requisitos

- Python 3.11+ (ya tienes 3.11 y 3.13 instalados)
- PostgreSQL — tienes dos opciones, elige una:
  - **Opción A — usar tu PostgreSQL ya instalado** (detectamos un servicio
    de Windows `postgresql-x64-15` corriendo en el puerto 5432). Crea ahí
    una base de datos vacía llamada `plataforma_negocio` y ajusta
    `DB_PORT=5432` y tu contraseña real en `.env`.
  - **Opción B — usar el contenedor Docker incluido** (recomendado si no
    quieres tocar tu instalación existente): usa el puerto **5433** para no
    chocar con la Opción A. Ya viene configurado así por defecto.

## 2. Preparar el entorno (una sola vez)

Desde la carpeta `backend/`:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

copy .env.example .env
# Abre .env y pon tu contraseña real de PostgreSQL y un JWT_SECRET_KEY propio.
# Para generar uno: .venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
```

Si eliges la Opción B (Docker), desde la carpeta raíz del proyecto:

```powershell
docker compose up -d
```

## 3. Crear las tablas (migraciones)

```powershell
.venv\Scripts\python -m alembic upgrade head
```

Esto crea las tablas `usuarios`, `productos` y `ventas` en tu base de
datos, siguiendo el diseño que revisamos juntos.

## 4. Crear el primer usuario (dueño)

No hay forma de crear usuarios por la API sin estar ya logueado como
dueño — así que el primero se crea directo con este script:

```powershell
.venv\Scripts\python crear_dueno_inicial.py
```

Te va a pedir nombre, correo y contraseña.

## 5. Correr la plataforma

```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- App web (login, ventas, productos, usuarios, KPIs): http://localhost:8000
- Documentación interactiva de la API (Swagger): http://localhost:8000/docs

## 6. Sembrar datos de prueba (opcional, solo cuando tú quieras)

```powershell
.venv\Scripts\python sembrar_datos_prueba.py             # crea productos y ventas de ejemplo
.venv\Scripts\python sembrar_datos_prueba.py --limpiar   # borra SOLO esos datos de ejemplo
```

Es un script aparte, no se ejecuta solo con la app. Todo lo que crea queda
marcado con el prefijo `DEMO - ` en el nombre del producto, así nunca se
confunde con tu catálogo real — y `--limpiar` borra únicamente lo marcado
así, sin tocar productos o ventas reales.

## 7. Correr las pruebas automáticas

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```

Las pruebas usan una base de datos SQLite temporal (no tocan tu
PostgreSQL real) y verifican: login, permisos por rol, registrar venta con
descuento de stock, precio histórico, el cálculo de KPIs, y el cierre de
caja con su reporte y aprobación. Las 39 pruebas pasan actualmente.

## Mapa del proyecto

```
backend/
  app/
    core/       -> configuración (.env), seguridad (login, JWT), hora de Lima y envío de correo
    db/         -> conexión a PostgreSQL
    usuarios/   -> login y gestión de usuarios (roles: dueño, contador, vendedor)
    productos/  -> catálogo (nombre, stock, vencimiento)
    ventas/     -> registro de ventas, resumen de hoy y más vendidos del mes
    kpis/       -> resumen de indicadores para la app (Power BI hace el análisis a fondo)
    caja/       -> cierre de caja diario (retiros, cuadre) y reporte por correo al dueño
    web/        -> frontend simple (páginas HTML + JS que llaman a la API)
  alembic/      -> historial de migraciones de la base de datos
  tests/        -> pruebas automáticas
  crear_dueno_inicial.py -> script para crear el primer usuario
```

## Roles y qué puede hacer cada uno

| Acción | Dueño | Contador | Vendedor |
|---|---|---|---|
| Ver catálogo de productos | Sí | Sí | Sí |
| Crear/editar productos | Sí | Sí | No |
| Registrar una venta | Sí | Sí | Sí |
| Ver historial completo de ventas | Sí | Sí | No (solo las propias) |
| Ver indicadores (KPIs) | Sí | Sí | No |
| Crear usuarios nuevos | Sí | No | No |
| Ver lista de usuarios | Sí | Sí | No |
| Desactivar usuarios | Sí | No | No |
| Registrar retiros y cerrar la caja del día | Sí | Sí | Sí |
| Ver el historial de cierres de caja | Sí | Sí | No |
| Marcar un cierre como "revisado" | Sí | No | No |

## Reporte diario de cierre de caja por correo

Al cerrar la caja del día (desde `/venta`), se genera un reporte y se envía
por correo a todos los usuarios con rol `dueno`. El envío usa Gmail SMTP
(librería estándar de Python, sin dependencias nuevas) y se configura con las
variables `SMTP_*` del `.env` — mientras `SMTP_USER`/`SMTP_PASSWORD` estén
vacíos, el cierre de caja funciona igual, solo que no se manda el correo (se
avisa en el log del servidor). Para activarlo con Gmail:

1. Activa la verificación en dos pasos en tu cuenta de Google.
2. Genera una "contraseña de aplicación" en https://myaccount.google.com/apppasswords.
3. En tu `.env`, pon `SMTP_USER=tu_correo@gmail.com` y `SMTP_PASSWORD=` esa
   contraseña de aplicación (no tu contraseña normal).

## Conexión con Power BI (fase futura)

Cuando llegue esa etapa, Power BI se conecta directo a PostgreSQL (host,
puerto, base de datos y usuario de `.env`) con un usuario de solo lectura
— no hace falta ningún endpoint especial para esto, las tablas ya están
normalizadas para eso desde el diseño.
