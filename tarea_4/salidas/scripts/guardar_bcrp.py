"""Guarda en salidas/ las cifras BCRP devueltas por el servidor MCP `bcrp` (copiadas de las respuestas de
`resumen` y `comparar_series`, consultadas el 2026-11-04). No calcula nada: solo registra.

Uso, desde la raíz del repo: uv run python salidas/scripts/guardar_bcrp.py
"""
import json

A, G = "PN09822PM", "PN01273PM"
N = {A: "Inflación de alimentos y bebidas, Lima Metropolitana (var% 12m)",
     G: "Inflación general IPC, Lima Metropolitana (var% 12m)"}


def url(c, d, h):
    return f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{c}/html/{d[:4]}-{int(d[5:])}/{h[:4]}-{int(h[5:])}"


rows = []


def add(c, d, h, e, v, txt):
    rows.append(dict(afirmacion=f"{N[c]}: {txt}", codigo=c, desde=d, hasta=h, estadistico=e,
                     valor=round(v, 4), fuente=url(c, d, h), herramienta="mcp bcrp resumen"))


add(A, "2020-01", "2024-12", "promedio", 5.884289, "promedio ene-2020 a dic-2024")
add(G, "2020-01", "2024-12", "promedio", 4.466356, "promedio ene-2020 a dic-2024")
add(A, "2020-01", "2024-12", "maximo", 13.1637473661575, "máximo del periodo (2023-02)")
add(G, "2020-01", "2024-12", "maximo", 8.81263294388897, "máximo del periodo (2022-06)")
add(A, "2020-01", "2024-12", "minimo", 0.687659922758327, "mínimo del periodo (2024-09)")
add(G, "2020-01", "2024-12", "minimo", 1.59873239164688, "mínimo del periodo (2020-06)")
add(A, "2020-01", "2020-01", "valor", 1.11379477251542, "ene-2020")
add(G, "2020-01", "2020-01", "valor", 1.88835605229068, "ene-2020")
for y, a, g in [(2020, 2.23665451633161, 1.97323222946074), (2021, 7.97176823871967, 6.43038716340725),
                (2022, 12.643877921265, 8.45916200000001), (2023, 4.8043982437401, 3.23738256432406),
                (2024, 1.24814760630121, 1.96630270142824)]:
    add(A, f"{y}-12", f"{y}-12", "valor", a, f"dic-{y}")
    add(G, f"{y}-12", f"{y}-12", "valor", g, f"dic-{y}")

with open("salidas/cifras_bcrp.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

comp = dict(herramienta="mcp bcrp comparar_series", codigo_a=A, codigo_b=G, desde="2020-01", hasta="2024-12",
            n_comunes=60, brecha_promedio_pp=1.417933, mayor_brecha=dict(periodo="2023-05", valor_pp=5.177527),
            periodos_alimentos_mayor=44, correlacion_pearson=0.9807,
            fuentes=[url(A, "2020-01", "2024-12"), url(G, "2020-01", "2024-12")],
            nota="Brecha = alimentos - general (puntos porcentuales). La 'variacion_pct' de la herramienta "
                 "(cambio % de una tasa) no se usa en el informe por no ser interpretable.")
with open("salidas/cifras_bcrp_comparacion.json", "w", encoding="utf-8") as f:
    json.dump(comp, f, ensure_ascii=False, indent=2)
print(len(rows), "cifras guardadas")
