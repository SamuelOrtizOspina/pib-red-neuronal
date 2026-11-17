# Red neuronal para predecir el PIB: Databricks + Render

- **Databricks Free Edition:** la plataforma en la nube donde se entrena la red neuronal y se publica como servicio.
- **Render:** donde vive la página web que consume ese servicio.

Resultado esperado de la red: error medio de **0,53 puntos** en años que no vio, R² de **0,89**, aprende en **1.539 épocas**.

---

## 1. Crear la cuenta

Entra a https://www.databricks.com/learn/free-edition, pulsa **Sign up** y regístrate con Google, Microsoft o tu correo. Es gratis y no pide tarjeta.

## 2. Los servicios de IA de Databricks (para contarlo en el video)

- **Playground:** probar modelos de lenguaje ya entrenados.
- **Agentes e IA generativa:** construir chatbots y asistentes.
- **Búsqueda vectorial:** buscar dentro de documentos propios.
- **Experimentos (MLflow):** entrenar modelos propios y guardar su historial.
- **Modelos (Unity Catalog):** registrar los modelos entrenados.
- **Serving:** publicar un modelo como servicio web.

**Elegimos Experimentos + Serving**, porque son los que permiten entrenar una red propia con nuestros datos y publicarla. Los demás usan modelos de lenguaje ya hechos, que no sirven para predecir el PIB.

## 3. Subir la base de conocimiento

1. En Databricks: **New → Add or upload data → Create or modify table**.
2. Arrastra `datos/pib_2001_2011.csv`.
3. Catálogo `workspace`, esquema `default`, nombre de tabla **`pib_2001_2011`**.
4. Pulsa **Create table**.

## 4. Entrenar la red

1. **Workspace** → tu carpeta → menú **⋮ → Import** → elige `databricks/entrenar_red_pib.py`.
2. Abre el cuaderno, conecta el cómputo **Serverless** (arriba a la derecha) y pulsa **Run all**.
3. Tarda unos 2 minutos. Al terminar verás la tabla, el error medio, las gráficas y el mensaje del modelo registrado.

Dónde ver lo que quedó guardado:

- **Experiments:** la ejecución `red-neuronal-pib`, con métricas, parámetros y las gráficas `curva_aprendizaje.png` y `real_vs_prediccion.png`.
- **Catalog → workspace → default → Models:** el modelo `red_neuronal_pib`.

## 5. Publicar la red como servicio

1. **Serving → Create serving endpoint**.
2. Nombre: **`red-neuronal-pib`**. Entidad: el modelo `workspace.default.red_neuronal_pib`, versión 1.
3. Tamaño **Small**, CPU, marca **Scale to zero**. Pulsa **Create**.
4. Espera a que diga **Ready** (10 a 20 minutos).
5. Pruébalo con **Query endpoint** y este JSON, que son los datos de 2009. Debe responder cerca de 5,73; el real fue 5,72.

```json
{"dataframe_split": {
  "columns": ["importaciones","consumo_total","consumo_hogares","consumo_gobierno",
              "formacion_bruta_capital","formacion_bruta_capital_fijo","demanda_final_interna","exportaciones"],
  "data": [[-5.207755, 6.618653, 5.724919, 10.274101, 2.235742, 4.520427, 5.614074, -6.010075]]
}}
```

6. Crea un **token** para que la web pueda llamar al servicio: tu usuario (arriba a la derecha) → **Settings → Developer → Access tokens → Generate new token**. Cópialo; solo se muestra una vez.

**Si el paso 5 o el 6 no funciona** en tu cuenta gratuita, usa el **plan B**:

1. Descarga `modelo_pib.pkl` desde **Catalog → workspace → default → Volumes → pib**.
2. Ponlo en `webapp/modelo/`.
3. La web usará ese modelo directamente y no necesitará el token.

## 6. Publicar la web en Render

1. **Sube el proyecto a GitHub.** En github.com crea un repositorio nuevo (por ejemplo `pib-red-neuronal`), elige **uploading an existing file** y arrastra:
   - `databricks`, `datos` y `webapp`
   - `render.yaml`, `requirements.txt`, `GUIA.md` y `GUION_VIDEO.md`

   **No subas `.venv`.**
2. En https://render.com entra con tu cuenta de GitHub. Elige **New → Blueprint** y selecciona el repositorio.
3. Render leerá `render.yaml` y te pedirá dos valores:
   - **DATABRICKS_HOST:** la dirección de tu Databricks, como aparece en el navegador hasta `.com`. Por ejemplo `https://dbc-1234abcd-5678.cloud.databricks.com`.
   - **DATABRICKS_TOKEN:** el token del paso 5.

   En el plan B, déjalos vacíos.
4. Pulsa **Deploy**. En unos minutos la web queda en `https://pib-red-neuronal.onrender.com` (o un nombre parecido).

**Antes de grabar, abre la web y haz una predicción.** Render gratis se duerme a los 15 minutos sin uso, y el servicio de Databricks se apaga solo cuando nadie lo usa. La primera vez puede tardar uno o dos minutos; después responde rápido.

## 7. Probar la web en tu computador (opcional)

```powershell
cd C:\Users\samuo\Projects\pib-red-neuronal-azure
.venv\Scripts\activate
python webapp/app.py
```

Abre http://127.0.0.1:5000.

- **Sin configurar nada:** usa un modelo de prueba y muestra una franja amarilla que lo avisa.
- **Para usar Databricks:** crea `webapp/.env` con estas líneas:

```
DATABRICKS_HOST=https://dbc-....cloud.databricks.com
DATABRICKS_TOKEN=tu-token
DATABRICKS_ENDPOINT=red-neuronal-pib
```

## Archivos

| Archivo | Qué es |
|---|---|
| `datos/` | El Excel del DANE y el CSV limpio que se sube a Databricks |
| `databricks/entrenar_red_pib.py` | El cuaderno que entrena la red |
| `webapp/` | La página web (Flask) |
| `render.yaml` | La configuración para Render |
| `GUION_VIDEO.md` | Qué decir y mostrar en el video |
