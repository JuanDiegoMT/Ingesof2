# AgroDecide · Prototipo 1

AgroDecide es un proyecto académico de Ingeniería de Software II en la Universidad Nacional de Colombia, sede Bogotá. La API prototipo administra sensores y mediciones de humedad del suelo, con autenticación JWT y autorización por roles. El [informe académico](docs/ENTREGA_PROTOTIPO_1.md) documenta el diseño para previsiones de humedad y precios, consultas agrícolas y un asistente local.

[Repositorio de entrega](https://github.com/JuanDiegoMT/Ingesof2)

**Integrantes y grupo** · Pendientes de confirmación por el equipo.

## Tecnologías

- Python 3.11 o posterior y servidor WSGI de la biblioteca estándar.
- SQLite embebido, con una base local y restricciones relacionales.
- Argon2id mediante la biblioteca compartida del sistema `libargon2`.
- JWT HS256, OpenAPI 3.0.3 y colección Postman 2.1.

## Ejecutar el backend en local

Desde el directorio que contiene este README, compruebe los requisitos.

```bash
python3 --version
python3 -c 'from ctypes.util import find_library; print(find_library("argon2"))'
```

Si la segunda instrucción imprime `None`, instale el paquete de su distribución que proporciona `libargon2`. Por ejemplo, Fedora utiliza `libargon2` y Debian/Ubuntu utilizan `libargon2-1`. La API usa un archivo SQLite y no requiere un proceso de base de datos aparte.

Configure el entorno de la sesión y arranque el servidor.

```bash
export AGRODECIDE_JWT_SECRET="$(openssl rand -hex 32)"
export AGRODECIDE_DB_PATH=agrodecide.sqlite3
export AGRODECIDE_CORS_ORIGINS=http://127.0.0.1:8080
python3 -m agrodecide crear-admin admin@example.invalid
python3 -m agrodecide servir
```

El comando `crear-admin` solicita dos veces la contraseña y requiere entre 12 y 128 caracteres. La cuenta persiste en el archivo SQLite. Ejecute el comando una sola vez por cuenta y ejecute el servidor con la misma ruta de base de datos. La API queda disponible en `http://127.0.0.1:8000`. Use `servir --puerto 8081` si 8000 está ocupado y ajuste `base_url` en la colección.

| Variable | Función | Ejemplo |
| --- | --- | --- |
| `AGRODECIDE_JWT_SECRET` | Clave de firma requerida, de al menos 32 bytes. | Genere un valor aleatorio con `openssl rand -hex 32`. |
| `AGRODECIDE_DB_PATH` | Ruta a un archivo local SQLite en un directorio escribible. | `agrodecide.sqlite3` |
| `AGRODECIDE_CORS_ORIGINS` | Orígenes exactos separados por comas. Vacío desactiva acceso desde otros orígenes en navegador. | `http://127.0.0.1:8080` |

[Plantilla de variables](.env.example). El proceso lee variables exportadas en el entorno. Use HTTP únicamente para las pruebas en loopback. Los pasos previstos para una exposición por red están en la sección 4(f) del informe.

## API, pruebas y prototipos de interfaz

- [Contrato OpenAPI](openapi.yaml) y [descarga desde la API en ejecución](http://127.0.0.1:8000/openapi.yaml).
- [Colección Postman](postman/AgroDecide.postman_collection.json). Importe el archivo, configure `base_url` y los valores locales `correo_admin` y `contrasena_admin` de una cuenta creada por CLI. Ejecute toda la colección en orden, con una base desechable. Los recursos de prueba se eliminan al final y la cuenta agricultora aleatoria queda en dicha base.
- [Wireframes adaptables](docs/wireframes.html). Abra el archivo en el navegador para consultar los diseños web y móvil identificados en cada pantalla. El enlace público de solo lectura está pendiente.
- GitHub Projects · Enlace pendiente de creación o confirmación por el equipo.

Ejecute la integración del controlador WSGI, los casos de uso y SQLite con una base temporal.

```bash
python3 -m unittest discover -s tests -v
```

[Resultados y pasos de verificación](docs/EVIDENCIA_API.md).
