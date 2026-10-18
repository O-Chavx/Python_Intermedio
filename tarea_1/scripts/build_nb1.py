import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Tarea 1 – Parte 1: Recolección, limpieza y EDA

**Pregunta guía:** ¿Pueden convertir titulares peruanos en un clasificador de noticias?

| Parámetro | Valor |
|---|---|
| Opción elegida | **A – La República** |
| Fecha de descarga | **17 de octubre de 2026** (también queda guardada en `datos/raw/fecha_descarga.txt`) |
| URL base | https://larepublica.pe |
| Canales RSS oficiales | `/rss/politica.xml`, `/rss/economia.xml`, `/rss/deportes.xml`, `/rss/ciencia.xml`, `/rss/home.xml` |
| Sitemaps de noticias | `/sitemap/{seccion}.xml`, `/sitemap/web/{seccion}.xml`, `/sitemap/noticias.xml` |
| Categorías finales | `politica`, `economia`, `deportes`, `ciencia_tecnologia` |

### Estrategia de extracción (y por qué)
1. **robots.txt revisado**: permite `/rss/*`, `/sitemap/*` y las páginas de noticia; prohíbe la paginación de secciones (`/*/pag/*`, `/*/*/page/*`), búsquedas, `/tag/*` y `/archivo/*`.
2. **RSS/sitemaps como semilla**: cada feed solo trae las ~10–25 notas más recientes, insuficiente para ~100 por categoría. Además `/rss/tecnologia.xml` responde **410 Gone**.
3. **Bloqueo documentado**: el botón *“Ver más noticias”* de cada sección usa `/api/search/articles`, que responde **403 Forbidden** a clientes que no son navegador. **No se intenta evadir** ese bloqueo.
4. **Solución**: se visitan las páginas de noticia (permitidas por robots.txt) obtenidas del RSS y se siguen los enlaces a *otras noticias de la misma sección* que cada artículo enlaza (“más noticias”, relacionadas). De cada página se lee `og:title`, `og:description` (bajada) y `mrf:sections`.
5. **Buenas prácticas**: `User-Agent` descriptivo, pausa de **1.5 s** entre solicitudes, **máximo 1 reintento**, timeout de 20 s, y caché en `datos/raw/` para no volver a descargar lo ya descargado si el notebook se reejecuta.
""")

code(r"""
import json, re, time, random
from datetime import datetime
from pathlib import Path
from collections import Counter, deque

import requests
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.io as pio

pio.renderers.default = "plotly_mimetype+png"
pd.set_option("display.max_colwidth", 120)

BASE = "https://larepublica.pe"
MEDIO = "La Republica"
HEADERS = {"User-Agent": "TareaCursoPython/1.0 (proyecto academico; titulares para clasificador; contacto via GitHub)"}
PAUSA = 1.5
OBJETIVO_POR_CAT = 115
DATOS = Path("datos"); RAW = DATOS / "raw"; RAW.mkdir(parents=True, exist_ok=True)

REDESCARGAR = False
archivo_fecha = RAW / "fecha_descarga.txt"
if REDESCARGAR or not archivo_fecha.exists():
    archivo_fecha.write_text(datetime.now().strftime("%Y-%m-%d %H:%M"), encoding="utf-8")
FECHA_DESCARGA = archivo_fecha.read_text(encoding="utf-8")
print("Fecha de descarga:", FECHA_DESCARGA)
""")

md("## 1. Revisión de robots.txt")
code(r"""
robots = requests.get(f"{BASE}/robots.txt", headers=HEADERS, timeout=20).text
(RAW / "robots.txt").write_text(robots, encoding="utf-8")
reglas = [l for l in robots.splitlines() if l.startswith(("Disallow", "Allow"))]
print("\n".join(reglas))
""")

md("## 2. Funciones de descarga con pausa y 1 reintento")
code(r"""
sesion = requests.Session()
sesion.headers.update(HEADERS)
log_peticiones = []

def descargar(url, reintentos=1):
    for intento in range(reintentos + 1):
        time.sleep(PAUSA)
        try:
            r = sesion.get(url, timeout=20)
            log_peticiones.append({"url": url, "status": r.status_code})
            if r.status_code == 200:
                return r
            if r.status_code in (403, 404, 410):
                return r
        except requests.RequestException as e:
            log_peticiones.append({"url": url, "status": f"error: {e.__class__.__name__}"})
    return None

