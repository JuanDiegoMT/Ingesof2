"""Evaluación cronológica reproducible de las dos series de AgroDecide."""

import argparse
import csv
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from math import isfinite, sqrt
from pathlib import Path
from statistics import linear_regression, mean


HORA = timedelta(hours=1)
DIA = timedelta(days=1)


def metricas(observados, predichos):
    errores = [
        predicho - observado
        for observado, predicho in zip(observados, predichos, strict=True)
    ]
    suma_cuadrados = sum(error**2 for error in errores)
    mae = mean(abs(error) for error in errores)
    rmse = sqrt(suma_cuadrados / len(errores))
    return mae, rmse, mean(errores)


def leer_csv(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as entrada:
        return list(csv.DictReader(entrada))


def evaluar_precios(ruta):
    registros = [
        (date.fromisoformat(fila["fin_semana"]), int(fila["precio_medio_cop_kg"]))
        for fila in leer_csv(ruta)
    ]
    if len(registros) < 8:
        raise ValueError("Se necesitan al menos ocho semanas para el piloto.")
    if any(
        fecha_actual - fecha_anterior != 7 * DIA
        for (fecha_anterior, _), (fecha_actual, _) in zip(registros, registros[1:])
    ):
        raise ValueError("Se requieren semanas consecutivas, ordenadas y sin duplicados.")
    if any(precio <= 0 for _, precio in registros):
        raise ValueError("Los precios deben ser positivos.")

    # Se fijan cinco semanas iniciales por diseño. En cada origen se reajusta
    # AR(1) con los pares de precios disponibles hasta esa semana.
    precios = [precio for _, precio in registros]
    persistencia, autorregresion = [], []
    print("Semana objetivo | Observado | Persistencia | AR(1)")
    for indice in range(5, len(registros)):
        anteriores = precios[:indice]
        if min(anteriores[:-1]) == max(anteriores[:-1]):
            prediccion = mean(anteriores[1:])
        else:
            pendiente, intercepto = linear_regression(
                anteriores[:-1], anteriores[1:]
            )
            prediccion = max(0, intercepto + pendiente * anteriores[-1])
        persistencia.append(anteriores[-1])
        autorregresion.append(prediccion)
        print(f"{registros[indice][0]} | {precios[indice]} | "
              f"{persistencia[-1]} | {prediccion:.2f}")
    for modelo, predichos in (
        ("Persistencia", persistencia), ("AR(1)", autorregresion)
    ):
        mae, rmse, sesgo = metricas(precios[5:], predichos)
        print(f"{modelo} (COP/kg): MAE={mae:.2f}, RMSE={rmse:.2f}, sesgo={sesgo:.2f}")


def leer_humedad(ruta):
    mediciones = {}
    identidades = set()
    for fila in leer_csv(ruta):
        profundidad = float(fila["profundidad_cm"])
        sensor = fila["sensor_id"].strip()
        if not sensor or not isfinite(profundidad) or profundidad <= 0:
            raise ValueError("Identificación de sensor o profundidad inválida.")
        identidades.add((sensor, profundidad))
        tiempo = datetime.fromisoformat(fila["timestamp"])
        if tiempo.utcoffset() is None:
            raise ValueError("Se requiere una zona horaria explícita.")
        instante = tiempo.astimezone(UTC)
        if instante.minute or instante.second or instante.microsecond:
            raise ValueError("Se requieren observaciones en una grilla horaria UTC.")
        if instante in mediciones:
            raise ValueError(f"Observación duplicada en {instante}.")
        entrada = fila["humedad_pct_vwc"].strip()
        valor = float(entrada) if entrada else None
        if valor is not None and not 0 <= valor <= 100:
            raise ValueError(f"Humedad volumétrica fuera de rango en {instante}.")
        recibido = fila.get("recibido_en", "").strip()
        disponibilidad = instante
        if recibido:
            fecha_recepcion = datetime.fromisoformat(recibido)
            if fecha_recepcion.utcoffset() is None:
                raise ValueError("Se requiere zona horaria en la recepción.")
            disponibilidad = fecha_recepcion.astimezone(UTC)
            if disponibilidad < instante:
                raise ValueError("La recepción no puede anteceder a la medición.")
        mediciones[instante] = (valor, disponibilidad)
    if len(identidades) != 1:
        raise ValueError("El CSV debe representar un solo sensor a una profundidad.")
    return identidades.pop(), mediciones


def evaluar_humedad(ruta):
    (sensor, profundidad), mediciones = leer_humedad(ruta)
    primero, ultimo = min(mediciones), max(mediciones)
    corte_validacion = primero + ((ultimo - primero) // HORA * 6 // 10) * HORA
    corte_prueba = primero + ((ultimo - primero) // HORA * 8 // 10) * HORA
    particiones = {"entrenamiento": [], "validación": [], "prueba": []}
    inicios_elegibles = 0
    instante = primero + 23 * HORA
    while instante + DIA <= ultimo:
        objetivo = instante + DIA
        grupo = None
        if objetivo < corte_validacion:
            grupo = "entrenamiento"
        elif instante >= corte_validacion and objetivo < corte_prueba:
            grupo = "validación"
        elif instante >= corte_prueba:
            grupo = "prueba"
        if grupo is not None:
            inicios_elegibles += 1
            historico = []
            for atraso in range(24):
                valor, disponibilidad = mediciones.get(
                    instante - atraso * HORA, (None, instante)
                )
                historico.append(valor if disponibilidad <= instante else None)
            recientes = [valor for valor in historico[:3] if valor is not None]
            disponibles = [valor for valor in historico if valor is not None]
            observado = mediciones.get(objetivo, (None, objetivo))[0]
            if len(disponibles) >= 18 and recientes and observado is not None:
                particiones[grupo].append(
                    (objetivo, recientes[0], mean(disponibles), observado)
                )
        instante += HORA
    utilizables = sum(len(filas) for filas in particiones.values())
    cobertura = utilizables / max(1, inicios_elegibles)
    print(f"Sensor: {sensor}, profundidad: {profundidad:g} cm, unidad: % VWC.")
    print(f"Inicios utilizables: {cobertura:.1%} de {inicios_elegibles}. "
          f"Corte validación: {corte_validacion}; corte prueba: {corte_prueba}.")
    if any(len(filas) < 2 for filas in particiones.values()):
        raise ValueError("Cobertura insuficiente en una o más particiones.")

    entrenamiento = particiones["entrenamiento"]
    medias = [media for _, _, media, _ in entrenamiento]
    objetivos = [observado for _, _, _, observado in entrenamiento]
    if min(medias) == max(medias):
        pendiente, intercepto = 0, mean(objetivos)
    else:
        pendiente, intercepto = linear_regression(medias, objetivos)

    print(f"Entrenamiento: {len(entrenamiento)} pares.")
    for grupo in ("validación", "prueba"):
        filas = particiones[grupo]
        observados = [observado for _, _, _, observado in filas]
        persistencia = [reciente for _, reciente, _, _ in filas]
        regresion = [
            min(100, max(0, intercepto + pendiente * media)) for _, _, media, _ in filas
        ]
        media_observada = mean(observados)
        sst = sum((valor - media_observada)**2 for valor in observados)
        for modelo, predichos in (
            ("Persistencia", persistencia), ("Regresión media24h", regresion)
        ):
            mae, rmse, sesgo = metricas(observados, predichos)
            r2 = f"{1 - len(filas) * rmse**2 / sst:.3f}" if sst else "indefinido"
            errores = [predicho - observado for observado, predicho in zip(
                observados, predichos, strict=True
            )]
            mayor = max(range(len(errores)), key=lambda indice: abs(errores[indice]))
            print(f"{grupo}, {modelo}, n={len(filas)}: MAE={mae:.3f}; "
                  f"RMSE={rmse:.3f}; sesgo={sesgo:.3f}; R²={r2}. "
                  f"Mayor desvío: {errores[mayor]:+.3f} en {filas[mayor][0]}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcomandos = parser.add_subparsers(dest="tarea", required=True)
    precios = subcomandos.add_parser("precios")
    precios.add_argument(
        "archivo", nargs="?", type=Path,
        default=Path(__file__).with_name("sipsa_tomate_chonto_bazurto_2026.csv"),
    )
    humedad = subcomandos.add_parser("humedad")
    humedad.add_argument("archivo", type=Path)
    args = parser.parse_args()
    try:
        print(f"SHA-256: {sha256(args.archivo.read_bytes()).hexdigest()}")
        if args.tarea == "precios":
            evaluar_precios(args.archivo)
        else:
            evaluar_humedad(args.archivo)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Entrada inválida: {error}\n")


if __name__ == "__main__":
    main()
