"""Calcula las respuestas esperadas de las 10 preguntas ANTES de correr la evaluación y escribe preguntas.csv.

    uv run evaluacion/respuestas_esperadas.py

Independiente del agente: BCRP directo de su API (httpx) y ENAHO directo de los .dta del INEI (pandas), sin usar
el servidor MCP ni las skills. Las tolerancias se fijan aquí y no se cambian después de ver los resultados.
"""
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1] / ".claude/skills/investigando-peru/scripts"))
from verificar import bcrp_mensual, sumaria_directa, tasa  # noqa: E402

AQUI = Path(__file__).parent


def personas_directas():
    with zipfile.ZipFile("datos/966-Modulo02.zip") as z:
        nombre = next(n for n in z.namelist() if n.lower().endswith("enaho01-2024-200.dta"))
        with z.open(nombre) as f:
            p = pd.read_stata(f, convert_categoricals=False)
    p.columns = [c.lower() for c in p.columns]
    p = p[((p.p204 == 1) & (p.p205 == 2)) | ((p.p204 == 2) & (p.p206 == 1))]
    llaves = ["conglome", "vivienda", "hogar"]
    for c in llaves:
        p[c] = p[c].astype(str).str.strip()
    s = sumaria_directa()
    for c in llaves:
        s[c] = s[c].astype(str).str.strip()
    return p.merge(s[llaves + ["pobreza"]], on=llaves, validate="m:1")


def main():
    sm, pe = sumaria_directa(), personas_directas()
    w = lambda d: 100 * ((d.pobreza <= 2) * d.facpob07).sum() / d.facpob07.sum()
    ipc = bcrp_mensual("PN01273PM", "2020-01", "2024-12")
    ali = bcrp_mensual("PN09822PM", "2020-01", "2024-12")
    tc = bcrp_mensual("PN01206PM", "2024-12", "2024-12")
    ref = bcrp_mensual("PD04722MM", "2024-12", "2024-12")
    rural, urbana = tasa(sm[sm.estrato > 5]), tasa(sm[sm.estrato <= 5])
    ext = 100 * ((sm.pobreza == 1) * sm.peso).sum() / sm.peso.sum()
    dep = sm.groupby("dep").apply(tasa, include_groups=False)

    P = [
        ("B1", "bcrp", "¿Cuál fue la inflación de Lima Metropolitana en los últimos 12 meses a diciembre de 2024, en %?",
         ipc["2024-12"], None, 0.01, "BCRP PN01273PM, 2024-12"),
        ("B2", "bcrp", "¿Cuál fue el tipo de cambio interbancario venta promedio de diciembre de 2024, en soles por dólar?",
         tc["2024-12"], None, 0.005, "BCRP PN01206PM, 2024-12"),
        ("B3", "bcrp", "¿Cuál era la tasa de referencia de la política monetaria del BCRP en diciembre de 2024, en %?",
         ref["2024-12"], None, 0.01, "BCRP PD04722MM, 2024-12"),
        ("B4", "bcrp", "Entre enero de 2020 y diciembre de 2024, ¿cuál fue el valor máximo de la inflación a 12 meses de "
         "alimentos y bebidas en Lima Metropolitana, en %?", ali.max(), None, 0.01, f"BCRP PN09822PM, máximo en {ali.idxmax()}"),
        ("E1", "enaho", "Según la ENAHO 2024, ¿qué porcentaje de la población del Perú estaba en pobreza extrema?",
         ext, None, 0.1, "ENAHO 2024 sumaria, factor07 × mieperho"),
        ("E2", "enaho", "Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria del departamento de Puno, en %?",
         dep["21"], None, 0.1, "ENAHO 2024 sumaria, ubigeo 21, factor07 × mieperho"),
        ("E3", "enaho", "Según la ENAHO 2024, ¿qué porcentaje de los niños de 0 a 13 años (residentes habituales) vivía en "
         "pobreza monetaria?", w(pe[pe.p208a <= 13]), None, 0.1, "ENAHO 2024 módulos 02+34, facpob07"),
        ("E4", "enaho", "Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria del departamento de Lima (ubigeo 15, "
         "sin Callao), en %?", dep["15"], None, 0.1, "ENAHO 2024 sumaria, ubigeo 15, factor07 × mieperho"),
        ("C1", "mixta", "En diciembre de 2024, ¿cuántos puntos porcentuales estaba la inflación a 12 meses de alimentos y "
         "bebidas de Lima por encima (positivo) o por debajo (negativo) de la inflación total? Y según la ENAHO 2024, "
         "¿cuántos puntos superaba la pobreza rural a la urbana? Responde valor_1 y valor_2.",
         ali["2024-12"] - ipc["2024-12"], rural - urbana, 0.05, "BCRP PN09822PM − PN01273PM; ENAHO rural − urbana"),
        ("C2", "mixta", "¿Cuál fue el promedio de la inflación a 12 meses de Lima en los 12 meses de 2024 (BCRP), y cuál fue "
         "la tasa de pobreza monetaria de Cajamarca según la ENAHO 2024? Responde valor_1 y valor_2.",
         ipc["2024-01":"2024-12"].mean(), dep["06"], 0.05, "BCRP PN01273PM promedio 2024; ENAHO ubigeo 06"),
    ]
    df = pd.DataFrame(P, columns=["id", "tipo", "pregunta", "verdad", "verdad_2", "tolerancia", "fuente_esperada"])
    df[["verdad", "verdad_2"]] = df[["verdad", "verdad_2"]].astype(float).round(4)
    df.to_csv(AQUI / "preguntas.csv", index=False)
    print(df[["id", "verdad", "verdad_2", "tolerancia", "fuente_esperada"]].to_string(index=False))


if __name__ == "__main__":
    main()
