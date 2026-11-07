"""Experimento: las mismas 10 preguntas a Claude Code sin (Modo A) y con (Modo B) el MCP del BCRP y las Skills.

    uv run evaluacion/evaluar.py                     # ambos modos, modelo sonnet
    uv run evaluacion/evaluar.py --modos A --ids B1 E2

Cada pregunta es una sesión nueva de `claude -p` (sin memoria entre preguntas, --no-session-persistence) que debe
responder un JSON. Las respuestas esperadas están en preguntas.csv (las calculó respuestas_esperadas.py antes de
correr esto) y el agente nunca ve ese archivo:

- Modo A corre en una carpeta temporal vacía: sin MCP (--strict-mcp-config sin config), sin Skills
  (--disallowedTools Skill) y sin los archivos del proyecto. Solo tiene WebSearch y WebFetch.
- Modo B corre en una copia del proyecto SIN evaluacion/, informes/, evidencias_ia/ ni resultados previos
  (salidas/, figuras/ y mapas/ vacías, así que las Skills tienen que correr): tiene el MCP bcrp, las Skills
  y Bash(uv run *) para ejecutarlas, y también WebSearch y WebFetch.

Guarda cada transcripción en evidencias_ia/evaluacion/ y la tabla en evaluacion/resultados.csv.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).parents[1]
EVID = RAIZ / "evidencias_ia" / "evaluacion"
ESQUEMA = {"type": "object", "required": ["valor", "fuente"],
           "properties": {"valor": {"type": ["number", "null"]}, "valor_2": {"type": ["number", "null"]},
                          "fuente": {"type": "string"}, "interpretacion": {"type": "string"}}}
INSTRUCCION = ("Responde con números en «valor» (y en «valor_2» si la pregunta pide dos), en la unidad que pide la "
               "pregunta. Si no puedes obtener la cifra con certeza, pon null: no estimes. En «fuente» di de dónde sale "
               "cada cifra (código de serie y periodo, o base de datos y método). En «interpretacion», una frase.\n\n")
WEB = "WebSearch,WebFetch"
MODOS = {
    "A": ["--strict-mcp-config", "--tools", WEB, "--allowedTools", WEB, "--disallowedTools", "Skill"],
    "B": ["--strict-mcp-config", "--mcp-config", ".mcp.json",
          "--allowedTools", f"mcp__bcrp,Skill,Bash(uv run *),Read,Glob,{WEB}"],
}
NO_COPIAR = {"evaluacion", "informes", "evidencias_ia", "salidas", "figuras", "mapas", ".venv", ".git", ".pytest_cache",
             "__pycache__"}


def carpeta(modo):
    d = Path(tempfile.mkdtemp(prefix=f"t4_{modo}_"))
    if modo == "B":
        for p in RAIZ.iterdir():
            if p.name in NO_COPIAR:
                continue
            (shutil.copytree if p.is_dir() else shutil.copy2)(p, d / p.name)
        for vacia in ("salidas", "figuras", "mapas"):   # sin resultados previos: las Skills deben correr
            (d / vacia).mkdir()
    return d


def preguntar(q, modo, modelo):
    d = carpeta(modo)
    cmd = ["claude", "-p", INSTRUCCION + q.pregunta, "--output-format", "stream-json", "--verbose",
           "--json-schema", json.dumps(ESQUEMA), "--no-session-persistence", "--model", modelo, *MODOS[modo]]
    t = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, cwd=d)
        salida = proc.stdout
    except subprocess.TimeoutExpired as e:
        salida = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    segundos = round(time.time() - t, 1)
    (EVID / f"{modo}_{q.id}.jsonl").write_text(salida, encoding="utf-8")
    herramientas, final = [], {}
    for linea in salida.splitlines():
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "assistant":
            herramientas += [c["name"] if c["name"] != "Skill" else f"Skill:{c['input'].get('skill')}"
                             for c in e["message"]["content"] if c.get("type") == "tool_use"]
        if e.get("type") == "result":
            final = e
    r = final.get("structured_output") or {}
    shutil.rmtree(d, ignore_errors=True)
    return {"valor": r.get("valor"), "valor_2": r.get("valor_2"), "fuente_respuesta": r.get("fuente", ""),
            "interpretacion": r.get("interpretacion", ""), "herramientas": ";".join(dict.fromkeys(herramientas)),
            "n_llamadas": len(herramientas), "segundos": segundos,
            "error": "" if final.get("subtype") == "success" and r else (final.get("subtype") or "sin respuesta")}


def cerca(v, verdad, tol):
    return v is not None and not pd.isna(v) and abs(float(v) - verdad) <= tol


def calificar(q, r):
    if r["valor"] is None:
        return "no contesta"
    ok = cerca(r["valor"], q.verdad, q.tolerancia)
    if q.tipo == "mixta":   # exige las dos cifras y una interpretación sin lenguaje causal
        # afirmaciones causales; «causal» a secas no cuenta, para no castigar «no es una relación causal»
        texto = str(r["interpretacion"]).lower()
        causal = any(w in texto for w in ("causó", "causa la", "causa el", "provoc", "debido a", "se debe a",
                                          "explica", "por culpa"))
        ok = ok and cerca(r["valor_2"], q.verdad_2, q.tolerancia) and not causal
    return "correcta" if ok else "incorrecta"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--modelo", default="sonnet")
    p.add_argument("--ids", nargs="*")
    p.add_argument("--paralelo", type=int, default=4)
    p.add_argument("--recalificar", action="store_true", help="vuelve a calificar resultados.csv sin llamar a Claude")
    a = p.parse_args()
    if a.recalificar:
        destino = RAIZ / "evaluacion" / "resultados.csv"
        res = pd.read_csv(destino)
        res["resultado"] = [calificar(q, {"valor": None if pd.isna(q.valor) else q.valor, "valor_2": q.valor_2,
                                          "interpretacion": q.interpretacion}) for q in res.itertuples()]
        res.to_csv(destino, index=False)
        print(res.groupby("modo").resultado.value_counts().unstack(fill_value=0))
        raise SystemExit
    EVID.mkdir(parents=True, exist_ok=True)
    preguntas = pd.read_csv(RAIZ / "evaluacion" / "preguntas.csv")
    if a.ids:
        preguntas = preguntas[preguntas.id.isin(a.ids)]
    casos = [(q, m) for q in preguntas.itertuples() for m in a.modos]
    print(f"{len(casos)} sesiones de claude -p con {a.modelo}...")
    with ThreadPoolExecutor(a.paralelo) as ex:
        resp = list(ex.map(lambda c: preguntar(c[0], c[1], a.modelo), casos))
    filas = [{"id": q.id, "tipo": q.tipo, "modo": m, "modelo": a.modelo, "pregunta": q.pregunta, "verdad": q.verdad,
              "verdad_2": q.verdad_2, "tolerancia": q.tolerancia, "fuente_esperada": q.fuente_esperada, **r,
              "resultado": calificar(q, r)} for (q, m), r in zip(casos, resp)]
    res = pd.DataFrame(filas)
    destino = RAIZ / "evaluacion" / "resultados.csv"
    if a.ids and destino.exists():   # re-correr algunas preguntas reemplaza solo esas filas
        viejo = pd.read_csv(destino)
        viejo = viejo[~(viejo.id.isin(a.ids) & viejo.modo.isin(a.modos))]
        res = pd.concat([viejo, res]).sort_values(["modo", "id"])
    res.to_csv(destino, index=False)
    print(res.groupby("modo").resultado.value_counts().unstack(fill_value=0))
    print(res.groupby("modo").segundos.mean().round(1))
