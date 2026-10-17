"""Dashboard Tarea 1 – Clasificador de titulares peruanos (La República)."""
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
DATOS, MODELO = BASE / "datos", BASE / "modelo"
CATS = ["politica", "economia", "deportes", "ciencia_tecnologia"]
COLORES = dict(zip(CATS, px.colors.qualitative.Set2))

st.set_page_config(page_title="Titulares peruanos → clasificador", page_icon="🗞️", layout="wide")


@st.cache_data
def cargar_datos():
    df = pd.read_csv(DATOS / "noticias.csv")
    llm = pd.read_csv(DATOS / "etiquetas_llm.csv")
    df["etiqueta_llm"] = llm["etiqueta_llm"].values
    df["confianza_llm"] = llm["confianza"].values
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    return df


@st.cache_data
def cargar_metricas():
    ruta = MODELO / "metricas.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


@st.cache_resource
def cargar_clasificador():
    """BETO fine-tuned local -> BETO desde Hugging Face Hub -> TF-IDF ligero (respaldo)."""
    origen = MODELO if (MODELO / "model.safetensors").exists() else os.environ.get("HF_MODEL_ID")
    if origen:
        try:
            from transformers import pipeline
            clf = pipeline("text-classification", model=str(origen), tokenizer=str(origen), top_k=None)
            return (lambda t: {d["label"]: d["score"] for d in clf(t)[0]}), "BETO fine-tuned"
        except Exception as e:  # pragma: no cover - sólo si falla la descarga
            st.warning(f"No se pudo cargar BETO ({e.__class__.__name__}); se usa el modelo ligero.")
    import joblib
    tfidf = joblib.load(MODELO / "tfidf_lr.joblib")
    return (lambda t: dict(zip(tfidf.classes_, tfidf.predict_proba([t])[0]))), "TF-IDF + Regresión logística (respaldo ligero)"


df = cargar_datos()
met = cargar_metricas()

# ---------------- Encabezado ----------------
st.title("🗞️ ¿Pueden convertirse los titulares peruanos en un clasificador de noticias?")
st.markdown(
    f"""
**Metodología:** {len(df)} titulares de **La República** (RSS + sitemaps oficiales y páginas de noticia, respetando robots.txt)
→ mapeo de la sección del diario a 4 categorías → **etiquetado débil con un LLM local (Qwen2.5-1.5B-Instruct)** auditado a mano
→ **fine-tuning de BETO** (`dccuchile/bert-base-spanish-wwm-cased`) con split estratificado 70/15/15
→ evaluación en un **test reservado** contra la sección editorial.
"""
)

# ---------------- Filtros ----------------
st.sidebar.header("Filtros")
medios = st.sidebar.multiselect("Medio", sorted(df.medio.unique()), default=sorted(df.medio.unique()))
cats = st.sidebar.multiselect("Categoría", CATS, default=CATS)
f_min, f_max = df.fecha.min(), df.fecha.max()
rango = st.sidebar.date_input("Rango de fechas", (f_min, f_max), min_value=f_min, max_value=f_max)
fil = df[df.medio.isin(medios) & df.etiqueta.isin(cats)]
if isinstance(rango, tuple) and len(rango) == 2:
    fil = fil[(fil.fecha >= rango[0]) & (fil.fecha <= rango[1])]
st.sidebar.caption(f"{len(fil)} de {len(df)} noticias seleccionadas")

# ---------------- KPIs ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Noticias recolectadas", f"{len(df)}", f"{len(fil)} en el filtro", delta_color="off")
c2.metric("F1 macro en test (BETO)", f"{met.get('f1_macro_test', float('nan')):.3f}",
          f"+{met.get('f1_macro_test', 0) - met.get('f1_zero_shot', 0):.3f} vs. zero-shot")
c3.metric("Acuerdo LLM vs. auditoría humana", f"{met.get('acuerdo_llm_humano_pct', 0):.0%}",
          met.get("acuerdo_llm_humano", ""), delta_color="off")
c4.metric("Acuerdo LLM vs. sección del diario", f"{met.get('acuerdo_llm_seccion', 0):.1%}")

# ---------------- Probador en vivo ----------------
st.subheader("🔮 Probador en vivo")
clasificar, nombre_modelo = cargar_clasificador()
col_in, col_out = st.columns([3, 2])
with col_in:
    titular = st.text_area("Escribe o pega un titular nuevo",
                           "Selección peruana convoca a nuevos jugadores para las Eliminatorias", height=90)
    boton = st.button("Clasificar titular", type="primary")
    st.caption(f"Modelo en uso: {nombre_modelo}")
with col_out:
    if boton and titular.strip():
        probs = pd.Series(clasificar(titular.strip())).reindex(CATS).fillna(0).sort_values()
        st.success(f"Categoría predicha: **{probs.idxmax()}**  ·  probabilidad **{probs.max():.1%}**")
        fig_p = px.bar(probs, orientation="h", range_x=[0, 1], color=probs.index, color_discrete_map=COLORES,
                       labels={"value": "probabilidad", "index": ""})
        fig_p.update_layout(showlegend=False, height=230, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_p, width="stretch")
    elif boton:
        st.warning("Escribe un titular primero.")

# ---------------- Exploración ----------------
st.subheader("📊 Distribución de categorías en la selección")
g1, g2 = st.columns(2)
dist = fil.etiqueta.value_counts().reindex(cats).fillna(0).rename_axis("categoria").reset_index(name="noticias")
g1.plotly_chart(px.bar(dist, x="categoria", y="noticias", color="categoria", color_discrete_map=COLORES, text="noticias",
                       title="Noticias por categoría").update_layout(showlegend=False), width="stretch")
cruce = fil.groupby(["etiqueta", "etiqueta_llm"]).size().reset_index(name="n")
g2.plotly_chart(px.density_heatmap(cruce, x="etiqueta_llm", y="etiqueta", z="n", text_auto=True,
                                   title="Sección del diario vs. etiqueta del LLM",
                                   labels={"etiqueta": "sección", "etiqueta_llm": "LLM"}), width="stretch")

st.subheader("🗂️ Datos")
cols = ["fecha", "etiqueta", "etiqueta_llm", "titular", "bajada", "seccion_original", "url"]
st.dataframe(fil[cols], width="stretch", hide_index=True,
             column_config={"url": st.column_config.LinkColumn("url")})
st.download_button("⬇️ Descargar CSV filtrado", fil[cols].to_csv(index=False).encode("utf-8"),
                   "noticias_filtradas.csv", "text/csv")

comp = MODELO / "comparativa.csv"
if comp.exists():
    with st.expander("Comparativa de modelos (test)"):
        st.dataframe(pd.read_csv(comp), hide_index=True, width="stretch")
