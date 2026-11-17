"""Pruebas de integración del contrato HTTP en WSGI con SQLite temporal."""
from contextlib import closing
from io import BytesIO
import json
import os
from pathlib import Path
import secrets
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator

from agrodecide.__main__ import crear_app


class PruebasAPI(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.db_path = Path(temporal.name) / "integracion.sqlite3"
        config = {
            "AGRODECIDE_DB_PATH": str(self.db_path),
            "AGRODECIDE_JWT_SECRET": secrets.token_hex(32),
            "AGRODECIDE_CORS_ORIGINS": "http://127.0.0.1:8080",
        }
        with patch.dict(os.environ, config):
            self.app = crear_app()
        self.wsgi = validator(self.app)
        self.agricultor = {"correo": "agricultor@example.invalid", "contrasena": secrets.token_hex(12)}
        self.admin = {"correo": "admin@example.invalid", "contrasena": secrets.token_hex(12)}
        self.app.identidad.registrar(self.admin, "administrador")

    def solicitar(self, metodo, ruta, esperado, datos=None, token=None, headers=None):
        headers = dict(headers or {})
        if datos is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        cuerpo = json.dumps(datos).encode() if datos is not None else b""
        url = urlsplit(ruta if ruta == "/openapi.yaml" else "/api/v1" + ruta)
        env = {
            "REQUEST_METHOD": metodo, "PATH_INFO": url.path, "QUERY_STRING": url.query, "SCRIPT_NAME": "",
            "CONTENT_LENGTH": str(len(cuerpo)), "wsgi.input": BytesIO(cuerpo),
        }
        for clave, valor in headers.items():
            nombre = clave.upper().replace("-", "_")
            env[nombre if nombre == "CONTENT_TYPE" else "HTTP_" + nombre] = valor
        setup_testing_defaults(env)
        respuesta = {}

        def iniciar(estado, encabezados, exc_info=None):
            respuesta.update(estado=int(estado.split()[0]), encabezados=dict(encabezados))

        with closing(self.wsgi(env, iniciar)) as iterable:
            binario = b"".join(iterable)
        self.assertEqual(respuesta["estado"], esperado, binario.decode())
        encabezados = respuesta["encabezados"]
        if encabezados.get("Content-Type", "").startswith("application/json"):
            datos = json.loads(binario)
        else:
            datos = binario
        if esperado >= 400:
            self.assertEqual(set(datos), {"error"})
            self.assertEqual(set(datos["error"]), {"codigo", "mensaje"})
        return datos, encabezados

    def token(self, credenciales):
        respuesta, _ = self.solicitar("POST", "/auth/login", 200, credenciales)
        self.assertEqual(respuesta["token_type"], "Bearer")
        self.assertEqual(respuesta["expires_in"], 900)
        return respuesta["access_token"]

    def alta_agricultor(self):
        datos, _ = self.solicitar("POST", "/auth/registro", 201, self.agricultor)
        self.assertEqual(datos["rol"], "agricultor")
        return self.token(self.agricultor)

    def test_registro_login_hash_y_duplicados(self):
        self.alta_agricultor()
        self.solicitar("POST", "/auth/registro", 409, self.agricultor)
        self.solicitar("POST", "/auth/registro", 400, {**self.agricultor, "rol": "administrador"})
        self.solicitar("POST", "/auth/login", 401, {**self.agricultor, "contrasena": "contraseña incorrecta"})
        with closing(sqlite3.connect(self.db_path)) as db:
            hashes = db.execute("SELECT hash FROM usuarios").fetchall()
        self.assertEqual(len(hashes), 2)
        self.assertTrue(all(fila[0].startswith("$argon2id$") for fila in hashes))
        for hash_guardado, in hashes:
            self.assertNotIn(self.agricultor["contrasena"], hash_guardado)
            self.assertNotIn(self.admin["contrasena"], hash_guardado)

    def test_401_403_y_endpoints_exclusivos(self):
        agricultor = self.alta_agricultor()
        admin = self.token(self.admin)
        _, respuesta = self.solicitar("GET", "/sensores", 401)
        self.assertEqual(respuesta.get("WWW-Authenticate"), "Bearer")
        self.solicitar("GET", "/mi-perfil", 200, token=agricultor)
        self.solicitar("GET", "/mi-perfil", 403, token=admin)
        antes, _ = self.solicitar("GET", "/sensores", 200, token=agricultor)
        sensor_valido = {"nombre": "Sonda A", "ubicacion": "Parcela A", "profundidad_cm": 15}
        self.solicitar("POST", "/sensores", 403, sensor_valido, agricultor)
        despues, _ = self.solicitar("GET", "/sensores", 200, token=agricultor)
        self.assertEqual(antes, despues)
        self.solicitar("POST", "/mediciones", 403, {}, agricultor)

    def test_vencimiento_jwt(self):
        with patch("agrodecide.seguridad.time.time", return_value=1000):
            admin = self.token(self.admin)
        with patch("agrodecide.seguridad.time.time", return_value=1900):
            self.solicitar("GET", "/sensores", 401, token=admin)

    def test_crud_y_consistencia_sensor_medicion(self):
        agricultor = self.alta_agricultor()
        admin = self.token(self.admin)
        modelo = {"nombre": "Sonda A", "ubicacion": "Parcela A", "profundidad_cm": 15}
        sensor, respuesta = self.solicitar("POST", "/sensores", 201, modelo, admin)
        ruta = "/sensores/" + str(sensor["id"])
        self.assertEqual(respuesta.get("Location"), "/api/v1" + ruta)
        listado, _ = self.solicitar("GET", "/sensores?limite=1", 200, token=agricultor)
        self.assertEqual(listado, [sensor])
        consultado, _ = self.solicitar("GET", ruta, 200, token=agricultor)
        self.assertEqual(consultado, sensor)
        sensor, _ = self.solicitar("PUT", ruta, 200, {**modelo, "profundidad_cm": 20}, admin)
        self.assertEqual(sensor["profundidad_cm"], 20)
        datos = {"sensor_id": sensor["id"], "instante": "2026-11-10T08:00:00-05:00", "humedad_pct": 32.5}
        self.solicitar("POST", "/mediciones", 400, {**datos, "humedad_pct": 105}, admin)
        self.solicitar("POST", "/mediciones", 404, {**datos, "sensor_id": 999}, admin)
        medicion, _ = self.solicitar("POST", "/mediciones", 201, datos, admin)
        self.assertEqual(medicion["instante"], "2026-11-10T13:00:00.000000Z")
        self.solicitar("POST", "/mediciones", 409, {**datos, "instante": medicion["instante"]}, admin)
        ruta_medicion = "/mediciones/" + str(medicion["id"])
        listado, _ = self.solicitar("GET", f"/mediciones?sensor_id={sensor['id']}", 200, token=agricultor)
        self.assertEqual(listado, [medicion])
        otro, _ = self.solicitar("GET", "/mediciones?sensor_id=999", 200, token=agricultor)
        self.assertEqual(otro, [])
        consultada, _ = self.solicitar("GET", ruta_medicion, 200, token=agricultor)
        self.assertEqual(consultada, medicion)
        medicion, _ = self.solicitar("PUT", ruta_medicion, 200, {**datos, "humedad_pct": 38}, admin)
        self.assertEqual(medicion["humedad_pct"], 38)
        self.solicitar("DELETE", ruta, 409, token=admin)
        self.solicitar("DELETE", ruta_medicion, 204, token=admin)
        self.solicitar("GET", ruta_medicion, 404, token=admin)
        self.solicitar("DELETE", ruta, 204, token=admin)
        self.solicitar("GET", ruta, 404, token=admin)

    def test_validacion_y_cors(self):
        admin = self.token(self.admin)
        self.solicitar("POST", "/sensores", 400, {"nombre": "A", "ubicacion": "B", "profundidad_cm": -1}, admin)
        self.solicitar("POST", "/mediciones", 400,
                       {"sensor_id": 1, "instante": "2026-11-10T08:00:00", "humedad_pct": 31}, admin)
        self.solicitar("GET", "/sensores?limite=0", 400, token=admin)
        self.solicitar("GET", "/mediciones?sensor_id=-1", 400, token=admin)
        preflight = {"Origin": "http://127.0.0.1:8080", "Access-Control-Request-Method": "POST"}
        _, respuesta = self.solicitar("OPTIONS", "/sensores", 204, headers=preflight)
        self.assertEqual(respuesta.get("Access-Control-Allow-Origin"), preflight["Origin"])
        _, respuesta = self.solicitar("OPTIONS", "/sensores", 403,
                                      headers={**preflight, "Origin": "https://origen.example.invalid"})
        self.assertIsNone(respuesta.get("Access-Control-Allow-Origin"))

    def test_publicacion_openapi(self):
        cuerpo, respuesta = self.solicitar("GET", "/openapi.yaml", 200)
        self.assertEqual(respuesta.get("Content-Type"), "application/yaml")
        self.assertEqual(cuerpo, Path("openapi.yaml").read_bytes())
