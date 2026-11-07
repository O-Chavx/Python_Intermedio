"""Brechas de pobreza 2024 a partir de salidas/indicadores.csv (generado por la skill limpiando-enaho).

Uso, desde la raíz del repo: uv run python salidas/scripts/brechas_enaho.py
"""
import pandas as pd

ind = pd.read_csv("salidas/indicadores.csv", dtype={"categoria": str})
mapa = pd.read_csv("mapas/pobreza_departamento.csv", dtype={"FIRST_IDDP": str})
nac = ind.query("dimension == 'Nacional'").pobreza_pct.iloc[0]
rur = ind.query("dimension == 'Área' and categoria == 'Rural'")
urb = ind.query("dimension == 'Área' and categoria == 'Urbana'")
dep = ind.query("dimension == 'Departamento'")
filas = [
    ("Brecha rural - urbana, pobreza (pp)", rur.pobreza_pct.iloc[0] - urb.pobreza_pct.iloc[0]),
    ("Razón rural / urbana, pobreza", rur.pobreza_pct.iloc[0] / urb.pobreza_pct.iloc[0]),
    ("Brecha rural - urbana, pobreza extrema (pp)", rur.pobreza_extrema_pct.iloc[0] - urb.pobreza_extrema_pct.iloc[0]),
    ("Participación rural en la población (%)", 100 * rur.poblacion_expandida.iloc[0] / (rur.poblacion_expandida.iloc[0] + urb.poblacion_expandida.iloc[0])),
    ("Brecha máx - mín departamental (pp)", dep.pobreza_pct.max() - dep.pobreza_pct.min()),
    ("Departamentos sobre el promedio nacional", float((dep.pobreza_pct > nac).sum())),
    ("Departamentos con pobreza >= 38 %", float((dep.pobreza_pct >= 38).sum())),
]
out = pd.DataFrame(filas, columns=["indicador", "valor"]).round(2)
out["metodo"] = "hogares: factor07 × mieperho (salidas/indicadores.csv)"
out.to_csv("salidas/brechas_enaho.csv", index=False)
print(out.to_string(index=False))
print("\nDepartamentos (mapas/pobreza_departamento.csv):")
print(mapa.to_string(index=False))
