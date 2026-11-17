"""Clientes de la red neuronal.

- ServicioDatabricks: endpoint de Model Serving de Databricks (camino A).
- ServicioModelo: el modelo entrenado en Databricks, cargado dentro de esta
  aplicación (camino B, cuando Model Serving no está disponible) o el modelo
  de prueba de modelo_local/.
"""
import json
import logging
import os
import pickle
from pathlib import Path

import requests

log = logging.getLogger("pib")

ENTRADAS = [
    "importaciones",
    "consumo_total",
    "consumo_hogares",
    "consumo_gobierno",
    "formacion_bruta_capital",
    "formacion_bruta_capital_fijo",
    "demanda_final_interna",
    "exportaciones",
]
VARIABLES = ("DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_ENDPOINT")


def leer_env(ruta: Path) -> dict:
    """Lee un archivo KEY=valor sencillo. Las variables de entorno reales tienen prioridad."""
    valores = {}
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                valores[k.strip()] = v.strip().strip('"')
    for k in VARIABLES:
        if os.environ.get(k):
            valores[k] = os.environ[k]
    return valores


class ErrorServicio(Exception):
    pass


def _post(url: str, cuerpo: dict, token: str, plataforma: str, motivos: dict, timeout: int) -> object:
    try:
        r = requests.post(
            url,
            data=json.dumps(cuerpo),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
    except requests.Timeout as e:
        log.warning("%s no respondió a tiempo: %s", plataforma, e)
        raise ErrorServicio(
            f"El servicio de {plataforma} tardó demasiado en responder. Si estaba apagado por inactividad, "
            "se está encendiendo: intenta de nuevo en un par de minutos."
        ) from e
    except requests.RequestException as e:
        log.warning("Fallo de conexión con %s: %s", plataforma, e)
        raise ErrorServicio(f"No se pudo conectar con el servicio de {plataforma}. Revisa que siga publicado.") from e
    if r.status_code != 200:
        log.warning("%s respondió %s: %s", plataforma, r.status_code, r.text[:500])
        motivo = motivos.get(r.status_code, f"revisa los registros del servicio en {plataforma}")
        raise ErrorServicio(f"{plataforma} respondió con error {r.status_code}: {motivo}.")
    respuesta = r.json()
    if isinstance(respuesta, str):  # algunas versiones devuelven el JSON como texto
        respuesta = json.loads(respuesta)
    if isinstance(respuesta, dict):
        respuesta = respuesta.get("predictions", respuesta)
    return [float(v) for v in respuesta]


class ServicioDatabricks:
    """Llama a un endpoint de Model Serving de Databricks por HTTPS."""

    en_nube = True

    def __init__(self, host: str, token: str, endpoint: str):
        host = host.strip().rstrip("/")
        if not host.startswith("http"):
            host = "https://" + host
        self.url = f"{host}/serving-endpoints/{endpoint}/invocations"
        self.token = token
        self.descripcion = f"Databricks Model Serving, endpoint {endpoint}"

    def predecir(self, filas: list[list[float]]) -> list[float]:
        cuerpo = {"dataframe_split": {"columns": ENTRADAS, "data": filas}}
        motivos = {
            400: "los datos no tienen el formato que espera el modelo",
            401: "el token no es válido o venció (crea otro en Configuración, Desarrollador, Tokens de acceso)",
            403: "el token no tiene permiso para consultar ese endpoint",
            404: "ese endpoint no existe; revisa DATABRICKS_ENDPOINT",
            429: "hay demasiadas peticiones; espera unos segundos",
            503: "el servicio se está encendiendo después de estar inactivo; intenta en un par de minutos",
            504: "el servicio se está encendiendo después de estar inactivo; intenta en un par de minutos",
        }
        # Con "scale to zero" el primer llamado tras un rato inactivo puede tardar minutos
        return _post(self.url, cuerpo, self.token, "Databricks", motivos, timeout=120)


class ServicioModelo:
    """Carga un modelo de scikit-learn guardado con pickle y predice dentro de esta aplicación.

    Solo debe cargarse un archivo propio: abrir un pickle ejecuta el código que contenga.
    """

    en_nube = False

    def __init__(self, archivo: Path, descripcion: str):
        import pandas as pd  # solo hace falta en este modo

        self._pd = pd
        with open(archivo, "rb") as f:
            self._modelo = pickle.load(f)
        self.descripcion = descripcion

    def predecir(self, filas: list[list[float]]) -> list[float]:
        df = self._pd.DataFrame(filas, columns=ENTRADAS).astype("float64")
        return [float(v) for v in self._modelo.predict(df)]
