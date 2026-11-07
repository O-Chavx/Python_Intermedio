"""Gráfico de barras de la pobreza ponderada por área, sexo, edad o departamento.

Uso: uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area [--anio 2024]
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

VARIABLES = {
    "area": ("area", "área de residencia"),
    "sexo": ("sexo", "sexo"),
    "edad": ("grupo_edad", "grupo de edad"),
    "departamento": ("departamento", "departamento"),
}
INDICADORES = {"pobreza": ("pobre", "Pobreza monetaria"), "extrema": ("pobre_extremo", "Pobreza extrema")}
NOMBRES_DEP = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
COLOR = "#2b5c8a"
HOGAR = {"area", "departamento"}
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
NACIONAL = 27.6  # referencia INEI 2024, línea punteada


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--por", choices=VARIABLES, required=True)
    ap.add_argument("--indicador", choices=INDICADORES, default="pobreza")
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--figuras", type=Path, default=Path("figuras"))
    a = ap.parse_args()

    ruta = Path(f"salidas/personas_{a.anio}.parquet")
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. Corre primero la skill limpiando-enaho.")
    base = pd.read_parquet(ruta)

    col, etiqueta = VARIABLES[a.por]
    ind, titulo_ind = INDICADORES[a.indicador]
    # Regla: siempre ponderado, nunca conteo de encuestas.
    # Área y departamento son características del hogar: método oficial del INEI (un registro por hogar,
    # factor07 × mieperho), que replica 24.8 % urbano y 39.3 % rural. Sexo y edad son de la persona: facpob07.
    if a.por in HOGAR:
        datos, peso, metodo = base.drop_duplicates(LLAVES_HOGAR), "peso_hogar", "factor07 × mieperho (hogares)"
        datos = datos.assign(peso_hogar=datos.factor07 * datos.mieperho)
    else:
        datos, peso, metodo = base, "facpob07", "facpob07 (personas)"
    tabla = (
        datos.assign(_num=datos[ind] * datos[peso])
        .groupby(col)[["_num", peso]].sum()
        .pipe(lambda t: t._num / t[peso] * 100)
        .sort_values()
    )
    if a.por == "departamento":
        tabla.index = tabla.index.map(NOMBRES_DEP)
    # Edad sigue su orden natural; el resto, de menor a mayor
    if a.por == "edad":
        tabla = tabla.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))

    alto = max(3.0, 0.32 * len(tabla) + 1.2)
    fig, ax = plt.subplots(figsize=(7, alto))
    barras = ax.barh(tabla.index.astype(str), tabla.values, color=COLOR)
    ax.bar_label(barras, labels=[f"{v:.1f} %" for v in tabla.values], padding=3, fontsize=9)
    ax.set_xlim(0, tabla.max() * 1.18)  # empieza en cero
    if a.indicador == "pobreza" and a.anio == 2024:
        ax.axvline(NACIONAL, color="#c0392b", linestyle="--", linewidth=1)
        ax.text(NACIONAL, len(tabla) - 0.4, f" Perú {NACIONAL} %", color="#c0392b", fontsize=8, va="bottom")
    ax.set_xlabel("% de personas")
    ax.set_title(f"{titulo_ind} por {etiqueta}, Perú {a.anio}", loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {a.anio}, módulos 34 y 02. Ponderado con {metodo}.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    a.figuras.mkdir(parents=True, exist_ok=True)
    salida = a.figuras / f"{a.indicador}_{a.por}_{a.anio}.png"
    fig.savefig(salida, dpi=200)
    print(f"{titulo_ind} por {etiqueta}, {a.anio} (ponderado con {metodo}):")
    for k, v in tabla.items():
        print(f"  {k:<15} {v:5.1f} %")
    print(f"Figura guardada en {salida}")


if __name__ == "__main__":
    main()
