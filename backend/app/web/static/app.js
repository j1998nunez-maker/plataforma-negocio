// app.js = el "conector" entre las páginas HTML y la API del backend.
// No hay build ni framework: son funciones simples que usan fetch() para
// hablar con /auth, /ventas, /productos, /usuarios, /kpis.
//
// La sesión (token JWT + rol + nombre) se guarda en localStorage del
// navegador. Es la forma más simple para un MVP; el token viaja en el
// header "Authorization: Bearer <token>" en cada request protegido.

const Sesion = {
  guardar(token, rol, nombreCompleto) {
    localStorage.setItem("token", token);
    localStorage.setItem("rol", rol);
    localStorage.setItem("nombre", nombreCompleto);
  },
  token: () => localStorage.getItem("token"),
  rol: () => localStorage.getItem("rol"),
  nombre: () => localStorage.getItem("nombre"),
  cerrar() {
    localStorage.clear();
    window.location.href = "/login";
  },
  exigir() {
    if (!Sesion.token()) {
      window.location.href = "/login";
    }
  },
};

// Todos los endpoints de la API real viven bajo /api/... (las páginas HTML
// usan las mismas rutas "bonitas" como /productos o /usuarios, así que la
// API se movió a su propio prefijo para no chocar con ellas). apiFetch()
// arma esa ruta completa, así el resto del código solo escribe "/productos"
// en vez de "/api/productos" en cada llamada.
async function apiFetch(ruta, opciones = {}) {
  const cabeceras = opciones.headers || {};
  if (Sesion.token()) {
    cabeceras["Authorization"] = `Bearer ${Sesion.token()}`;
  }
  if (opciones.body && !(opciones.body instanceof URLSearchParams)) {
    cabeceras["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(opciones.body);
  }

  const respuesta = await fetch(`/api${ruta}`, { ...opciones, headers: cabeceras });

  if (respuesta.status === 401) {
    Sesion.cerrar();
    throw new Error("Sesión expirada");
  }

  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new Error(datos.detail || "Ocurrió un error inesperado.");
  }
  return datos;
}

// Pinta la barra de navegación según el rol logueado y arma el botón de
// salir. Se llama al cargar cualquier página protegida.
function pintarNav() {
  const contenedorNav = document.getElementById("nav-enlaces");
  const nombreSpan = document.getElementById("nav-nombre");
  if (!contenedorNav) return;

  const rol = Sesion.rol();
  if (nombreSpan) nombreSpan.textContent = `${Sesion.nombre()} (${rol})`;

  const enlaces = [{ href: "/venta", texto: "Registrar venta", roles: ["dueno", "contador", "vendedor"] }];
  enlaces.push({ href: "/productos", texto: "Productos", roles: ["dueno", "contador", "vendedor"] });
  enlaces.push({ href: "/kpis", texto: "Indicadores", roles: ["dueno", "contador"] });
  enlaces.push({ href: "/usuarios", texto: "Usuarios", roles: ["dueno", "contador"] });

  contenedorNav.innerHTML = enlaces
    .filter((e) => e.roles.includes(rol))
    .map((e) => `<a href="${e.href}">${e.texto}</a>`)
    .join("");

  const botonSalir = document.getElementById("nav-salir");
  if (botonSalir) botonSalir.addEventListener("click", Sesion.cerrar);
}

document.addEventListener("DOMContentLoaded", pintarNav);
