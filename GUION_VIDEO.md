# Guion del video (unos 5 minutos)

Graba pantalla y voz con Xbox Game Bar (Win + Alt + R) u OBS. Lo que va entre comillas es una guía; dilo con tus palabras.

Antes de grabar abre en pestañas:

- Databricks, con el cuaderno ya ejecutado.
- La web en Render, con una predicción ya hecha para que esté despierta.

---

**1. El problema (30 s)**: muestra el Excel.

"Esta es la base de conocimiento del DANE: la variación del PIB de Colombia entre 2001 y 2011 y ocho
variables, como consumo, inversión, exportaciones e importaciones. El objetivo es entrenar una red
neuronal en la nube que prediga el PIB a partir de esas ocho variables, y usarla desde una página web."

**2. La plataforma (45 s)**: muestra el menú izquierdo de Databricks.

"Usé Databricks, una plataforma en la nube. Sus servicios de IA incluyen el Playground de modelos de
lenguaje, agentes, búsqueda vectorial, experimentos con MLflow y Serving para publicar modelos. Elegí
Experimentos y Serving porque permiten entrenar una red propia con mis datos y publicarla como servicio."

Muestra la tabla `pib_2001_2011` en el catálogo: "Aquí subí los datos."

**3. La red neuronal (1 min)**: el cuaderno, celda 2.

"La red tiene tres capas:

- Entrada, con 8 neuronas, una por variable.
- Una capa oculta de 8 neuronas con función sigmoide.
- Una neurona de salida, que da el PIB.

Cada neurona multiplica sus entradas por unos pesos, los suma y aplica la función. La red aprende
por retropropagación con el optimizador Adam: predice, mide el error contra el PIB real y corrige
los pesos un poco en cada época."

**4. El entrenamiento y el resultado (1 min)**: las celdas 3 y 4, y la gráfica.

"Como solo hay 11 años, la evalué dejando un año fuera cada vez: la entreno sin ese año y luego le
pido que lo prediga. El error medio fue de 0,53 puntos porcentuales y el R² de 0,89. En la gráfica,
la línea de la red sigue de cerca a la real."

Muestra la curva de aprendizaje: "El error baja rápido al principio y se estabiliza; aprendió en
1.539 épocas."

Abre **Experiments**: "MLflow guardó los parámetros, las métricas y las gráficas."

**5. El servicio (30 s)**: Serving, el endpoint `red-neuronal-pib` en estado Ready.

"Publiqué el modelo como servicio web." Haz la prueba con el JSON de 2009: "Le mando los datos de
2009 y responde 5,73 %; el real fue 5,72 %."

**6. La página web (1 min)**: la web en Render.

1. Carga el año 2009 y pulsa «Predecir el PIB». "La página le envía los datos al servicio de
   Databricks y muestra la respuesta."
2. Señala la línea de abajo: "Calculado por Databricks Model Serving".
3. Cambia algunos valores y predice de nuevo: "También sirve para escenarios inventados."

**7. Cierre (15 s)**

"En resumen: cargué la base del DANE, entrené una red neuronal en Databricks, la publiqué como
servicio y la consumo desde una página web en Render que predice el PIB."

---

## Si te preguntan

- **¿Por qué no separaste datos de prueba?** Con 11 años no alcanza. Dejar uno fuera cada vez usa
  los 11 para medir.
- **¿Predice el PIB del próximo año?** No. Calcula el PIB de un año a partir de las variables de ese
  mismo año.
- **¿Una regresión lineal no daría igual?** Daría incluso un poco mejor (0,27 puntos de error),
  porque el PIB es por definición consumo + inversión + exportaciones − importaciones. La actividad
  pedía una red neuronal, y la red también predice bien.
