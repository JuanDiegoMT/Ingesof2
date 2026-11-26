// auth.js — Servicio de autenticación (Integrante 2)
// Encapsula registro, login y cierre de sesión. La vista NO llama a la API:
// habla con este servicio, que a su vez usa el HttpClient.
(function (global) {
  class AuthService {
    constructor(http) {
      this.http = http;
      this.estado = "inicial"; // inicial | cargando | autenticado | error
      this.mensaje = "";
      this.sesion = null; // { token }
    }

    async iniciarSesion(correo, contrasena) {
      this.estado = "cargando";
      this.mensaje = "";
      try {
        const r = await this.http.post("/api/v1/auth/login", {
          correo: correo,
          contrasena: contrasena,
        });
        this.http.setToken(r.access_token); // token en memoria
        this.sesion = { token: r.access_token };
        this.estado = "autenticado";
        return r;
      } catch (e) {
        this.estado = "error";
        this.mensaje =
          e.status === 401
            ? "Correo o contraseña incorrectos."
            : e.message || "No se pudo iniciar sesión.";
        throw e;
      }
    }

    async registrar(correo, contrasena) {
      // Crea una cuenta de agricultor (rol por defecto en el backend).
      return this.http.post("/api/v1/auth/registro", {
        correo: correo,
        contrasena: contrasena,
      });
    }

    cerrarSesion() {
      this.http.setToken(null);
      this.sesion = null;
      this.estado = "inicial";
    }

    estaAutenticado() {
      return this.estado === "autenticado";
    }
  }

  const api = { AuthService };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else Object.assign(global, api);
})(typeof self !== "undefined" ? self : globalThis);
