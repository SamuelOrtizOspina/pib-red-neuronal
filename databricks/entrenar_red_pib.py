# Databricks notebook source
# MAGIC %md
# MAGIC # Red neuronal para predecir el PIB de Colombia
# MAGIC Base de conocimiento: variación % anual del PIB y de 8 componentes de la demanda, 2001-2011 (DANE).

# COMMAND ----------

# MAGIC %pip install scikit-learn==1.6.1 --quiet

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Cargar los datos
# MAGIC La tabla se creó subiendo `pib_2001_2011.csv` (Nuevo → Agregar o cargar datos).

# COMMAND ----------

import pickle

import matplotlib.pyplot as plt
import mlflow
import numpy as np
from mlflow.models import infer_signature
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ENTRADAS = [
    "importaciones", "consumo_total", "consumo_hogares", "consumo_gobierno",
    "formacion_bruta_capital", "formacion_bruta_capital_fijo", "demanda_final_interna", "exportaciones",
]

datos = spark.table("workspace.default.pib_2001_2011").toPandas().sort_values("anio").reset_index(drop=True)
X = datos[ENTRADAS].astype("float64")   # 8 entradas
y = datos["pib"].astype("float64")      # salida: PIB
display(datos)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. La red neuronal
# MAGIC - **8 neuronas de entrada** (una por variable, estandarizadas).
# MAGIC - **8 neuronas ocultas** con función sigmoide.
# MAGIC - **1 neurona de salida**: la variación del PIB.
# MAGIC
# MAGIC Aprende con **retropropagación** y el optimizador **Adam**: predice, mide el error y corrige los pesos, época tras época.

# COMMAND ----------

def crear_red():
    red = MLPRegressor(
        hidden_layer_sizes=(8,),     # capa oculta de 8 neuronas
        activation="logistic",       # sigmoide
        solver="adam",               # optimizador
        learning_rate_init=0.01,     # tasa de aprendizaje
        alpha=0.01,                  # penalización para no memorizar
        max_iter=20000, tol=1e-7, random_state=0,
    )
    # Estandariza entradas y salida antes de la red
    return TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(), red), transformer=StandardScaler())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. ¿Qué tan bien predice?
# MAGIC Con solo 11 años se usa **validación dejando uno fuera**: se entrena 11 veces, cada vez sin un año, y se predice ese año.

# COMMAND ----------

pred = cross_val_predict(crear_red(), X, y, cv=LeaveOneOut())
mae = mean_absolute_error(y, pred)
r2 = r2_score(y, pred)
print(f"Error medio: {mae:.2f} puntos porcentuales | R2: {r2:.2f}")

plt.figure(figsize=(7, 4))
plt.plot(datos["anio"], y, "o-", label="PIB real (DANE)")
plt.plot(datos["anio"], pred, "s--", label="Red neuronal")
plt.xlabel("Año"); plt.ylabel("Variación anual del PIB (%)"); plt.legend(); plt.grid(alpha=0.3)
grafica_pred = plt.gcf()
plt.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Entrenar el modelo final y registrarlo
# MAGIC Se entrena con los 11 años. MLflow guarda parámetros, métricas, gráficas y el modelo,
# MAGIC y lo registra en el catálogo como `workspace.default.red_neuronal_pib`.

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")

with mlflow.start_run(run_name="red-neuronal-pib"):
    modelo = crear_red()
    modelo.fit(X, y)
    red = modelo.regressor_.named_steps["mlpregressor"]

    mlflow.log_params({"neuronas_ocultas": 8, "activacion": "sigmoide", "optimizador": "adam", "tasa_aprendizaje": 0.01})
    mlflow.log_metrics({"error_medio": mae, "r2": r2, "epocas": red.n_iter_})

    plt.figure(figsize=(7, 4))
    plt.plot(red.loss_curve_)
    plt.yscale("log"); plt.xlabel("Época"); plt.ylabel("Error"); plt.title("Curva de aprendizaje"); plt.grid(alpha=0.3)
    mlflow.log_figure(plt.gcf(), "curva_aprendizaje.png")
    mlflow.log_figure(grafica_pred, "real_vs_prediccion.png")
    plt.show()

    mlflow.sklearn.log_model(
        modelo, "modelo",
        signature=infer_signature(X, modelo.predict(X)),
        input_example=X.head(1),
        registered_model_name="workspace.default.red_neuronal_pib",
    )

print(f"La red aprendió en {red.n_iter_} épocas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Guardar una copia del modelo
# MAGIC Por si se necesita poner el modelo directamente en la aplicación web (Render).

# COMMAND ----------

spark.sql("CREATE VOLUME IF NOT EXISTS workspace.default.pib")
with open("/Volumes/workspace/default/pib/modelo_pib.pkl", "wb") as f:
    pickle.dump(modelo, f)
print("Copia guardada en Catálogo → workspace → default → Volúmenes → pib")
