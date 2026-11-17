"""Adapta el archivo público Montería 2025, DOI 10.17632/fn8h5h33ct.1."""

import argparse
import csv
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo

from openpyxl import load_workbook


HUELLA = "7e9b24971a60b1f60941ee75a6e1c4f44d6c8771050c8d7fb9730f45807b2fc7"
ZONA = ZoneInfo("America/Bogota")


def fecha_local(valor):
    if not isinstance(valor, datetime):
        raise ValueError("Se esperaba una fecha de Excel.")
    return valor.replace(tzinfo=ZONA).isoformat(timespec="milliseconds")


def normalizar(origen, salida, solo_sin_comp):
    if sha256(origen.read_bytes()).hexdigest() != HUELLA:
        raise ValueError("El archivo debe coincidir con el SHA-256 de la versión 1.")
    libro = load_workbook(origen, read_only=True, data_only=True)
    registros = []
    resumen = Counter()
    try:
        filas = libro["IoT_Node_Observations"].iter_rows(values_only=True)
        campos = next(filas)
        for valores in filas:
            fila = dict(zip(campos, valores, strict=True))
            if fila["timestamp"] is None:
                continue
            if (fila["device_id"], fila["sensor_node_serial"], fila["plot_id"],
                fila["sensor_depth_cm"]) != (
                "NODE_001", "SN-MON-PLT-2025-001", "PLOT_A01", 20
            ):
                raise ValueError("Identidad inesperada para el canal a 20 cm.")
            marca_comp = "-COMP-" in fila["packet_id_sent"]
            if marca_comp:
                resumen["identificador con COMP"] += 1
            humedad = fila["soil_moisture_vwc_pct"]
            motivo = "lectura retenida"
            if solo_sin_comp and marca_comp:
                motivo = "COMP excluido"
            elif fila["telemetry_available_flag"] != 1:
                motivo = "sin recepción remota"
            elif fila["calibration_status"] != "calibrated":
                motivo = "calibración pendiente"
            elif humedad is None or not 0 <= humedad <= 100:
                motivo = "humedad faltante o fuera de rango"
            resumen[motivo] += 1

            instante = fecha_local(fila["timestamp"])
            recibido = None
            if motivo == "lectura retenida":
                recibido = fecha_local(fila["platform_received_timestamp"])
            else:
                humedad = None
            registros.append((instante, "NODE_001", 20, humedad, recibido))
    finally:
        libro.close()

    with salida.open("w", encoding="utf-8", newline="") as destino:
        escritor = csv.writer(destino)
        escritor.writerow(
            ("timestamp", "sensor_id", "profundidad_cm", "humedad_pct_vwc", "recibido_en")
        )
        escritor.writerows(registros)
    print(f"Filas: {len(registros)}.")
    for motivo, cantidad in resumen.items():
        print(f"{motivo}: {cantidad}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origen", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--solo-sin-comp", action="store_true")
    args = parser.parse_args()
    if args.origen.resolve() == args.salida.resolve():
        parser.error("La salida debe ser distinta del archivo original.")
    try:
        normalizar(args.origen, args.salida, args.solo_sin_comp)
    except (OSError, ValueError) as error:
        parser.exit(2, f"Entrada inválida: {error}\n")


if __name__ == "__main__":
    main()
