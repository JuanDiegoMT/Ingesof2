# Evidencia de la API de AgroDecide

Verificación realizada el 17 de noviembre de 2026. Se usaron archivos SQLite temporales, credenciales sintéticas generadas para la prueba y HTTP limitado a loopback. La colección contiene datos sintéticos de demostración.

## Resultados reproducibles

| Comprobación | Herramienta | Resultado |
| --- | --- | --- |
| Integración de controlador, aplicación y SQLite | `python3 -m unittest discover -s tests -v` | Seis pruebas aprobadas. |
| Puerto HTTP local y recorrido mínimo | Servidor WSGI y cliente de la biblioteca estándar | Cinco respuestas correctas. Registro 201, login 200, listado sin token 401, listado con token 200, escritura con rol agricultor 403. |
| Especificación del contrato | openapi-spec-validator 0.9.0 | `openapi.yaml: OK` para OpenAPI 3.0.3. Swagger Editor 4.14.8 obtuvo cero diagnósticos en Firefox local. [Captura](evidencias/swagger-editor.png) |
| Colección Postman exportada en CLI | Newman 6.2.3 | Una iteración, 22 solicitudes, 22 scripts de prueba, dos scripts previos y 40 aserciones. Cero fallos y código de salida 0. |

[Registro depurado de Newman](evidencias/newman.txt).

La primera prueba de socket en el entorno restringido devolvió `PermissionError`. La integración WSGI se ejecutó en proceso y las comprobaciones HTTP posteriores se ejecutaron con permiso de loopback. Newman es el ejecutor CLI de colecciones Postman. La sesión gráfica del Collection Runner queda pendiente. [Resumen depurado de Newman](evidencias/newman.txt).

## Matriz de la ejecución en Newman

| Prueba | Resultado esperado | Resultado observado | Estado |
| --- | --- | --- | --- |
| Registrar agricultor | 201, rol agricultor | 201, rol agricultor | Aprobada |
| Login agricultor | 200, token con vigencia 900 s | 200, vigencia 900 s | Aprobada |
| Login administrador | 200, token reutilizable | 200, token aceptado en escrituras | Aprobada |
| Listado sin token | 401, error uniforme | 401, error uniforme | Aprobada |
| Consultar perfil como agricultor | 200, rol agricultor | 200, rol agricultor | Aprobada |
| Consultar perfil como administrador | 403, error uniforme | 403, error uniforme | Aprobada |
| Crear sensor como agricultor | 403, error uniforme | 403, error uniforme | Aprobada |
| Crear sensor con profundidad inválida | 400, error uniforme | 400, error uniforme | Aprobada |
| Crear, listar, obtener y reemplazar sensor | 201 y tres respuestas 200 | 201, 200, 200, 200 | Aprobada |
| Crear, listar, obtener y reemplazar medición | 201 y tres respuestas 200 | 201, 200, 200, 200 | Aprobada |
| Duplicar una medición | 409, error uniforme | 409, error uniforme | Aprobada |
| Borrar un sensor con mediciones | 409, error uniforme | 409, error uniforme | Aprobada |
| Borrar y volver a consultar una medición | 204 y 404 | 204 y 404 | Aprobada |
| Borrar y volver a consultar un sensor | 204 y 404 | 204 y 404 | Aprobada |

La suite WSGI comprobó adicionalmente los prefijos de hash Argon2id en SQLite, el rechazo de credenciales incorrectas, el vencimiento exacto del JWT, el catálogo sin cambios tras un 403 con cuerpo válido, el rechazo de humedad superior al 100 %, la referencia a sensor inexistente, CORS y la correspondencia byte a byte entre el YAML publicado y el archivo.

## Repetición local

1. Siga [los pasos del README](../README.md) usando una ruta SQLite temporal. Cree la cuenta administrativa antes de iniciar la API.
2. Importe [la colección](../postman/AgroDecide.postman_collection.json) en Postman o ejecute Newman desde una instalación local. Configure `base_url`, `correo_admin` y `contrasena_admin` en un entorno de ejecución privado, sin exportarlo al repositorio.
3. Ejecute los 22 pasos en orden con el Collection Runner o con `newman run postman/AgroDecide.postman_collection.json -e /ruta/al/entorno-local.json`.
4. Compruebe la especificación con `openapi-spec-validator openapi.yaml` y abra el mismo YAML en Swagger Editor. Para esta verificación el archivo tuvo SHA-256 `f9799882d228e4120177fa0894f279a0b162b5376149f3e8a75e222b4aadaea3`. Un control que omitió `info.title` produjo el diagnóstico estructural esperado.

Los tiempos de Newman corresponden a una ejecución con una carga pequeña y secuencial. La prueba de concurrencia y latencia p95 requiere el escenario de carga descrito en el informe.
