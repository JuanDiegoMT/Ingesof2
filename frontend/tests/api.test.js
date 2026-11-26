// api.test.js — Pruebas de integración del cliente HTTP (Integrante 2)
// Usan un doble de fetch (interceptor) en lugar de un servidor real.
// Ejecutar: node --test frontend/tests/
const test = require("node:test");
const assert = require("node:assert");
const { HttpClient, ApiError } = require("../js/api.js");

function fetchFalso(status, cuerpo) {
  return async function () {
    return {
      ok: status >= 200 && status < 300,
      status: status,
      text: async () => (cuerpo === null ? "" : JSON.stringify(cuerpo)),
    };
  };
}

test("una respuesta 200 se mapea correctamente a datos", async () => {
  const http = new HttpClient("http://backend", {
    fetch: fetchFalso(200, [{ id: 1, nombre: "Sonda A" }]),
  });
  const datos = await http.get("/api/v1/sensores");
  assert.deepStrictEqual(datos, [{ id: 1, nombre: "Sonda A" }]);
});

test("una respuesta 401 lanza ApiError y dispara onNoAutenticado", async () => {
  let redirigido = false;
  const http = new HttpClient("http://backend", {
    fetch: fetchFalso(401, { error: { codigo: "token_invalido", mensaje: "x" } }),
    onNoAutenticado: () => {
      redirigido = true;
    },
  });
  await assert.rejects(
    () => http.get("/api/v1/sensores"),
    (e) => e instanceof ApiError && e.status === 401
  );
  assert.strictEqual(redirigido, true);
});

test("el token se adjunta en Authorization: Bearer", async () => {
  let cabeceras = null;
  const http = new HttpClient("http://backend", {
    fetch: async (url, opciones) => {
      cabeceras = opciones.headers;
      return { ok: true, status: 200, text: async () => "[]" };
    },
  });
  http.setToken("abc.def.ghi");
  await http.get("/api/v1/sensores");
  assert.strictEqual(cabeceras["Authorization"], "Bearer abc.def.ghi");
});
