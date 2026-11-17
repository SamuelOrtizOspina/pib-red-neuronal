"""Convierte la base de conocimiento del DANE (Excel) en un CSV limpio.

Entrada : datos/base_conocimiento_pib_2001_2011.xls  (hoja "Cuadro 2 Var. % Anual")
Salida  : datos/pib_2001_2011.csv

Cada fila es un año y cada columna una variación porcentual anual:
x1..x8 son los componentes de la demanda y Y es el Producto Interno Bruto.
"""
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
ORIGEN = AQUI / "base_conocimiento_pib_2001_2011.xls"
DESTINO = AQUI / "pib_2001_2011.csv"

# Nombres cortos para las columnas (los usa el modelo, la API y la web)
COLUMNAS = {
    "x1": "importaciones",
    "x2": "consumo_total",
    "x3": "consumo_hogares",
    "x4": "consumo_gobierno",
    "x5": "formacion_bruta_capital",
    "x6": "formacion_bruta_capital_fijo",
    "x7": "demanda_final_interna",
    "x8": "exportaciones",
    "Y": "pib",
}


def main() -> None:
    hoja = pd.read_excel(ORIGEN, sheet_name="Cuadro 2 Var. % Anual", header=None)

    # La fila con "x1 ... Y" marca los encabezados; los años empiezan dos filas abajo.
    fila_codigos = hoja.index[hoja.eq("x1").any(axis=1)][0]
    codigos = hoja.loc[fila_codigos]
    col_periodo = hoja.loc[fila_codigos + 1].eq("Periodo").idxmax()

    filas = []
    for i in range(fila_codigos + 2, len(hoja)):
        anio = hoja.at[i, col_periodo]
        if pd.isna(anio):
            break
        registro = {"anio": int(anio)}
        for col, codigo in codigos.items():
            if codigo in COLUMNAS:
                registro[COLUMNAS[codigo]] = float(hoja.at[i, col])
        filas.append(registro)

    datos = pd.DataFrame(filas)
    assert len(datos) == 11 and datos["anio"].tolist() == list(range(2001, 2012)), datos
    assert not datos.isna().any().any(), "hay celdas vacías"

    datos.to_csv(DESTINO, index=False, float_format="%.6f")
    # Copia para la aplicación web (que se publica sola, sin la carpeta datos/)
    datos.to_csv(AQUI.parent / "webapp" / DESTINO.name, index=False, float_format="%.6f")
    print(f"{len(datos)} años guardados en {DESTINO.name}")
    print(datos.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
