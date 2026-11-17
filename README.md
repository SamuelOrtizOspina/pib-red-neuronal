# Predicción del PIB de Colombia con una red neuronal en la nube

Red neuronal entrenada en **Databricks** con la base de conocimiento del DANE (2001-2011), publicada como servicio web con **Model Serving** y consumida por una aplicación web desplegada en **Render**.

**Aplicación en línea:** https://pib-red-neuronal.onrender.com

> El plan gratuito de Render apaga la aplicación tras 15 minutos sin uso y el servicio de Databricks escala a cero. La primera predicción después de un rato puede tardar uno o dos minutos.

---

## Cómo funciona todo

```mermaid
flowchart LR
    subgraph datos["1. Datos"]
        A["Excel del DANE<br/>PIB 2001-2011"] --> B["extraer_datos.py"]
        B --> C["pib_2001_2011.csv<br/>11 años, 8 variables + PIB"]
    end

    subgraph databricks["2. Databricks (entrenamiento y servicio)"]
        D["Tabla<br/>workspace.default.pib_2001_2011"]
        E["Cuaderno<br/>entrenar_red_pib"]
        F["MLflow<br/>experimento: métricas y gráficas"]
        G["Unity Catalog<br/>modelo red_neuronal_pib"]
        H["Model Serving<br/>endpoint red-neuronal-pib"]
        D --> E
        E -->|entrena la red| F
        E -->|registra| G
        G -->|se publica| H
    end

    subgraph render["3. Render (aplicación web)"]
        I["Aplicación Flask<br/>webapp/app.py"]
    end

    U(("Usuario")) -->|escribe 8 valores| I
    C -->|se sube| D
    I -->|"POST /invocations + token"| H
    H -->|PIB predicho| I
    I -->|muestra resultado y gráfica| U
```

### Qué pasa en una predicción

```mermaid
sequenceDiagram
    actor U as Usuario
    participant W as Navegador
    participant R as Render (Flask)
    participant D as Databricks Model Serving
    participant M as Red neuronal

    U->>W: Elige un año o escribe las 8 variables
    W->>R: POST /api/predecir
    R->>R: Valida los valores
    R->>D: POST /serving-endpoints/red-neuronal-pib/invocations<br/>(token en la cabecera, nunca en el navegador)
    D->>M: Estandariza entradas y ejecuta la red
    M-->>D: Variación del PIB (%)
    D-->>R: {"predictions": [5.73]}
    R-->>W: PIB, fuente y avisos de rango
    W-->>U: Muestra la cifra y la marca en la gráfica
```

---

## La red neuronal

```mermaid
flowchart LR
    subgraph entrada["Entrada: 8 neuronas"]
        x1["Importaciones"]
        x2["Consumo total"]
        x3["Consumo hogares"]
        x4["Consumo gobierno"]
        x5["Formación bruta de capital"]
        x6["Formación bruta de capital fijo"]
        x7["Demanda final interna"]
        x8["Exportaciones"]
    end

    subgraph oculta["Capa oculta: 8 neuronas sigmoide"]
        h1(("h1")) ~~~ h2(("h2")) ~~~ h3(("h3")) ~~~ h4(("h4"))
        h5(("h5")) ~~~ h6(("h6")) ~~~ h7(("h7")) ~~~ h8(("h8"))
    end

    subgraph salida["Salida: 1 neurona"]
        y(("PIB %"))
    end

    entrada -->|"64 pesos + 8 sesgos"| oculta
    oculta -->|"8 pesos + 1 sesgo"| salida
```

| Elemento | Valor |
|---|---|
| Tipo | Perceptrón multicapa (`MLPRegressor` de scikit-learn) |
| Arquitectura | 8 → 8 → 1, activación sigmoide en la capa oculta |
| Parámetros aprendidos | 81 (64 + 8 + 8 + 1) |
| Preprocesamiento | Estandarización de entradas y salida (media 0, desviación 1) |
| Entrenamiento | Retropropagación con optimizador Adam, tasa de aprendizaje 0,01, regularización L2 α = 0,01 |
| Épocas | 1.539 (se detiene cuando el error deja de mejorar) |

Cada neurona oculta calcula `z = w1·x1 + … + w8·x8 + b` y luego `σ(z) = 1 / (1 + e^(−z))`. La neurona de salida combina las 8 activaciones con sus pesos y da la variación del PIB.

### Resultados (validación dejando un año fuera)

| Modelo | Error medio absoluto | R² |
|---|---|---|
| **Red neuronal 8-8-1** | **0,53 puntos** | **0,89** |
| Red con 1 neurona oculta | 1,00 puntos | 0,63 |
| Predecir siempre el promedio | 2,12 puntos | −0,21 |

---

## Estructura del repositorio

```
datos/                  Excel original del DANE, CSV limpio y script de extracción
databricks/             Cuaderno de entrenamiento (se importa en Databricks)
webapp/                 Aplicación web Flask
  app.py                Rutas: página principal, /api/predecir, /salud
  servicio.py           Cliente del endpoint de Databricks (o modelo incluido)
  templates/, static/   Interfaz
modelo_local/           Modelo de prueba para correr la web sin la nube
render.yaml             Configuración de despliegue en Render
GUIA.md                 Paso a paso para montar todo
```

## Correr la aplicación en local

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python webapp/app.py
```

Abre http://127.0.0.1:5000. Sin configurar nada, usa el modelo de prueba de `modelo_local/`. Para usar el servicio de Databricks, define `DATABRICKS_HOST`, `DATABRICKS_TOKEN` y `DATABRICKS_ENDPOINT` como variables de entorno o en `webapp/.env` (este archivo no se sube al repositorio).

## Tecnologías

Databricks Free Edition (cuadernos, MLflow, Unity Catalog, Model Serving) · scikit-learn · Flask · Render
