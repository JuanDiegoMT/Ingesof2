// app.js — Controlador de la interfaz (une vistas y servicios). Solo navegador.
// Flujo: login -> lista de sensores -> ver/crear/eliminar, con manejo de 401 y 403.
(function () {
  if (typeof document === "undefined") return; // no corre en pruebas de Node

  // --- Construcción de dependencias (inyección) ---
  const http = new HttpClient(AgroConfig.BACKEND_URL, {
    onNoAutenticado: volverALogin, // 401 -> de vuelta al login
    onSinPermiso: mostrarSinPermiso, // 403 -> mensaje de permiso
  });
  const auth = new AuthService(http);
  const repo = new SensorRepositorio(http);
  const vm = new SensoresViewModel(repo);

  // --- Referencias a la interfaz ---
  const $ = (id) => document.getElementById(id);
  const vistaLogin = $("vista-login");
  const vistaApp = $("vista-app");
  const loginMsg = $("login-msg");
  const listaCont = $("lista-sensores");
  const avisoPermiso = $("aviso-permiso");

  // --- Eventos ---
  $("form-login").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    loginMsg.textContent = "";
    loginMsg.className = "msg";
    try {
      await auth.iniciarSesion($("correo").value.trim(), $("contrasena").value);
      entrarAlApp();
    } catch (e) {
      loginMsg.textContent = auth.mensaje;
      loginMsg.className = "msg error";
    }
  });

  $("btn-registrar").addEventListener("click", async () => {
    loginMsg.textContent = "";
    const correo = $("correo").value.trim();
    const contrasena = $("contrasena").value;
    if (!correo || contrasena.length < 12) {
      loginMsg.textContent =
        "Para registrarte: correo válido y contraseña de 12+ caracteres.";
      loginMsg.className = "msg error";
      return;
    }
    try {
      await auth.registrar(correo, contrasena);
      loginMsg.textContent = "Cuenta creada. Ahora inicia sesión.";
      loginMsg.className = "msg exito";
    } catch (e) {
      loginMsg.textContent =
        e.status === 409 ? "Ese correo ya está registrado." : e.message;
      loginMsg.className = "msg error";
    }
  });

  $("btn-salir").addEventListener("click", () => {
    auth.cerrarSesion();
    volverALogin();
  });

  $("form-crear").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    avisoPermiso.textContent = "";
    const sensor = {
      nombre: $("c-nombre").value.trim(),
      ubicacion: $("c-ubicacion").value.trim(),
      profundidad_cm: Number($("c-profundidad").value),
    };
    try {
      await vm.crear(sensor);
      ev.target.reset();
      renderLista();
    } catch (e) {
      if (e.status === 403) mostrarSinPermiso();
      else avisoPermiso.textContent = e.message || "No se pudo crear.";
    }
  });

  // --- Navegación / estados ---
  function entrarAlApp() {
    vistaLogin.hidden = true;
    vistaApp.hidden = false;
    renderLista();
  }
  function volverALogin() {
    vistaApp.hidden = true;
    vistaLogin.hidden = false;
  }
  function mostrarSinPermiso() {
    avisoPermiso.textContent =
      "Permiso insuficiente: solo un administrador puede modificar sensores (403).";
  }

  async function renderLista() {
    estadoCargando(listaCont);
    const estado = await vm.cargar();
    if (estado === "cargando") return;
    if (estado === "error") return estadoError(listaCont, vm.mensaje);
    if (estado === "vacio")
      return estadoVacio(listaCont, "No hay sensores registrados.");
    // estado === "exito"
    const filas = vm.lista
      .map(
        (s) =>
          "<tr><td>" +
          s.id +
          "</td><td>" +
          escapar(s.nombre) +
          "</td><td>" +
          escapar(s.ubicacion) +
          "</td><td>" +
          s.profundidad_cm +
          ' cm</td><td><button data-ver="' +
          s.id +
          '">Ver</button> <button data-del="' +
          s.id +
          '">Eliminar</button></td></tr>'
      )
      .join("");
    listaCont.innerHTML =
      "<table><thead><tr><th>ID</th><th>Nombre</th><th>Ubicación</th><th>Prof.</th><th></th></tr></thead><tbody>" +
      filas +
      "</tbody></table>";

    listaCont.querySelectorAll("[data-ver]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          const s = await vm.obtener(b.getAttribute("data-ver"));
          alert(
            "Sensor #" +
              s.id +
              "\nNombre: " +
              s.nombre +
              "\nUbicación: " +
              s.ubicacion +
              "\nProfundidad: " +
              s.profundidad_cm +
              " cm"
          );
        } catch (e) {
          if (e.status === 403) mostrarSinPermiso();
        }
      })
    );
    listaCont.querySelectorAll("[data-del]").forEach((b) =>
      b.addEventListener("click", async () => {
        avisoPermiso.textContent = "";
        try {
          await vm.eliminar(b.getAttribute("data-del"));
          renderLista();
        } catch (e) {
          if (e.status === 403) mostrarSinPermiso();
          else avisoPermiso.textContent = e.message;
        }
      })
    );
  }

  function escapar(t) {
    return String(t).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c]
    );
  }
})();
