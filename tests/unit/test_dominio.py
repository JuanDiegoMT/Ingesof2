"""Pruebas unitarias del dominio: entidades, validaciones y reglas (estructura AAA)."""
import unittest

from agrodecide.dominio import ErrorAPI, Medicion, Sensor, validar_credenciales

SENSOR = {"nombre": "Sonda A", "ubicacion": "Parcela A", "profundidad_cm": 15}
MEDICION = {"sensor_id": 1, "instante": "2026-11-10T08:00:00-05:00", "humedad_pct": 32.5}


class PruebasSensor(unittest.TestCase):
    def test_desdeJson_datosValidos_creaSensorNormalizado(self):
        sensor = Sensor.desde_json({**SENSOR, "nombre": "  Sonda A  "})
        self.assertEqual(sensor, Sensor("Sonda A", "Parcela A", 15.0))

    def test_desdeJson_profundidadMinimaExacta_seAcepta(self):
        self.assertEqual(Sensor.desde_json({**SENSOR, "profundidad_cm": 0.1}).profundidad_cm, 0.1)

    def test_desdeJson_profundidadBajoElMinimo_lanza400(self):
        with self.assertRaises(ErrorAPI) as ctx:
            Sensor.desde_json({**SENSOR, "profundidad_cm": 0.09})
        self.assertEqual((ctx.exception.estado, ctx.exception.codigo), (400, "entrada_invalida"))

    def test_desdeJson_campoExtra_lanza400(self):
        with self.assertRaises(ErrorAPI):
            Sensor.desde_json({**SENSOR, "id": 5})


class PruebasMedicion(unittest.TestCase):
    def test_desdeJson_instanteConZona_seNormalizaAUtc(self):
        medicion = Medicion.desde_json(MEDICION)
        self.assertEqual(medicion.instante, "2026-11-10T13:00:00.000000Z")

    def test_desdeJson_humedadEnLosLimites_seAcepta(self):
        self.assertEqual(Medicion.desde_json({**MEDICION, "humedad_pct": 0}).humedad_pct, 0.0)
        self.assertEqual(Medicion.desde_json({**MEDICION, "humedad_pct": 100}).humedad_pct, 100.0)

    def test_desdeJson_humedadSobre100_lanza400(self):
        with self.assertRaises(ErrorAPI):
            Medicion.desde_json({**MEDICION, "humedad_pct": 100.01})

    def test_desdeJson_instanteSinZonaHoraria_lanza400(self):
        with self.assertRaises(ErrorAPI):
            Medicion.desde_json({**MEDICION, "instante": "2026-11-10T08:00:00"})

    def test_desdeJson_sensorIdBooleano_lanza400(self):
        # bool es subclase de int: no debe colarse como identificador.
        with self.assertRaises(ErrorAPI):
            Medicion.desde_json({**MEDICION, "sensor_id": True})


class PruebasValidadores(unittest.TestCase):

    def test_validarCredenciales_contrasenaDe11Caracteres_lanza400(self):
        with self.assertRaises(ErrorAPI):
            validar_credenciales({"correo": "a@b.co", "contrasena": "x" * 11})


if __name__ == "__main__":
    unittest.main()
