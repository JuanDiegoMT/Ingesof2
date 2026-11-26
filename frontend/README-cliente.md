# Cliente web de AgroDecide (Prototipo 2)

Cliente web en HTML + JavaScript (sin dependencias) que consume la API del backend del Prototipo 1. Cubre la parte de **Integración cliente–backend** (Integrantes 1 y 2).

## Qué incluye

- **Inicio de sesión real** contra `POST /api/v1/auth/login`; el token JWT se guarda **en memoria** y se envía en `Authorization: Bearer` en cada petición.
- **Flujo principal del MVP** sobre el recurso *sensores*: listar, ver detalle, crear y eliminar.
- **Estados de interfaz**: cargando, vacío, error y éxito.
- **Manejo de errores**: 401 → vuelve al inicio de sesión; 403 → muestra mensaje de permiso insuficiente.
- **Arquitectura por capas**: la vista no llama a la API directamente.
  - `js/app.js` — controlador/vista (navegador).
  - `js/sensores.js` — `SensoresViewModel` (estado de pantalla, lógica pura y testeable).
  - `js/repositorio.js` — `SensorRepositorio` (acceso al recurso).
  - `js/auth.js` — `AuthService` (login, registro, logout).
  - `js/api.js` — `HttpClient` (cliente HTTP, token, manejo de 401/403).
  - `js/config.js` — URL del backend (configuración, no escrita en la lógica).
  - `js/estados.js` — helpers de estados de interfaz.

## Cómo ejecutarlo en local

1. **Arranca el backend** (desde la raíz del repo) en el puerto 8000, autorizando el origen del cliente:

   ```bash
   export AGRODECIDE_JWT_SECRET="$(openssl rand -hex 32)"
   export AGRODECIDE_DB_PATH=agrodecide.sqlite3
   export AGRODECIDE_CORS_ORIGINS=http://127.0.0.1:8080
   python3 -m agrodecide crear-admin admin@example.invalid   # crea un administrador
   python3 -m agrodecide servir                              # API en http://127.0.0.1:8000
   ```

2. **Sirve el cliente** en el puerto 8080 (en otra terminal, dentro de `frontend/`):

   ```bash
   cd frontend
   python3 -m http.server 8080
   ```

3. Abre **http://127.0.0.1:8080** en el navegador.
   - Inicia sesión con el administrador creado (puede listar y **crear** sensores).
   - O usa **Crear cuenta** para registrar un agricultor (podrá listar y ver, pero al crear recibirá **403**, que el cliente muestra como mensaje de permiso).

> Si cambias el puerto del backend, ajusta `js/config.js` (o define `window.AGRO_BACKEND_URL` antes de cargar los scripts) y el valor de `AGRODECIDE_CORS_ORIGINS`.

## Pruebas del cliente

Requiere Node 18+ (usa el runner integrado `node:test` y un doble de `fetch`; no instala nada).

```bash
# desde la raíz del repo
node --test frontend/tests/*.test.js
```

- `tests/auth.test.js` — 3 pruebas unitarias de la lógica de presentación (ViewModel): lista vacía → estado vacío, error de red → estado error, lista con datos → estado éxito.
- `tests/api.test.js` — 3 pruebas de integración del cliente HTTP (con interceptor de `fetch`): respuesta 200 bien mapeada, 401 manejado, token adjuntado en `Authorization`.
