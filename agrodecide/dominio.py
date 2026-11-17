"""Reglas y datos de la API de monitoreo."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re


class ErrorAPI(Exception):
    def __init__(self, estado, codigo, mensaje):
        super().__init__(mensaje)
        self.estado = estado
        self.codigo = codigo


def entrada_invalida(mensaje):
    return ErrorAPI(400, "entrada_invalida", mensaje)


def validar_campos(datos, esperados):
    if datos.keys() != esperados:
        raise entrada_invalida("Campos requeridos: " + ", ".join(sorted(esperados)))


def validar_texto(valor, campo, maximo):
    if not isinstance(valor, str) or not 1 <= len(valor.strip()) <= maximo:
        raise entrada_invalida(f"{campo} debe contener entre 1 y {maximo} caracteres.")
    return valor.strip()


def validar_numero(valor, campo, minimo, maximo):
    if type(valor) not in (int, float) or not minimo <= valor <= maximo:
        raise entrada_invalida(f"{campo} debe estar entre {minimo} y {maximo}.")
    return float(valor)


@dataclass(frozen=True)
class Sensor:
    nombre: str
    ubicacion: str
    profundidad_cm: float

    @classmethod
    def desde_json(cls, datos):
        validar_campos(datos, {"nombre", "ubicacion", "profundidad_cm"})
        return cls(
            validar_texto(datos["nombre"], "nombre", 80),
            validar_texto(datos["ubicacion"], "ubicacion", 120),
            validar_numero(datos["profundidad_cm"], "profundidad_cm", 0.1, 1000),
        )


@dataclass(frozen=True)
class Medicion:
    sensor_id: int
    instante: str
    humedad_pct: float

    @classmethod
    def desde_json(cls, datos):
        validar_campos(datos, {"sensor_id", "instante", "humedad_pct"})
        sensor_id = datos["sensor_id"]
        if type(sensor_id) is not int or not 1 <= sensor_id <= 2**63 - 1:
            raise entrada_invalida("sensor_id debe ser un entero positivo válido.")
        instante = datos["instante"]
        formato = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)"
        try:
            if not isinstance(instante, str) or not re.fullmatch(formato, instante):
                raise ValueError
            fecha = datetime.fromisoformat(instante).astimezone(timezone.utc)
        except (ValueError, OverflowError):
            raise entrada_invalida("instante debe ser una fecha RFC 3339 con zona horaria.") from None
        return cls(
            sensor_id, fecha.isoformat(timespec="microseconds").replace("+00:00", "Z"),
            validar_numero(datos["humedad_pct"], "humedad_pct", 0, 100),
        )


def validar_credenciales(datos):
    validar_campos(datos, {"correo", "contrasena"})
    correo = validar_texto(datos["correo"], "correo", 254).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
        raise entrada_invalida("correo debe tener un formato de correo válido.")
    contrasena = datos["contrasena"]
    if not isinstance(contrasena, str) or not 12 <= len(contrasena) <= 128:
        raise entrada_invalida("contrasena debe tener entre 12 y 128 caracteres.")
    return correo, contrasena
