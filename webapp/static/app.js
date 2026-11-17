// Interfaz de la predicción del PIB. El navegador solo habla con /api/predecir;
// la llamada a la nube (con su token) la hace el servidor.
const historia = JSON.parse(document.getElementById("historia").textContent);
const form = document.getElementById("formulario");
const selectorAnio = document.getElementById("anio");
const boton = document.getElementById("boton");
const campos = [...document.querySelectorAll(".campo")].map((el) => el.dataset.campo);

const num = (v, dec = 2) =>
  v.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
const leer = (texto) => {
  const t = String(texto).trim().replace(",", ".");
  return t === "" || isNaN(Number(t)) ? null : Number(t);
};

// Rango histórico de cada variable, para orientar a quien escribe un escenario
for (const k of campos) {
  const vals = historia.map((f) => f[k]);
  const caja = document.querySelector(`[data-campo="${k}"] .rango`);
  caja.textContent = `De 2001 a 2011 fue de ${num(Math.min(...vals), 1)} % a ${num(Math.max(...vals), 1)} %.`;
}

function filaDelAnio() {
  return historia.find((f) => String(f.anio) === selectorAnio.value) || null;
}

function coincideConAnio() {
  const fila = filaDelAnio();
  if (!fila) return false;
  return campos.every((k) => {
    const v = leer(form.elements[k].value);
    return v !== null && Math.abs(v - fila[k]) < 0.005;
  });
}

selectorAnio.addEventListener("change", () => {
  const fila = filaDelAnio();
  for (const k of campos) form.elements[k].value = fila ? num(fila[k]) : "";
  limpiarErrores();
});

function limpiarErrores() {
  document.querySelectorAll(".campo").forEach((el) => {
    el.classList.remove("mal");
    el.querySelector(".error").textContent = "";
  });
  document.getElementById("error-general").textContent = "";
}

function marcarErrores(errores) {
  for (const [k, msg] of Object.entries(errores)) {
    const el = document.querySelector(`[data-campo="${k}"]`);
    el.classList.add("mal");
    el.querySelector(".error").textContent = msg;
  }
  const primero = Object.keys(errores)[0];
  if (primero) form.elements[primero].focus();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  limpiarErrores();

  const valores = {};
  const errores = {};
  for (const k of campos) {
    const texto = form.elements[k].value;
    if (leer(texto) === null) errores[k] = texto.trim() ? "Escribe un número, por ejemplo 8,5 o -3." : "Falta este dato.";
    valores[k] = texto;
  }
  if (Object.keys(errores).length) {
    marcarErrores(errores);
    document.getElementById("error-general").textContent = "Revisa los campos marcados.";
    return;
  }

  const fila = coincideConAnio() ? filaDelAnio() : null;
  boton.disabled = true;
  boton.textContent = "Consultando la red neuronal…";
  try {
    const r = await fetch("/api/predecir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(valores),
    });
    const datos = await r.json();
    if (!r.ok) {
      if (datos.campos) marcarErrores(datos.campos);
      document.getElementById("error-general").textContent = datos.error || "No se pudo obtener la predicción.";
      return;
    }
    mostrar(datos, fila);
  } catch {
    document.getElementById("error-general").textContent =
      "No hubo respuesta del servidor. Revisa que la aplicación siga corriendo.";
  } finally {
    boton.disabled = false;
    boton.textContent = "Predecir el PIB";
  }
});

