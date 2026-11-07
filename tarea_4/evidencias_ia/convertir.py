"""Convierte las transcripciones de `claude -p --output-format stream-json` (.jsonl) en Markdown legible.

    uv run evidencias_ia/convertir.py

Cada .md muestra, en orden: el pedido, los textos del asistente, cada herramienta llamada con sus argumentos y el
resultado (recortado a 1,500 caracteres). Los .jsonl originales quedan al lado, completos.
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
OCULTAR = [(re.compile(r"sk-ant-[A-Za-z0-9_-]+"), "[CLAVE OCULTA]"),
           (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[TOKEN OCULTO]"),
           (re.compile(r"[A-Za-z0-9._%+\\-]+@(gmail|hotmail|outlook|yahoo)[\\.]+com"), "[correo oculto]"),
           (re.compile(r"/tmp/claude-0/[^\s\"']*?/tarea_4/"), "tarea_4/"),
           (re.compile(r"/tmp/claude-0/[^\s\"']*?/t4_[AB]_[a-z0-9_]+/"), "<carpeta temporal>/")]


def limpiar(t):
    for patron, reemplazo in OCULTAR:
        t = patron.sub(reemplazo, t)
    return t


def convertir(ruta):
    md = [f"# Transcripción: {ruta.stem}", "", f"Archivo original: `{ruta.name}`", ""]
    pedido = ruta.with_name("prompt.txt")
    if pedido.exists():
        md += ["## Pedido del usuario (argumento de `claude -p`)", "", pedido.read_text(encoding="utf-8").strip(), ""]
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            continue
        tipo = e.get("type")
        if tipo == "system" and e.get("subtype") == "init":
            md += [f"**Sesión:** modelo `{e.get('model')}` · MCP: {[s['name'] + ' ' + s['status'] for s in e.get('mcp_servers', [])]}",
                   ""]
        elif tipo in ("user", "assistant"):
            contenido = e["message"]["content"]
            if isinstance(contenido, str):
                md += [f"## {'Usuario' if tipo == 'user' else 'Claude'}", "", contenido, ""]
                continue
            for c in contenido:
                if c.get("type") == "text" and c["text"].strip():
                    md += [f"## {'Usuario' if tipo == 'user' else 'Claude'}", "", c["text"], ""]
                elif c.get("type") == "tool_use":
                    md += [f"### → Herramienta `{c['name']}`", "", "```json",
                           json.dumps(c["input"], ensure_ascii=False, indent=1)[:3000], "```", ""]
                elif c.get("type") == "tool_result":
                    r = c.get("content")
                    if isinstance(r, list):
                        r = "\n".join(x.get("text", "[imagen]") for x in r)
                    r = str(r)
                    md += ["<details><summary>Resultado</summary>", "", "```", r[:1500] + (" […]" if len(r) > 1500 else ""),
                           "```", "</details>", ""]
        elif tipo == "result":
            md += ["---", f"**Fin:** {e.get('subtype')} · {e.get('num_turns')} turnos · "
                   f"{round(e.get('duration_ms', 0) / 1000)} s · US$ {e.get('total_cost_usd', 0):.2f}", ""]
            if e.get("structured_output"):
                md += ["Respuesta estructurada:", "", "```json",
                       json.dumps(e["structured_output"], ensure_ascii=False, indent=1), "```"]
    ruta.with_suffix(".md").write_text(limpiar("\n".join(md)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for r in sorted(AQUI.rglob("*.jsonl")):
        convertir(r)
        r.write_text(limpiar(r.read_text(encoding="utf-8")), encoding="utf-8")
        print("ok", r.relative_to(AQUI))
