"""Casos de uso con dobles de prueba: se verifican interacciones, no SQLite."""
import unittest
from unittest.mock import MagicMock

from agrodecide.aplicacion import Identidad, Monitoreo
from agrodecide.dominio import ErrorAPI

SENSOR = {"nombre": "Sonda A", "ubicacion": "Parcela A", "profundidad_cm": 15}
CREDENCIALES = {"correo": "ana@example.com", "contrasena": "una-clave-larga-123"}


def identidad_con_dobles(usuario=None):
    repositorio, contrasenas, tokens = MagicMock(), MagicMock(), MagicMock()
    contrasenas.generar.return_value = "hash-ficticio"
    repositorio.usuario_por_correo.return_value = usuario
    return Identidad(repositorio, contrasenas, tokens), repositorio, contrasenas, tokens


class PruebasMonitoreo(unittest.TestCase):
    def test_guardar_datosInvalidos_noTocaElRepositorio(self):
        repositorio = MagicMock()
        servicio = Monitoreo(repositorio)
        with self.assertRaises(ErrorAPI):
            servicio.guardar("sensores", {**SENSOR, "profundidad_cm": -1})
        repositorio.guardar.assert_not_called()

    def test_guardar_datosValidos_delegaUnaVezConElRecursoDeDominio(self):
        repositorio = MagicMock()
        repositorio.guardar.return_value = {"id": 7, **SENSOR}
        resultado = Monitoreo(repositorio).guardar("sensores", SENSOR, 7)
        (tabla, recurso, identificador), _ = repositorio.guardar.call_args
        self.assertEqual((tabla, identificador, recurso.nombre), ("sensores", 7, "Sonda A"))
        self.assertEqual(resultado["id"], 7)


class PruebasIdentidad(unittest.TestCase):

    def test_iniciarSesion_contrasenaIncorrecta_401SinEmitirToken(self):
        identidad, _, contrasenas, tokens = identidad_con_dobles({"id": 1, "hash": "h", "rol": "agricultor"})
        contrasenas.verificar.return_value = False
        with self.assertRaises(ErrorAPI) as ctx:
            identidad.iniciar_sesion(CREDENCIALES)
        self.assertEqual(ctx.exception.codigo, "credenciales_invalidas")
        tokens.emitir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
