"""Verificación independiente de las cifras del informe.

Uso: uv run .claude/skills/investigando-peru/scripts/verificar.py

No reutiliza el código del servidor MCP ni el de las skills: vuelve a pedir los datos a la API del BCRP con httpx y
vuelve a leer los .dta del INEI con pandas, y compara contra lo que el agente guardó en
salidas/cifras_bcrp.json, salidas/indicadores.csv y mapas/pobreza_departamento.csv.
Escribe salidas/verificacion.md y sale con código 1 si alguna cifra no coincide.
"""
import json
import sys
import zipfile
from pathlib import Path

import httpx
import pandas as pd

API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9,
         "Oct": 10, "Nov": 11, "Dic": 12}


def bcrp_mensual(codigo, desde, hasta):
    """Serie mensual directo de la API: {'2024-12': 1.97, ...}."""
    d, h = (f"{p[:4]}-{int(p[5:7])}" for p in (desde, hasta))
    js = httpx.get(f"{API}/{codigo}/json/{d}/{h}", timeout=60, follow_redirects=True).json()
    out = {}
    for p in js["periods"]:
        mes, anio = p["name"].split(".")
        try:
            out[f"{anio}-{MESES[mes]:02d}"] = float(p["values"][0])
        except ValueError:
            pass
    return pd.Series(out)


def estadistico(s, cual):
    return {"valor": s.iloc[-1], "ultimo": s.iloc[-1], "primero": s.iloc[0], "promedio": s.mean(),
            "maximo": s.max(), "minimo": s.min()}[cual]


def sumaria_directa():
    with zipfile.ZipFile("datos/966-Modulo34.zip") as z:
        nombre = next(n for n in z.namelist() if n.lower().endswith("sumaria-2024.dta"))
        with z.open(nombre) as f:
            df = pd.read_stata(f, convert_categoricals=False, columns=None)
    df.columns = [c.lower() for c in df.columns]
    df["peso"] = df.factor07 * df.mieperho
    df["pobre"] = (df.pobreza <= 2).astype(float)
    df["dep"] = df.ubigeo.astype(str).str.zfill(6).str[:2]
    return df


def tasa(df):
    return 100 * (df.pobre * df.peso).sum() / df.peso.sum()


def main():
    filas = []

    def anotar(fuente, afirmacion, informe, calculado, tol, metodo):
        ok = abs(informe - calculado) <= tol
        filas.append({"Fuente": fuente, "Afirmación": afirmacion, "Valor en el informe": round(informe, 2),
                      "Valor recalculado": round(calculado, 2), "Diferencia": round(informe - calculado, 3),
                      "Tolerancia": tol, "Coincide": "Sí" if ok else "NO", "Cómo se verificó": metodo})

    # --- BCRP: cada cifra que el agente guardó, recalculada desde la API ---
    ruta = Path("salidas/cifras_bcrp.json")
    if not ruta.exists():
        sys.exit("Falta salidas/cifras_bcrp.json: el agente debe guardar las cifras del BCRP que usa.")
    for c in json.loads(ruta.read_text(encoding="utf-8")):
        s = bcrp_mensual(c["codigo"], c["desde"], c["hasta"])
        anotar("BCRP", c["afirmacion"], float(c["valor"]), float(estadistico(s, c["estadistico"])), 0.01,
               f"API BCRP {c['codigo']} {c['desde']}–{c['hasta']}, {c['estadistico']} con pandas")

    # --- ENAHO: lectura nueva de la sumaria, sin pasar por limpiar.py ---
    sm = sumaria_directa()
    ind = pd.read_csv("salidas/indicadores.csv", dtype={"categoria": str})
    get = lambda dim, cat: float(ind.query("dimension == @dim and categoria == @cat").pobreza_pct.iloc[0])
    anotar("ENAHO", "Pobreza monetaria nacional 2024 (%)", get("Nacional", "Perú"), tasa(sm), 0.05,
           "sumaria-2024.dta leída de nuevo, factor07 × mieperho; referencia INEI 27.6 %")
    rural, urbana = sm[sm.estrato > 5], sm[sm.estrato <= 5]
    anotar("ENAHO", "Pobreza rural 2024 (%)", get("Área", "Rural"), tasa(rural), 0.05, "estrato 6-8; referencia 39.3 %")
    anotar("ENAHO", "Pobreza urbana 2024 (%)", get("Área", "Urbana"), tasa(urbana), 0.05, "estrato 1-5; referencia 24.8 %")
    mapa = pd.read_csv("mapas/pobreza_departamento.csv", dtype={"FIRST_IDDP": str})
    dep = sm.groupby("dep").apply(tasa, include_groups=False)
    top = mapa.iloc[0]
    anotar("ENAHO", f"Departamento con más pobreza: {top.NOMBDEP.title()} (%)", float(top.tasa), float(dep[top.FIRST_IDDP]),
           0.05, f"sumaria por ubigeo[:2] = {top.FIRST_IDDP}; referencia Sesión 16 45.0 %")
    anotar("ENAHO", "Departamentos en el mapa", float(len(mapa)), float(dep.size), 0, "ubigeo[:2] distintos en la sumaria")

    tabla = pd.DataFrame(filas)
    md = ["# Verificación independiente de cifras", "",
          "Generado por `.claude/skills/investigando-peru/scripts/verificar.py`. Los valores recalculados no usan "
          "el servidor MCP ni los scripts de las skills: salen de la API del BCRP y de los .dta del INEI.", "",
          tabla.to_markdown(index=False), "",
          f"**Resultado:** {(tabla.Coincide == 'Sí').sum()}/{len(tabla)} cifras coinciden."]
    Path("salidas/verificacion.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    sys.exit(0 if (tabla.Coincide == "Sí").all() else 1)


if __name__ == "__main__":
    main()
