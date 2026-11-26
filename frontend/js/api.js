// api.js — Cliente HTTP del backend (Integrante 2)
// Responsabilidades: enviar peticiones, adjuntar el token (Authorization: Bearer),
// y manejar de forma centralizada 401 (no autenticado) y 403 (sin permiso).
// El token se guarda EN MEMORIA (nunca en el código ni en el repositorio).
(function (global) {
  class ApiError extends Error {
    constructor(status, codigo, mensaje) {
      super(mensaje || codigo || "HTTP " + status);
      this.status = status;
      this.codigo = codigo;
    }
  }

  class HttpClient {
    constructor(baseUrl, opciones) {
      opciones = opciones || {};
      this.baseUrl = baseUrl;
      // fetch inyectable: en el navegador usa el global; en pruebas se pasa un doble.
      this._fetch =
        opciones.fetch ||
        (typeof fetch !== "undefined" ? fetch.bind(globalThis) : null);
      this._token = null; // en memoria
      this.onNoAutenticado = opciones.onNoAutenticado || null; // callback 401
      this.onSinPermiso = opciones.onSinPermiso || null; // callback 403
    }

    setToken(token) {
      this._token = token;
    }
    getToken() {
      return this._token;
    }

    async request(metodo, ruta, cuerpo) {
      const headers = {};
      if (cuerpo !== undefined) headers["Content-Type"] = "application/json";
      if (this._token) headers["Authorization"] = "Bearer " + this._token;

      const resp = await this._fetch(this.baseUrl + ruta, {
        method: metodo,
        headers: headers,
        body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
      });

      if (resp.status === 204) return null; // sin contenido (DELETE)

      let datos = null;
      const texto = await resp.text();
      if (texto) {
        try {
          datos = JSON.parse(texto);
        } catch (e) {
          datos = texto;
        }
      }

      if (resp.ok) return datos;

      const err = (datos && datos.error) || {};
      // Manejo centralizado de autenticación/autorización:
      if (resp.status === 401 && this.onNoAutenticado) this.onNoAutenticado();
      if (resp.status === 403 && this.onSinPermiso)
        this.onSinPermiso(err.mensaje);
      throw new ApiError(resp.status, err.codigo, err.mensaje);
    }

    get(ruta) {
      return this.request("GET", ruta);
    }
    post(ruta, cuerpo) {
      return this.request("POST", ruta, cuerpo);
    }
    put(ruta, cuerpo) {
      return this.request("PUT", ruta, cuerpo);
    }
    del(ruta) {
      return this.request("DELETE", ruta);
    }
  }

  const api = { ApiError, HttpClient };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else Object.assign(global, api);
})(typeof self !== "undefined" ? self : globalThis);
