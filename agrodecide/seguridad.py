"""Hash Argon2id y tokens de acceso firmados para el servidor local."""
import base64
import binascii
from ctypes import CDLL, c_char_p, c_int, c_size_t, c_uint32, create_string_buffer
from ctypes.util import find_library
import hashlib
import hmac
import json
import secrets
import time

from .dominio import ErrorAPI


class HashArgon2:
    def __init__(self):
        biblioteca = find_library("argon2")
        if not biblioteca:
            raise RuntimeError("Se requiere la biblioteca del sistema libargon2.")
        argon2 = CDLL(biblioteca)
        self.codificar = argon2.argon2id_hash_encoded
        self.codificar.argtypes = [
            c_uint32, c_uint32, c_uint32, c_char_p, c_size_t,
            c_char_p, c_size_t, c_size_t, c_char_p, c_size_t,
        ]
        self.codificar.restype = c_int
        self.comprobar = argon2.argon2id_verify
        self.comprobar.argtypes = [c_char_p, c_char_p, c_size_t]
        self.comprobar.restype = c_int

    def generar(self, contrasena):
        valor = contrasena.encode()
        sal = secrets.token_bytes(16)
        salida = create_string_buffer(256)
        resultado = self.codificar(
            2, 19456, 1, valor, len(valor), sal, len(sal), 32, salida, len(salida)
        )
        if resultado:
            raise RuntimeError("No se pudo calcular el hash Argon2id.")
        return salida.value.decode("ascii")

    def verificar(self, contrasena, hash_guardado):
        valor = contrasena.encode()
        return self.comprobar(hash_guardado.encode("ascii"), valor, len(valor)) == 0


def formato_base64(datos):
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def json_base64(datos):
    return formato_base64(json.dumps(datos, separators=(",", ":")).encode())


def leer_base64(segmento):
    return base64.b64decode(segmento + "=" * (-len(segmento) % 4), altchars=b"-_", validate=True)


class Tokens:
    vigencia = 900
    encabezado = json_base64({"alg": "HS256", "typ": "JWT"})

    def __init__(self, clave):
        if len(clave.encode()) < 32:
            raise ValueError("AGRODECIDE_JWT_SECRET requiere al menos 32 bytes.")
        self.clave = clave.encode()

    def firma(self, mensaje):
        return formato_base64(hmac.digest(self.clave, mensaje.encode("ascii"), hashlib.sha256))

    def emitir(self, usuario_id):
        ahora = int(time.time())
        datos = json_base64({
            "iss": "agrodecide", "aud": "agrodecide-api", "sub": str(usuario_id),
            "iat": ahora, "exp": ahora + self.vigencia,
        })
        mensaje = self.encabezado + "." + datos
        return {"access_token": mensaje + "." + self.firma(mensaje),
                "token_type": "Bearer", "expires_in": self.vigencia}

    def validar(self, autorizacion):
        try:
            esquema, token = autorizacion.split()
            if esquema.lower() != "bearer" or len(token) > 2048:
                raise ValueError
            encabezado, datos, firma = token.split(".")
            if encabezado != self.encabezado or not hmac.compare_digest(
                firma, self.firma(encabezado + "." + datos)
            ):
                raise ValueError
            contenido = json.loads(leer_base64(datos))
            if contenido["iss"] != "agrodecide" or contenido["aud"] != "agrodecide-api":
                raise ValueError
            if not contenido["iat"] <= int(time.time()) < contenido["exp"]:
                raise ValueError
            return int(contenido["sub"])
        except (ValueError, TypeError, KeyError, UnicodeError, binascii.Error):
            raise ErrorAPI(401, "token_invalido", "Se requiere un token de acceso válido.") from None
