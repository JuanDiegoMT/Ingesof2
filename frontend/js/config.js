// config.js — Configuración del cliente (Integrante 2)
// La URL del backend se lee de aquí, NO está escrita dentro de la lógica.
// Para cambiarla sin tocar el código, pueden definir window.AGRO_BACKEND_URL antes de cargar los scripts.
(function (global) {
  const config = {
    BACKEND_URL:
      (typeof global !== "undefined" && global.AGRO_BACKEND_URL) ||
      "http://127.0.0.1:8000",
  };
  if (typeof module !== "undefined" && module.exports) module.exports = config;
  else global.AgroConfig = config;
})(typeof self !== "undefined" ? self : globalThis);
