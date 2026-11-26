// estados.js — Helpers de estados de interfaz (Integrante 1)
// Cada pantalla debe mostrar: cargando, vacío, error y éxito.
(function (global) {
  function estadoCargando(el) {
    el.innerHTML = '<p class="estado cargando">Cargando…</p>';
  }
  function estadoVacio(el, mensaje) {
    el.innerHTML =
      '<p class="estado vacio">' + (mensaje || "No hay datos todavía.") + "</p>";
  }
  function estadoError(el, mensaje) {
    el.innerHTML =
      '<p class="estado error">' + (mensaje || "Ocurrió un error.") + "</p>";
  }
  function limpiar(el) {
    el.innerHTML = "";
  }

  const api = { estadoCargando, estadoVacio, estadoError, limpiar };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else Object.assign(global, api);
})(typeof self !== "undefined" ? self : globalThis);