r_api = descargar(f"{BASE}/api/search/articles?category_slug=politica&limit=12&page=2&order_by=update_date&view=section", reintentos=0)
r_tec = descargar(f"{BASE}/rss/tecnologia.xml", reintentos=0)
print("API 'Ver más noticias' ->", r_api.status_code if r_api is not None else None)
print("RSS tecnologia        ->", r_tec.status_code if r_tec is not None else None)
""")

md("## 3. Semillas: RSS oficiales y sitemaps de noticias (respaldo crudo en `datos/raw/`)")
code(r"""
SECCIONES_OBJETIVO = ["politica", "economia", "deportes", "ciencia", "tecnologia"]
FEEDS = (["rss/home.xml", "sitemap/noticias.xml", "sitemap/web/noticias.xml"]
         + [f"rss/{s}.xml" for s in ["politica", "economia", "deportes", "ciencia"]]
         + [f"sitemap/{s}.xml" for s in ["politica", "economia", "deportes", "ciencia"]]
         + [f"sitemap/web/{s}.xml" for s in ["politica", "economia", "deportes", "ciencia"]])

PATRON_NOTA = re.compile(r"^https://larepublica\.pe/((?:[a-z0-9-]+/)*?)(20\d\d)/(\d\d)/(\d\d)/[a-z0-9-]+-\d+/?$")

def limpiar(t):
    return re.sub(r"\s+", " ", t or "").strip()

registros_rss = []
for feed in FEEDS:
    respaldo = RAW / feed.replace("/", "_")
    if REDESCARGAR or not respaldo.exists():
        r = descargar(f"{BASE}/{feed}")
        if r is None or r.status_code != 200:
            print(f"{feed}: sin respuesta"); continue
        respaldo.write_bytes(r.content)
    soup = BeautifulSoup(respaldo.read_bytes(), "xml")
    n = 0
    for it in soup.find_all("item"):
        registros_rss.append({"url": limpiar(it.link.text), "titular": limpiar(it.title.text),
                              "bajada": limpiar(it.description.text if it.description else ""),
                              "fecha_raw": limpiar(it.pubDate.text if it.pubDate else ""), "fuente": feed}); n += 1
    for it in soup.find_all("url"):
        t = it.find("title")
        registros_rss.append({"url": limpiar(it.loc.text), "titular": limpiar(t.text if t else ""), "bajada": "",
                              "fecha_raw": limpiar(it.find("publication_date").text if it.find("publication_date") else ""),
                              "fuente": feed}); n += 1
    print(f"{feed:28s} {n:4d} items")

semillas = pd.DataFrame(registros_rss)
print("Total items en feeds:", len(semillas), "| URLs únicas:", semillas.url.nunique())
""")

md("""
## 4. Extracción de cada noticia y expansión por enlaces de la misma sección
Cada página de noticia aporta `titular`, `bajada`, `seccion_original`, `fecha` y enlaces a otras notas.
Se avanza por sección hasta alcanzar el objetivo. Lo ya descargado se guarda en `datos/raw/articulos.jsonl` y se reutiliza.
""")
code(r"""
RAW_ART = RAW / "articulos.jsonl"
cache = {}
if RAW_ART.exists():
    for linea in RAW_ART.read_text(encoding="utf-8").splitlines():
        d = json.loads(linea); cache[d["url"]] = d
print("Artículos ya en caché:", len(cache))

def seccion_de(url):
    m = PATRON_NOTA.match(url)
    return m.group(1).strip("/") if m else None

def extraer_articulo(url):
    r = descargar(url)
    if r is None or r.status_code != 200:
        return {"url": url, "ok": False, "status": getattr(r, "status_code", None)}
    s = BeautifulSoup(r.text, "lxml")
    meta = lambda k: (s.find("meta", attrs={"property": k}) or s.find("meta", attrs={"name": k}) or {}).get("content", "")
    h1 = s.find("h1")
    enlaces = set()
    for a in s.find_all("a", href=True):
        h = a["href"].split("?")[0].split("#")[0]
        if h.startswith("/"): h = BASE + h
        if PATRON_NOTA.match(h): enlaces.add(h)
    return {"url": url, "ok": True,
            "titular": limpiar(h1.get_text() if h1 else meta("og:title")),
            "bajada": limpiar(meta("og:description") or meta("description")),
            "seccion_meta": limpiar(meta("mrf:sections")),
            "fecha_meta": meta("article:published_time"),
            "enlaces": sorted(enlaces)}

