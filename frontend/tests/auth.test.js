// auth.test.js — Pruebas unitarias de la lógica de presentación (Integrante 2)
// Verifican el ViewModel sin red, usando un repositorio doble (fake).
// Ejecutar: node --test frontend/tests/
const test = require("node:test");
const assert = require("node:assert");
const { SensoresViewModel } = require("../js/sensores.js");

test("una lista vacía produce el estado 'vacio'", async () => {
  const repoFake = { listar: async () => [] };
  const vm = new SensoresViewModel(repoFake);
  await vm.cargar();
  assert.strictEqual(vm.estado, "vacio");
});

test("un error de red produce el estado 'error'", async () => {
  const repoFake = {
    listar: async () => {
      throw new Error("fallo de red");
    },
  };
  const vm = new SensoresViewModel(repoFake);
  await vm.cargar();
  assert.strictEqual(vm.estado, "error");
  assert.strictEqual(vm.mensaje, "fallo de red");
});

test("una lista con datos produce el estado 'exito'", async () => {
  const repoFake = { listar: async () => [{ id: 1, nombre: "Sonda A" }] };
  const vm = new SensoresViewModel(repoFake);
  await vm.cargar();
  assert.strictEqual(vm.estado, "exito");
  assert.strictEqual(vm.lista.length, 1);
});
