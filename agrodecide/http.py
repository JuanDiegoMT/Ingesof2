"""Controlador WSGI y traducción uniforme de errores a HTTP."""
from http import HTTPStatus
import json
import logging
from pathlib import Path
import re
from urllib.parse import parse_qs

from .dominio import ErrorAPI, entrada_invalida

PREFIJO = "/api/v1"
RUTA_RECURSO = re.compile(PREFIJO + r"/(sensores|mediciones)(?:/([^/]+))?")
LIMITE_JSON = 16_384
ARCHIVO_OPENAPI = Path(__file__).resolve().parent.parent / "openapi.yaml"


def entero(valor, minimo, maximo):
    if not re.fullmatch(r"[0-9]{1,19}", valor) or not minimo <= int(valor) <= maximo:
        raise entrada_invalida(f"Se esperaba un entero entre {minimo} y {maximo}.")
    return int(valor)


def leer_json(env):
    if env.get("CONTENT_TYPE", "").partition(";")[0].strip().lower() != "application/json":
        raise entrada_invalida("Se requiere Content-Type application/json.")
    longitud = entero(env.get("CONTENT_LENGTH", ""), 1, LIMITE_JSON)
    try:
        datos = json.loads(env["wsgi.input"].read(longitud).decode("utf-8"))
        json.dumps(datos, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, RecursionError):
        raise entrada_invalida("El cuerpo debe contener JSON UTF-8 válido.") from None
    if not isinstance(datos, dict):
        raise entrada_invalida("El cuerpo debe ser un objeto JSON.")
    return datos


def paginacion(env, tabla):
    permitidos = {"limite", "desplazamiento"}
    if tabla == "mediciones":
        permitidos.add("sensor_id")
    try:
        parametros = parse_qs(env.get("QUERY_STRING", ""), keep_blank_values=True, max_num_fields=len(permitidos))
    except ValueError:
        raise entrada_invalida("Parámetros permitidos: " + ", ".join(sorted(permitidos))) from None
    if parametros.keys() - permitidos or any(
        len(valor) != 1 for valor in parametros.values()
    ):
        raise entrada_invalida("Parámetros permitidos: " + ", ".join(sorted(permitidos)))
    return (
        entero(parametros.get("limite", ["50"])[0], 1, 200),
        entero(parametros.get("desplazamiento", ["0"])[0], 0, 2**63 - 1),
        entero(parametros["sensor_id"][0], 1, 2**63 - 1) if "sensor_id" in parametros else None,
    )


class ControladorHTTP:
    def __init__(self, identidad, monitoreo, origenes):
        self.identidad = identidad
        self.monitoreo = monitoreo
        self.origenes = origenes

    def despachar(self, env):
        metodo = env["REQUEST_METHOD"]
        ruta = env["PATH_INFO"]
        if ruta == "/openapi.yaml" and metodo == "GET":
            return 200, ARCHIVO_OPENAPI.read_bytes(), [("Content-Type", "application/yaml")]
        if ruta == PREFIJO + "/auth/registro" and metodo == "POST":
            return 201, self.identidad.registrar(leer_json(env)), []
        if ruta == PREFIJO + "/auth/login" and metodo == "POST":
            return 200, self.identidad.iniciar_sesion(leer_json(env)), []
        if ruta == PREFIJO + "/mi-perfil" and metodo == "GET":
            usuario = self.identidad.autenticar(env.get("HTTP_AUTHORIZATION", ""))
            self.identidad.autorizar(usuario, "agricultor")
            return 200, usuario, []
        recurso = RUTA_RECURSO.fullmatch(ruta)
        if recurso is None:
            raise ErrorAPI(404, "ruta_inexistente", "La ruta solicitada no existe.")
        tabla, id_recibido = recurso.groups()
        usuario = self.identidad.autenticar(env.get("HTTP_AUTHORIZATION", ""))
        permitido = {"GET", "POST"} if id_recibido is None else {"GET", "PUT", "DELETE"}
        if metodo not in permitido:
            raise ErrorAPI(405, "metodo_no_permitido", "El método no está disponible en esta ruta.")
        identificador = None if id_recibido is None else entero(id_recibido, 1, 2**63 - 1)
        if metodo == "GET":
            if identificador is None:
                return 200, self.monitoreo.listar(tabla, *paginacion(env, tabla)), []
            return 200, self.monitoreo.obtener(tabla, identificador), []
        self.identidad.autorizar(usuario, "administrador")
        if metodo == "DELETE":
            self.monitoreo.eliminar(tabla, identificador)
            return 204, None, []
        recurso = self.monitoreo.guardar(tabla, leer_json(env), identificador)
        if metodo == "POST":
            return 201, recurso, [("Location", f"{ruta}/{recurso['id']}")]
        return 200, recurso, []

    def __call__(self, env, start_response):
        origen = env.get("HTTP_ORIGIN")
        encabezados = [("Vary", "Origin"), ("Cache-Control", "no-store"),
                       ("X-Content-Type-Options", "nosniff")]
        if origen in self.origenes:
            encabezados.append(("Access-Control-Allow-Origin", origen))
        try:
            if env["REQUEST_METHOD"] == "OPTIONS" and "HTTP_ACCESS_CONTROL_REQUEST_METHOD" in env:
                if origen not in self.origenes:
                    raise ErrorAPI(403, "origen_denegado", "El origen no está autorizado.")
                estado, datos, extras = 204, None, [
                    ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
                    ("Access-Control-Allow-Headers", "Authorization, Content-Type"),
                ]
            else:
                estado, datos, extras = self.despachar(env)
        except ErrorAPI as error:
            estado, datos = error.estado, {"error": {"codigo": error.codigo, "mensaje": str(error)}}
            extras = [("WWW-Authenticate", "Bearer")] if estado == 401 else []
            if estado == 405:
                coincidencia = RUTA_RECURSO.fullmatch(env["PATH_INFO"])
                extras.append(("Allow", "GET, PUT, DELETE" if coincidencia.group(2) else "GET, POST"))
        except Exception:
            logging.exception("Error interno al atender la solicitud")
            estado, datos, extras = 500, {
                "error": {"codigo": "error_interno", "mensaje": "No se pudo atender la solicitud."}
            }, []
        encabezados.extend(extras)
        if datos is None:
            cuerpo = b""
        elif isinstance(datos, bytes):
            cuerpo = datos
        else:
            cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
            encabezados.append(("Content-Type", "application/json; charset=utf-8"))
        encabezados.append(("Content-Length", str(len(cuerpo))))
        start_response(f"{estado} {HTTPStatus(estado).phrase}", encabezados)
        return [cuerpo]
