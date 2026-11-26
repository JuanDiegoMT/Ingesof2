// sensores.js — ViewModel del flujo de sensores (Integrante 1)
// Mantiene el estado de la pantalla (cargando/vacio/error/exito) y la lista.
// Es lógica pura y testeable: recibe un repositorio por inyección, sin DOM.
(function (global) {
  class SensoresViewModel {
    constructor(repo) {
      this.repo = repo;
      this.estado = "inicial"; // inicial | cargando | vacio | error | exito
      this.lista = [];
      this.mensaje = "";
    }

    async cargar() {
      this.estado = "cargando";
      this.mensaje = "";
      try {
        const lista = await this.repo.listar();
        this.lista = lista || [];
        this.estado = this.lista.length ? "exito" : "vacio";
      } catch (e) {
        this.estado = "error";
        this.mensaje = e.message || "No se pudieron cargar los sensores.";
      }
      return this.estado;
    }

    async crear(sensor) {
      const nuevo = await this.repo.crear(sensor);
      await this.cargar();
      return nuevo;
    }

    async eliminar(id) {
      await this.repo.eliminar(id);
      await this.cargar();
    }

    obtener(id) {
      return this.repo.obtener(id);
    }
  }

  const api = { SensoresViewModel };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else Object.assign(global, api);
})(typeof self !== "undefined" ? self : globalThis);
