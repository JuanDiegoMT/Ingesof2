// repositorio.js — Repositorio de sensores (Integrante 2)
// Aísla el acceso al recurso "sensores" detrás de métodos con nombre de negocio.
// El ViewModel usa este repositorio; nunca llama al HttpClient directamente.
(function (global) {
  class SensorRepositorio {
    constructor(http) {
      this.http = http;
    }
    listar(limite) {
      return this.http.get("/api/v1/sensores?limite=" + (limite || 50));
    }
    obtener(id) {
      return this.http.get("/api/v1/sensores/" + id);
    }
    crear(sensor) {
      return this.http.post("/api/v1/sensores", sensor);
    }
    actualizar(id, sensor) {
      return this.http.put("/api/v1/sensores/" + id, sensor);
    }
    eliminar(id) {
      return this.http.del("/api/v1/sensores/" + id);
    }
  }

  const api = { SensorRepositorio };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else Object.assign(global, api);
})(typeof self !== "undefined" ? self : globalThis);
