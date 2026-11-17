"""Aplicación web que consume la red neuronal para predecir el PIB.

Local:   python webapp/app.py            -> http://127.0.0.1:5000
Render:  ver GUIA.md

Qué servicio usa (el primero que esté configurado):
  1. Databricks Model Serving: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_ENDPOINT
  2. El modelo entrenado en Databricks copiado en webapp/modelo/modelo_pib.pkl
  3. El modelo de prueba de ../modelo_local/ (solo en tu computador)
Las variables se leen del entorno o de webapp/.env. El token nunca llega al
navegador: el navegador le habla a esta aplicación y esta, a la nube.
"""
import csv
import logging
import math
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from servicio import ENTRADAS, ErrorServicio, ServicioDatabricks, ServicioModelo, leer_env

AQUI = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ETIQUETAS = {
    "consumo_hogares": "Consumo de los hogares",
    "consumo_gobierno": "Consumo final del gobierno",
    "consumo_total": "Consumo total",
    "formacion_bruta_capital": "Formación bruta de capital",
    "formacion_bruta_capital_fijo": "Formación bruta de capital fijo",
    "demanda_final_interna": "Demanda final interna",
    "exportaciones": "Exportaciones totales",
    "importaciones": "Importaciones totales",
}
GRUPOS = [
    ("Consumo", ["consumo_hogares", "consumo_gobierno", "consumo_total"]),
    ("Inversión", ["formacion_bruta_capital", "formacion_bruta_capital_fijo"]),
    ("Comercio exterior", ["exportaciones", "importaciones"]),
    ("Total interno", ["demanda_final_interna"]),
]


def cargar_historia() -> list[dict]:
    with open(AQUI / "pib_2001_2011.csv", encoding="utf-8") as f:
        return [{k: (int(v) if k == "anio" else float(v)) for k, v in fila.items()} for fila in csv.DictReader(f)]


def crear_servicio():
    """Devuelve (servicio, es_prueba). es_prueba=True solo con el modelo de modelo_local/."""
    c = leer_env(AQUI / ".env")
    if c.get("DATABRICKS_HOST") and c.get("DATABRICKS_TOKEN"):
        return ServicioDatabricks(c["DATABRICKS_HOST"], c["DATABRICKS_TOKEN"], c.get("DATABRICKS_ENDPOINT", "red-neuronal-pib")), False
    incluido = AQUI / "modelo" / "modelo_pib.pkl"
    if incluido.exists():
        return ServicioModelo(incluido, "la red neuronal entrenada en Databricks, alojada en este servidor"), False
    prueba = AQUI.parent / "modelo_local" / "model.pkl"
    if prueba.exists():
        return ServicioModelo(prueba, "el modelo de prueba de este computador"), True
    return None, False


app = Flask(__name__)
HISTORIA = cargar_historia()
RANGOS = {k: (min(f[k] for f in HISTORIA), max(f[k] for f in HISTORIA)) for k in ENTRADAS}
SERVICIO, ES_PRUEBA = crear_servicio()
logging.getLogger("pib").info("Servicio: %s", SERVICIO.descripcion if SERVICIO else "ninguno")


@app.get("/")
def inicio():
    return render_template(
        "index.html",
        grupos=GRUPOS,
        etiquetas=ETIQUETAS,
        historia=HISTORIA,
        es_prueba=ES_PRUEBA,
        fuente=SERVICIO.descripcion if SERVICIO else None,
    )


@app.post("/api/predecir")
def predecir():
    if SERVICIO is None:
        return jsonify(error="No hay ninguna red neuronal configurada. Revisa las variables DATABRICKS_* (GUIA.md)."), 503

    recibido = request.get_json(silent=True) or {}
    valores, errores = {}, {}
    for k in ENTRADAS:
        texto = str(recibido.get(k, "")).strip().replace(",", ".")
        try:
            v = float(texto)
            if not math.isfinite(v):
                raise ValueError
            valores[k] = v
        except ValueError:
            errores[k] = "Escribe un número, por ejemplo 8,5 o -3."
    if errores:
        return jsonify(error="Revisa los campos marcados.", campos=errores), 400

    inicio_ms = time.perf_counter()
    try:
        pib = SERVICIO.predecir([[valores[k] for k in ENTRADAS]])[0]
    except ErrorServicio as e:
        return jsonify(error=str(e)), 502
    ms = round((time.perf_counter() - inicio_ms) * 1000)

    # Margen de 0,01 para que un año cargado con 2 decimales no salga "fuera de rango"
    fuera = [ETIQUETAS[k] for k, v in valores.items() if not (RANGOS[k][0] - 0.01 <= v <= RANGOS[k][1] + 0.01)]
    return jsonify(pib=pib, ms=ms, fuente=SERVICIO.descripcion, fuera_de_rango=fuera)


@app.get("/salud")
def salud():
    return {"servicio": SERVICIO.descripcion if SERVICIO else None, "prueba": ES_PRUEBA}


if __name__ == "__main__":
    import os

    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