def guardar(d):
    with RAW_ART.open("a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

def categoria_url(url):
    sec = seccion_de(url) or ""
    raiz = sec.split("/")[0]
    return {"ciencia": "ciencia_tecnologia", "tecnologia": "ciencia_tecnologia"}.get(raiz, raiz)

CATS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
colas = {c: deque() for c in CATS}
vistos = set()
def encolar(url):
    c = categoria_url(url)
    if c in colas and url not in vistos:
        vistos.add(url); colas[c].append(url)

for u in semillas.url: encolar(u)
for d in list(cache.values()):
    for e in d.get("enlaces", []): encolar(e)

conteo = Counter(categoria_url(u) for u, d in cache.items() if d.get("ok"))
MAX_PETICIONES = 700
peticiones = 0
for c in CATS:
    while conteo[c] < OBJETIVO_POR_CAT and colas[c] and peticiones < MAX_PETICIONES:
        u = colas[c].popleft()
        if u in cache: continue
        d = extraer_articulo(u); peticiones += 1
        cache[u] = d; guardar(d)
        if d["ok"]:
            conteo[c] += 1
            for e in d["enlaces"]: encolar(e)
    print(f"{c:20s} descargadas={conteo[c]:4d}  cola restante={len(colas[c])}")
print("Peticiones nuevas en esta ejecución:", peticiones)
""")

code(r"""
filas = []
for u in semillas.url.unique():
    if u not in cache:
        s = semillas[semillas.url == u].iloc[0]
        filas.append({"url": u, "ok": True, "titular": s.titular, "bajada": s.bajada, "seccion_meta": "",
                      "fecha_meta": s.fecha_raw, "origen": "rss"})
for u, d in cache.items():
    filas.append({**{k: v for k, v in d.items() if k != "enlaces"}, "origen": "html"})
crudo = pd.DataFrame(filas)
crudo["medio"] = MEDIO
crudo["seccion_original"] = crudo.url.map(seccion_de)
f = crudo.url.str.extract(r"/(20\d\d)/(\d\d)/(\d\d)/")
crudo["fecha"] = f[0] + "-" + f[1] + "-" + f[2]
crudo.to_csv(RAW / "crudo_completo.csv", index=False, encoding="utf-8")
print("Registros crudos:", crudo.shape)
pd.DataFrame(log_peticiones).status.astype(str).value_counts()
""")

md("## 5. Limpieza y normalización")
code(r"""
descartes = []
df = crudo.copy()
def descartar(mask, motivo):
    global df
    descartes.append({"motivo": motivo, "n": int(mask.sum())})
    df = df[~mask]

descartar(~df.ok.fillna(False).astype(bool), "Página no disponible (error HTTP)")
descartar(df.url.duplicated(), "URL duplicada")
df["titular"] = df.titular.fillna("").map(limpiar)
df["bajada"] = df.bajada.fillna("").map(limpiar)
descartar(df.titular.str.len() == 0, "Titular vacío")
descartar(df.titular.str.lower().duplicated(), "Titular duplicado (misma nota con otra URL)")
print(df.shape)
""")

md("""
### Tabla de equivalencias `seccion_original` → `etiqueta`
La regla es explícita sobre la **raíz** de la sección en la URL. Cualquier otra sección (sociedad, mundo, espectáculos, opinión, etc.) **no encaja** en las 4 categorías y se descarta (no se crea una 5.ª categoría).
""")
code(r"""
MAPEO_RAIZ = {"politica": "politica", "economia": "economia", "deportes": "deportes",
              "ciencia": "ciencia_tecnologia", "tecnologia": "ciencia_tecnologia"}
df["etiqueta"] = df.seccion_original.fillna("").str.split("/").str[0].map(MAPEO_RAIZ)

tabla_mapeo = (df.groupby("seccion_original", dropna=False)
                 .agg(etiqueta=("etiqueta", lambda s: s.iloc[0] if s.notna().any() else "DESCARTADA"), noticias=("url", "size"))
                 .reset_index().sort_values(["etiqueta", "noticias"], ascending=[True, False]))
tabla_mapeo
""")

code(r"""
fuera = df.etiqueta.isna()
print("Secciones descartadas por no encajar:", df[fuera].seccion_original.value_counts().to_dict())
descartar(fuera, "Sección fuera de las 4 categorías (sociedad, mundo, espectáculos, etc.)")

plantilla = df.titular.str.lower().str.replace(r"\d+|lunes|martes|miércoles|jueves|viernes|sábado|domingo|de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)", "", regex=True).str[:45]
descartar(plantilla.duplicated(), "Nota repetitiva diaria (misma plantilla de titular)")

df = df.sort_values("fecha", ascending=False)
exceso = df.groupby("etiqueta").cumcount() >= 100
descartar(exceso, "Excedente para balancear (máx. 100 por categoría)")

reporte_descartes = pd.DataFrame(descartes)
print("Noticias finales:", len(df), "| descartadas:", reporte_descartes.n.sum())
reporte_descartes
""")

md("## 6. Análisis exploratorio (Plotly Express)")
code(r"""
df["largo_titular"] = df.titular.str.len()
dist = df.etiqueta.value_counts().rename_axis("etiqueta").reset_index(name="noticias")
fig1 = px.bar(dist, x="etiqueta", y="noticias", text="noticias", color="etiqueta",
              title=f"Dataset perfectamente balanceado: {dist.noticias.min()} titulares en cada una de las 4 categorías ({len(df)} en total)" if dist.noticias.nunique() == 1
                    else f"Dataset casi balanceado: {dist.noticias.min()}–{dist.noticias.max()} titulares por categoría ({len(df)} en total)")
fig1.update_layout(showlegend=False); fig1.show()
""")
code(r"""
dias = (pd.Timestamp(FECHA_DESCARGA[:10]) - pd.to_datetime(df.fecha)).dt.days
orden = ["0–7 días", "8–30 días", "1–6 meses", "más de 6 meses"]
df["antiguedad"] = pd.cut(dias, [-1, 7, 30, 182, 10**5], labels=orden)
por_rango = df.groupby(["antiguedad", "etiqueta"], observed=False).size().reset_index(name="noticias")
pct_mes = (dias <= 30).mean()
mas_vieja = df.groupby("etiqueta").fecha.min().idxmin()
fig2 = px.bar(por_rango, x="antiguedad", y="noticias", color="etiqueta", barmode="group", category_orders={"antiguedad": orden},
              title=f"El {pct_mes:.0%} de las notas es del último mes; {mas_vieja} arrastra las notas más antiguas (desde {df.fecha.min()})")
fig2.show()
print("Rango de fechas por categoría:"); display(df.groupby("etiqueta").fecha.agg(["min", "max"]))
""")
code(r"""
med = df.groupby("etiqueta").largo_titular.median().sort_values()
fig3 = px.histogram(df, x="largo_titular", color="etiqueta", nbins=30, barmode="overlay", opacity=0.6,
                    labels={"largo_titular": "caracteres del titular"},
                    title=f"Titulares de {med.index[-1]} son los más largos (mediana {med.iloc[-1]:.0f} car.) y los de {med.index[0]} los más cortos ({med.iloc[0]:.0f})")
fig3.show()
df.groupby("etiqueta").largo_titular.describe().round(1)
""")

md("## 7. Validación: titulares más largos y más cortos")
code(r"""
cols = ["titular", "etiqueta", "largo_titular"]
print("5 titulares MÁS LARGOS"); display(df.nlargest(5, "largo_titular")[cols])
print("5 titulares MÁS CORTOS"); display(df.nsmallest(5, "largo_titular")[cols])
print(f"Rango observado: {df.largo_titular.min()}–{df.largo_titular.max()} caracteres, coherente con los extremos del histograma.")
""")

md("## 8. Exportación de `datos/noticias.csv`")
code(r"""
COLUMNAS = ["titular", "bajada", "medio", "seccion_original", "url", "fecha", "etiqueta"]
final = df[COLUMNAS].reset_index(drop=True)
final.to_csv(DATOS / "noticias.csv", index=False, encoding="utf-8")
print(final.shape)
final.head()
""")
code(r"""
muestra = final.sample(10, random_state=42).url
estados = {u: (descargar(u, reintentos=0) or type("x", (), {"status_code": None})).status_code for u in muestra}
print(Counter(estados.values()))
""")

md("""
## Conclusiones de la Parte 1
- Se usó RSS + sitemaps oficiales como semilla y páginas de noticia (permitidas en robots.txt) para alcanzar el volumen; el endpoint “Ver más” (403) **no** se usó.
- Las notas fuera de las 4 categorías y las plantillas repetitivas se descartaron y se reportan en la tabla de descartes.
- El dataset final queda balanceado y listo para el etiquetado con LLM en `02_clasificacion.ipynb`.
""")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = Path(__file__).resolve().parents[1] / "01_recoleccion.ipynb"
nbf.write(nb, out)
print("escrito", out)
