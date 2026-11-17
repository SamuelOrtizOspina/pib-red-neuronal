# Carpeta del modelo (camino B)

Solo se usa si Databricks no te deja publicar el modelo como servicio (Model Serving) o crear el token.

1. En Databricks ejecuta el cuaderno completo (por lo menos hasta la sección 6).
2. Ve a **Catálogo → workspace → default → Volúmenes → pib** y descarga `modelo_pib.pkl`.
3. Ponlo en esta carpeta: `webapp/modelo/modelo_pib.pkl`.
4. No configures las variables `DATABRICKS_*` en Render.

La aplicación carga ese archivo y atiende las predicciones en `POST /api/predecir`.

No pongas aquí el modelo de `modelo_local/`: es el de prueba entrenado en este computador, no en la nube.
