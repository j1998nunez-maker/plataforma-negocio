# Graph Report - PLATAFORMA-NEGOCIO  (2026-09-25)

## Corpus Check
- Corpus is ~21,327 words - fits in a single context window. You may not need a graph.

## Summary
- 1098 nodes · 3073 edges · 68 communities (35 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 230 edges (avg confidence: 0.89)
- Token cost: 64,273 input · 0 output

## Community Hubs (Navigation)
- Chart.js Dataset Options
- KPIs & Lima Time Service
- Chart.js Core Helpers
- Integration Tests
- Auth, Session & Routers
- Frontend Pages & app.js
- Chart.js Time Scale
- Chart.js Registry & Scales
- Cash Closing (Caja)
- Chart.js Animations
- Chart.js Elements & Hit-Testing
- Chart.js Math Utils
- Chart.js Layout & Legend
- Sales Service & Reports
- ORM Models & Seeding
- Chart.js Events & Drawing
- Chart.js Minified Internals
- Chart.js DOM Events
- KPI & Product Endpoints
- Chart.js Minified Utils
- Chart.js Bar Controller
- Chart.js Tick Labels
- Chart.js Plugin Registry
- Chart.js Tooltip
- Chart.js Chart Lifecycle
- Chart.js Filler Plugin
- Chart.js Data Limits
- Chart.js Tooltip Drawing
- Chart.js Radial Scale
- Chart.js Data Parsing
- Chart.js Pixel Mapping
- Chart.js Doughnut Controller
- Chart.js Scale Config
- Chart.js Grid Drawing
- HTML Page Routes
- Chart.js Platform Canvas
- Chart.js Dataset Meta
- Chart.js Visibility
- Chart.js Layers
- Chart.js Legend Labels
- Templates & Web Deps
- KPI Product Charts
- App Settings
- Login & Auth Deps
- Excel Export
- Navigation Bar
- KPI Daily History
- KPI Loader
- KPI Day Summary
- KPI Month Summary
- alembic dependency
- httpx dependency
- pytest dependency
- email-validator dependency
- fastapi dependency
- psycopg2 dependency
- pydantic dependency
- pydantic-settings dependency
- sqlalchemy dependency
- uvicorn dependency
- Docker Postgres Service

## God Nodes (most connected - your core abstractions)
1. `an()` - 61 edges
2. `ns()` - 55 edges
3. `Usuario` - 54 edges
4. `crear_usuario_prueba()` - 45 edges
5. `s()` - 42 edges
6. `login()` - 41 edges
7. `o()` - 39 edges
8. `a()` - 38 edges
9. `n()` - 37 edges
10. `no` - 35 edges

## Surprising Connections (you probably didn't know these)
- `cargarResumenHoy()` --calls--> `apiFetch()`  [EXTRACTED]
  backend/app/web/templates/venta.html → backend/app/web/static/app.js
- `registrarVenta()` --calls--> `apiFetch()`  [EXTRACTED]
  backend/app/web/templates/venta.html → backend/app/web/static/app.js
- `formatearMoneda (kpis.html)` --semantically_similar_to--> `formatearMoneda() (venta)`  [INFERRED] [semantically similar]
  backend/app/web/templates/kpis.html → backend/app/web/templates/venta.html
- `formatearMoneda (productos.html)` --semantically_similar_to--> `formatearMoneda() (venta)`  [INFERRED] [semantically similar]
  backend/app/web/templates/productos.html → backend/app/web/templates/venta.html
- `formatearMoneda() (caja)` --semantically_similar_to--> `formatearMoneda() (venta)`  [INFERRED] [semantically similar]
  backend/app/web/templates/caja.html → backend/app/web/templates/venta.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Pages sharing the _nav.html partial include** — backend_app_web_templates_kpis_page, backend_app_web_templates_productos_page, backend_app_web_templates_usuarios_page [EXTRACTED 1.00]
- **Pages guarded by Sesion.exigir() session check** — backend_app_web_templates_kpis_page, backend_app_web_templates_productos_page, backend_app_web_templates_usuarios_page [INFERRED 0.85]
- **Role-gated admin CRUD pattern (create/list/toggle-status)** — backend_app_web_templates_productos_cargarproductos, backend_app_web_templates_productos_cambiarestado, backend_app_web_templates_productos_formproductosubmithandler, backend_app_web_templates_usuarios_cargarusuarios, backend_app_web_templates_usuarios_desactivarusuario, backend_app_web_templates_usuarios_formusuariosubmithandler [INFERRED 0.80]
- **PostgreSQL setup: README rationale, Docker service, Python driver** — docker_compose_db_service [INFERRED 0.80]
- **Flujo de cierre de caja (retiros, cuadre, revision del dueno)** — backend_app_web_templates_venta_cargarcaja, backend_app_web_templates_venta_pintarcajaabierta, backend_app_web_templates_venta_modal_cerrar_caja, backend_app_web_templates_venta_pintarcajacerrada, backend_app_web_templates_caja_cargarcierres, backend_app_web_templates_caja_marcarrevisado, backend_readme_cierre_de_caja [INFERRED 0.85]
- **Flujo de registrar venta (catalogo, busqueda, cantidad, confirmacion)** — backend_app_web_templates_venta_cargarproductos, backend_app_web_templates_venta_aplicarbusqueda, backend_app_web_templates_venta_pintarproductos, backend_app_web_templates_venta_abrirmodalcantidad, backend_app_web_templates_venta_registrarventa [EXTRACTED 1.00]

## Communities (68 total, 26 thin omitted)

### Community 0 - "Chart.js Dataset Options"
Cohesion: 0.05
Nodes (12): As(), beforeUpdate(), bn(), initialize(), labelColor(), labelPointStyle(), ns(), pn() (+4 more)

### Community 1 - "KPIs & Lima Time Service"
Cohesion: 0.08
Nodes (60): a_hora_lima(), hoy_lima(), inicio_utc_de_fecha_lima(), date, La fecha de "hoy" en hora local de Lima (no UTC, no la hora del servidor)., Convierte un datetime tal como llega de la base de datos (aware en PostgreSQL;…, Instante UTC exacto en que empieza (medianoche) una fecha de Lima. Sirve para…, HistoricoProductoItem (+52 more)

### Community 2 - "Chart.js Core Helpers"
Cohesion: 0.05
Nodes (21): at(), b(), cn(), destroy(), dn(), hn(), ho(), Ie() (+13 more)

### Community 3 - "Integration Tests"
Cohesion: 0.15
Nodes (45): Venta, crear_producto_prueba(), crear_usuario_prueba(), login(), patch, test_cerrar_caja_calcula_efectivo_esperado_y_diferencia(), test_cerrar_caja_notifica_por_correo_al_dueno_activo(), test_estado_hoy_antes_de_cualquier_movimiento() (+37 more)

### Community 4 - "Auth, Session & Routers"
Cohesion: 0.09
Nodes (36): crear_token(), _credenciales_invalidas(), get_current_user(), hashear_contrasena(), Session, Lee el token JWT que envía el navegador y devuelve el usuario real de la base…, Genera una dependencia que exige que el usuario logueado tenga uno de los roles…, requiere_rol() (+28 more)

### Community 5 - "Frontend Pages & app.js"
Cohesion: 0.07
Nodes (40): apiFetch(), fechaLimaISO(), hoyLimaISO(), Sesion, caja.html (historial de cierres), cargarCierres(), formatearMoneda() (caja), marcarRevisado() (+32 more)

### Community 6 - "Chart.js Time Scale"
Cohesion: 0.06
Nodes (12): beforeLayout(), buildLookupTable(), En, _generate(), getDecimalForValue(), _getTimestampsForTable(), init(), initOffsets() (+4 more)

### Community 7 - "Chart.js Registry & Scales"
Cohesion: 0.06
Nodes (14): Be(), bo, ce(), de, dt(), getValueForPixel(), H(), he() (+6 more)

### Community 8 - "Cash Closing (Caja)"
Cohesion: 0.16
Nodes (33): CierreCaja, RetiroCaja, cerrar_caja(), estado_hoy(), listar_cierres(), marcar_revisado(), get, patch (+25 more)

### Community 9 - "Chart.js Animations"
Cohesion: 0.09
Nodes (7): Cs, fe(), ks(), nn(), os(), sn, xt

### Community 10 - "Chart.js Elements & Hit-Testing"
Cohesion: 0.09
Nodes (30): ai(), ao(), average(), beforeDraw(), dataset(), draw(), getCenterPoint(), getMaxOverflow() (+22 more)

### Community 11 - "Chart.js Math Utils"
Cohesion: 0.09
Nodes (15): Bt(), color(), Ee(), Ft(), Gt(), It(), jt(), kt() (+7 more)

### Community 12 - "Chart.js Layout & Legend"
Cohesion: 0.10
Nodes (5): afterUpdate(), ba, d(), Di(), kn()

### Community 13 - "Sales Service & Reports"
Cohesion: 0.15
Nodes (27): generar_reporte_html(), Session, listar_ventas(), mas_vendidos_mes(), mis_ventas(), get, post, Session (+19 more)

### Community 14 - "ORM Models & Seeding"
Cohesion: 0.15
Nodes (14): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), Base, _fecha_vencimiento(), limpiar(), date (+6 more)

### Community 16 - "Chart.js Minified Internals"
Cohesion: 0.14
Nodes (21): es(), f(), g(), j(), m(), mt(), g(), o() (+13 more)

### Community 17 - "Chart.js DOM Events"
Cohesion: 0.13
Nodes (15): ct(), et(), fs(), ge(), s(), label(), ms(), on() (+7 more)

### Community 18 - "KPI & Product Endpoints"
Cohesion: 0.20
Nodes (20): exportar_dia(), historico_diario(), historico_productos_diario(), jornada_hoy(), date, get, Session, resumen_dia() (+12 more)

### Community 19 - "Chart.js Minified Utils"
Cohesion: 0.13
Nodes (18): aa(), e(), ei(), gi(), Gn(), je(), la(), mi() (+10 more)

### Community 20 - "Chart.js Bar Controller"
Cohesion: 0.15
Nodes (11): _calculateBarIndexPixels(), getLabelAndValue(), getLabelForValue(), _getRuler(), _getStackCount(), _getStackIndex(), _getStacks(), In() (+3 more)

### Community 23 - "Chart.js Tooltip"
Cohesion: 0.20
Nodes (3): afterDraw(), afterEvent(), va

### Community 24 - "Chart.js Chart Lifecycle"
Cohesion: 0.20
Nodes (3): ke(), reset(), wn()

### Community 25 - "Chart.js Filler Plugin"
Cohesion: 0.15
Nodes (14): beforeDatasetDraw(), beforeDatasetsDraw(), ca(), da(), ea(), fa(), ga(), ha (+6 more)

### Community 26 - "Chart.js Data Limits"
Cohesion: 0.22
Nodes (5): a(), determineDataLimits(), Fo(), is(), pt()

### Community 27 - "Chart.js Tooltip Drawing"
Cohesion: 0.30
Nodes (6): gs(), ki(), oa(), Oi(), Si(), x()

### Community 28 - "Chart.js Radial Scale"
Cohesion: 0.22
Nodes (3): Do(), eo(), Oe()

### Community 29 - "Chart.js Data Parsing"
Cohesion: 0.16
Nodes (9): buildTicks(), Fn(), go(), ii(), parse(), parseArrayData(), parsePrimitiveData(), po() (+1 more)

### Community 30 - "Chart.js Pixel Mapping"
Cohesion: 0.19
Nodes (4): _calculateBarValuePixels(), getBasePixel(), getPixelForValue(), updateElements()

### Community 32 - "Chart.js Scale Config"
Cohesion: 0.17
Nodes (6): addBox(), configure(), removeBox(), start(), stop(), vn()

### Community 33 - "Chart.js Grid Drawing"
Cohesion: 0.23
Nodes (4): Ae(), Bi(), Ci(), Fi()

### Community 34 - "HTML Page Routes"
Cohesion: 0.35
Nodes (11): pagina_caja(), pagina_kpis(), pagina_login(), pagina_productos(), pagina_usuarios(), pagina_venta(), get, raiz() (+3 more)

### Community 40 - "Templates & Web Deps"
Cohesion: 0.33
Nodes (6): Kpis Page (Indicadores), Login Page, Productos Page, Usuarios Page, jinja2==3.1.5 (dependency), python-multipart==0.0.20 (dependency)

### Community 41 - "KPI Product Charts"
Cohesion: 0.40
Nodes (5): cargarHistoricoProductosDiario, cargarJornadaHoy, crearFiltroProductos, dibujarGraficoHistoricoProductos, dibujarGraficoJornada

### Community 42 - "App Settings"
Cohesion: 0.50
Nodes (3): Arma la cadena de conexión que SQLAlchemy necesita para hablar con PostgreSQL,…, Settings, BaseSettings

### Community 45 - "Login & Auth Deps"
Cohesion: 0.67
Nodes (3): form-login submit handler, bcrypt==4.2.1 (dependency), pyjwt==2.10.1 (dependency)

## Knowledge Gaps
- **34 isolated node(s):** `Barra de navegación (_nav.html component)`, `Kpis Page (Indicadores)`, `cargarKpis`, `cargarResumenMes`, `cargarResumenDia` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 183 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ns()` connect `Chart.js Dataset Options` to `Chart.js Grid Drawing`, `Chart.js Core Helpers`, `Chart.js Dataset Meta`, `Chart.js Animations`, `Chart.js Minified Internals`, `Chart.js Bar Controller`, `Chart.js Tooltip`, `Chart.js Data Parsing`, `Chart.js Pixel Mapping`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `no` connect `Chart.js Time Scale` to `Chart.js Core Helpers`, `Chart.js Registry & Scales`, `Chart.js Elements & Hit-Testing`, `Chart.js Tick Labels`, `Chart.js Filler Plugin`, `Chart.js Data Limits`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `an()` connect `Chart.js Events & Drawing` to `Chart.js Scale Config`, `Chart.js Grid Drawing`, `Chart.js Core Helpers`, `Chart.js Dataset Meta`, `Chart.js Visibility`, `Chart.js Legend Labels`, `Chart.js Registry & Scales`, `Chart.js DOM Events`, `Chart.js Chart Lifecycle`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `Usuario` (e.g. with `cerrar_caja()` and `estado_hoy()`) actually correct?**
  _`Usuario` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `s()` (e.g. with `beforeUpdate()` and `da()`) actually correct?**
  _`s()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Barra de navegación (_nav.html component)`, `Kpis Page (Indicadores)`, `cargarKpis` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Chart.js Dataset Options` be split into smaller, more focused modules?**
  _Cohesion score 0.052464947987336044 - nodes in this community are weakly interconnected._