function mostrar(datos, fila) {
  const cifra = document.getElementById("cifra");
  cifra.textContent = `${num(datos.pib)} %`;
  cifra.classList.remove("vacia");

  const detalle = document.getElementById("detalle");
  const notas = [];
  if (fila) {
    const dif = datos.pib - fila.pib;
    detalle.textContent = `Real según el DANE en ${fila.anio}: ${num(fila.pib)} %. La red se desvía ${dif >= 0 ? "+" : ""}${num(dif)} puntos.`;
    notas.push(`${fila.anio} es uno de los 11 años con los que se entrenó la red, por eso acierta casi exacto. En años que no vio, se equivoca en promedio por unos 0,5 puntos.`);
  } else {
    detalle.textContent = "Escenario propio: no hay un dato real con qué compararlo.";
    notas.push("En años que no vio durante el entrenamiento, la red se equivoca en promedio por unos 0,5 puntos.");
  }
  for (const nombre of datos.fuera_de_rango) {
    notas.push({ alerta: true, texto: `${nombre} está fuera de lo observado entre 2001 y 2011: la red está extrapolando y la cifra es menos confiable.` });
  }
  const lista = document.getElementById("notas");
  lista.replaceChildren(
    ...notas.map((n) => {
      const li = document.createElement("li");
      if (typeof n === "string") li.textContent = n;
      else { li.textContent = n.texto; li.className = "alerta"; }
      return li;
    })
  );

  document.getElementById("fuente").textContent =
    `Calculado por ${datos.fuente} en ${datos.ms} ms.`;
  dibujar(datos.pib, fila ? fila.anio : null);
}

// Gráfica: PIB real 2001-2011 y el punto de la predicción
const SVG = "http://www.w3.org/2000/svg";
function el(tag, attrs, texto) {
  const n = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (texto !== undefined) n.textContent = texto;
  return n;
}

function dibujar(pred, anioPred) {
  const svg = document.getElementById("grafica");
  svg.replaceChildren();
  const etiquetas = historia.map((f) => String(f.anio));
  const conEscenario = pred !== null && anioPred === null;
  if (conEscenario) etiquetas.push("Escenario");
  const W = 520, H = 260, izq = 44, der = conEscenario ? 34 : 16, arr = 28, aba = 30;

  const vals = historia.map((f) => f.pib).concat(pred !== null ? [pred] : []);
  const yMin = Math.floor(Math.min(...vals) - 1);
  const yMax = Math.ceil(Math.max(...vals) + 1);
  const x = (i) => izq + (i * (W - izq - der)) / (etiquetas.length - 1);
  const y = (v) => arr + ((yMax - v) * (H - arr - aba)) / (yMax - yMin);

  const paso = yMax - yMin > 10 ? 4 : 2;
  for (let v = Math.ceil(yMin / paso) * paso; v <= yMax; v += paso) {
    svg.append(el("line", { x1: izq, x2: W - der, y1: y(v), y2: y(v), class: "eje" }));
    svg.append(el("text", { x: izq - 8, y: y(v) + 4, "text-anchor": "end", class: "texto" }, `${v} %`));
  }
  etiquetas.forEach((t, i) => {
    const corta = t === "Escenario" ? t : `’${t.slice(2)}`;
    svg.append(el("text", { x: x(i), y: H - 8, "text-anchor": "middle", class: "texto" }, corta));
  });

  const d = historia.map((f, i) => `${i ? "L" : "M"}${x(i)},${y(f.pib)}`).join(" ");
  svg.append(el("path", { d, class: "linea" }));
  historia.forEach((f, i) => svg.append(el("circle", { cx: x(i), cy: y(f.pib), r: 3.5, class: "punto" })));

  if (pred !== null) {
    const i = anioPred === null ? etiquetas.length - 1 : historia.findIndex((f) => f.anio === anioPred);
    svg.append(el("line", { x1: x(i), x2: x(i), y1: arr, y2: H - aba, class: "guia" }));
    svg.append(el("circle", { cx: x(i), cy: y(pred), r: 6, class: "pred" }));
    // Cifra encima del punto, sobre la línea guía, para no tapar los puntos vecinos
    const ancla = x(i) > W - 40 ? "end" : x(i) < izq + 30 ? "start" : "middle";
    const dx = ancla === "end" ? 8 : ancla === "start" ? -8 : 0;
    svg.append(el("text", { x: x(i) + dx, y: arr - 10, "text-anchor": ancla, class: "etq-pred" }, `${num(pred)} %`));
  }
}

dibujar(null, null);
document.getElementById("cifra").classList.add("vacia");
