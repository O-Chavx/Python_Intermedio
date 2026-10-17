"""Genera 02_clasificacion.ipynb a partir de celdas definidas aqui (luego se ejecuta con nbconvert)."""
import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md("""
# Tarea 1 – Parte 2: Del LLM al clasificador

Flujo del notebook:
1. **Partición 70/15/15** estratificada (`random_state=42`). Se hace primero para que el conjunto de **test quede aislado desde el inicio**: ningún paso posterior lo usa para entrenar ni para elegir hiperparámetros.
2. **Línea base zero-shot** (`Recognai/bert-base-spanish-wwm-cased-xnli`) sobre 40 titulares del test.
3. **Supervisión débil con LLM** (Gemini) sobre el dataset completo → `datos/etiquetas_llm.csv` + **auditoría humana de 20 casos**.
4. **Fine-tuning de BETO** (`dccuchile/bert-base-spanish-wwm-cased`) entrenado con las **etiquetas del LLM** (train/val).
5. **Evaluación final en test** contra la etiqueta editorial (sección del diario), que es independiente del LLM.
6. **Comparativa** zero-shot vs. LLM vs. fine-tuned y decisión.
""")

code(r"""
import os, json, time, random
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix

SEED = 42
random.seed(SEED); np.random.seed(SEED)
DATOS, MODELO = Path("datos"), Path("modelo")
MODELO.mkdir(exist_ok=True)
CATS = ["politica", "economia", "deportes", "ciencia_tecnologia"]

df = pd.read_csv(DATOS / "noticias.csv")
print(df.shape); df.etiqueta.value_counts()
""")

md("## 1. Partición estratificada 70 / 15 / 15 (semilla 42)")
code(r"""
train_df, temp_df = train_test_split(df, test_size=0.30, stratify=df.etiqueta, random_state=SEED)
val_df, test_df = train_test_split(temp_df, test_size=0.50, stratify=temp_df.etiqueta, random_state=SEED)
for n, d in [("train", train_df), ("val", val_df), ("test", test_df)]:
    print(f"{n:5s} {len(d):4d} ({len(d)/len(df):.0%})", d.etiqueta.value_counts().to_dict())
assert not set(test_df.url) & set(train_df.url) and not set(test_df.url) & set(val_df.url)
""")

md("""
## 2. Línea base zero-shot (sin fine-tuning)
Se evalúan **40 titulares del test** (10 por categoría). Las etiquetas candidatas se expresan en lenguaje natural para el modelo NLI.
""")
code(r"""
from transformers import pipeline
ZS_MODEL = "Recognai/bert-base-spanish-wwm-cased-xnli"
zs = pipeline("zero-shot-classification", model=ZS_MODEL)
NOMBRES = {"politica": "política", "economia": "economía", "deportes": "deportes", "ciencia_tecnologia": "ciencia y tecnología"}
INV = {v: k for k, v in NOMBRES.items()}

zs_df = test_df.groupby("etiqueta").sample(10, random_state=SEED)
t0 = time.perf_counter()
res = zs(list(zs_df.titular), candidate_labels=list(NOMBRES.values()), hypothesis_template="Esta noticia trata sobre {}.")
zs_lat = (time.perf_counter() - t0) / len(zs_df)
zs_df = zs_df.assign(pred_zs=[INV[r["labels"][0]] for r in res], score_zs=[r["scores"][0] for r in res])

acc_zs = accuracy_score(zs_df.etiqueta, zs_df.pred_zs)
f1_zs = f1_score(zs_df.etiqueta, zs_df.pred_zs, average="macro")
print(f"Zero-shot (n=40)  Accuracy={acc_zs:.3f}  F1 macro={f1_zs:.3f}  latencia={zs_lat*1000:.0f} ms/titular")
print(classification_report(zs_df.etiqueta, zs_df.pred_zs, digits=3, zero_division=0))
""")

md("""
## 3. Supervisión débil con un LLM (Gemini)
Prompt estructurado con definición de cada categoría, salida **JSON con esquema fijo** y lotes de 25 noticias (menos llamadas → respeta el límite gratuito).
Se envían titular + bajada (más contexto para el etiquetador). La clave se lee de `.env` (no se sube a GitHub).
Si `datos/etiquetas_llm.csv` ya existe, se reutiliza para no repetir llamadas al API.
""")
code(r"""
PROMPT = '''Eres un editor de un diario peruano. Clasifica cada noticia en EXACTAMENTE una de estas 4 categorías:
- politica: Gobierno, Congreso, elecciones, partidos, justicia y fiscalía ligada a políticos, política exterior del Estado.
- economia: mercados, dólar, empresas, empleo, impuestos, inflación, comercio, finanzas personales, minería y pesca como actividad económica.
- deportes: fútbol y cualquier deporte, clubes, selecciones, deportistas, torneos.
- ciencia_tecnologia: ciencia, espacio, salud desde la investigación, medio ambiente científico, tecnología, apps, IA, videojuegos, celulares.
Devuelve, para cada id, la categoría y tu confianza entre 0 y 1.

Noticias:
{noticias}'''

ARCHIVO_LLM = DATOS / "etiquetas_llm.csv"
if ARCHIVO_LLM.exists():
    llm = pd.read_csv(ARCHIVO_LLM)
    print("Etiquetas LLM cargadas desde disco:", llm.shape)
else:
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types
    load_dotenv()
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    LLM_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    esquema = {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "integer"}, "etiqueta": {"type": "string", "enum": CATS}, "confianza": {"type": "number"}},
        "required": ["id", "etiqueta", "confianza"]}}
    salidas, tiempos = [], []
    for ini in range(0, len(df), 25):
        lote = df.iloc[ini:ini + 25]
        texto = "\n".join(f"{i}. {r.titular} — {r.bajada}" for i, r in lote.iterrows())
        for intento in range(3):
            try:
                t0 = time.perf_counter()
                resp = cliente.models.generate_content(model=LLM_MODEL, contents=PROMPT.format(noticias=texto),
                    config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json", response_schema=esquema))
                tiempos.append((time.perf_counter() - t0) / len(lote))
                salidas += json.loads(resp.text); break
            except Exception as e:
                print("reintento", ini, e.__class__.__name__); time.sleep(20)
        time.sleep(4)   # respeta el límite de solicitudes por minuto del plan gratuito
    pred = pd.DataFrame(salidas).drop_duplicates("id").set_index("id")
    llm = pd.DataFrame({"titular": df.titular, "etiqueta_llm": pred.etiqueta.reindex(df.index),
                        "confianza": pred.confianza.reindex(df.index).round(3),
                        "modelo_llm": LLM_MODEL, "fecha": datetime.now().strftime("%Y-%m-%d")})
    llm.to_csv(ARCHIVO_LLM, index=False, encoding="utf-8")
    json.dump({"latencia_llm_s_por_titular": float(np.mean(tiempos))}, open(MODELO / "latencia_llm.json", "w"))
    print("Etiquetas LLM generadas:", llm.shape)

assert len(llm) == len(df) and (llm.titular.values == df.titular.values).all()
print("Sin etiqueta:", llm.etiqueta_llm.isna().sum())
df["etiqueta_llm"] = llm.etiqueta_llm.values
df["confianza_llm"] = llm.confianza.values
llm.head()
""")

md("""
### 3.1 Auditoría humana de 20 predicciones al azar
Se toma una muestra aleatoria (`random_state=42`) y se revisa **a mano** leyendo titular y bajada. La revisión se guarda en `datos/auditoria_humana.csv` (columna `etiqueta_humana`) junto con un comentario en los casos discutibles.
""")
code(r"""
ARCHIVO_AUD = DATOS / "auditoria_humana.csv"
if not ARCHIVO_AUD.exists():
    (df.sample(20, random_state=SEED)[["titular", "bajada", "etiqueta_llm"]]
       .assign(etiqueta_humana="", comentario="").to_csv(ARCHIVO_AUD, index=False, encoding="utf-8"))
    print("Plantilla creada: completar la columna etiqueta_humana y reejecutar.")
aud = pd.read_csv(ARCHIVO_AUD).fillna("")
completa = (aud.etiqueta_humana != "").all()
acuerdo_n = int((aud.etiqueta_llm == aud.etiqueta_humana).sum())
print(f"Acuerdo LLM vs. humano: {acuerdo_n}/20 = {acuerdo_n/20:.0%}" + ("" if completa else "  (AUDITORÍA INCOMPLETA)"))
aud[["titular", "etiqueta_llm", "etiqueta_humana", "comentario"]]
""")

code(r"""
# Acuerdo del LLM con la sección editorial del diario (todo el dataset)
acuerdo_seccion = (df.etiqueta_llm == df.etiqueta).mean()
print(f"LLM vs. sección del diario: {acuerdo_seccion:.1%} de coincidencia")
pd.crosstab(df.etiqueta, df.etiqueta_llm, rownames=["sección"], colnames=["LLM"])
""")
code(r"""
print("Ejemplos donde el LLM discrepa de la sección:")
df.loc[df.etiqueta_llm != df.etiqueta, ["titular", "etiqueta", "etiqueta_llm", "confianza_llm"]].head(12)
""")

md("""
## 4. Fine-tuning de BETO con las etiquetas del LLM
- Modelo: `dccuchile/bert-base-spanish-wwm-cased` (BETO, preentrenado en español).
- **Train y validación usan `etiqueta_llm`** (supervisión débil); el test no se toca.
- 4 épocas, batch 16, evaluación por época, se conserva el mejor checkpoint según **F1 macro en validación**.
""")
code(r"""
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, set_seed
set_seed(SEED)

BASE_MODEL = "dccuchile/bert-base-spanish-wwm-cased"
label2id = {c: i for i, c in enumerate(CATS)}; id2label = {i: c for c, i in label2id.items()}
tok = AutoTokenizer.from_pretrained(BASE_MODEL)

def a_dataset(d, col):
    ds = Dataset.from_dict({"text": d.titular.tolist(), "label": d[col].map(label2id).tolist()})
    return ds.map(lambda b: tok(b["text"], truncation=True, max_length=64, padding="max_length"), batched=True)

train_lab = df.loc[train_df.index, ["titular", "etiqueta_llm"]].dropna()
val_lab = df.loc[val_df.index, ["titular", "etiqueta_llm"]].dropna()
ds_train, ds_val = a_dataset(train_lab, "etiqueta_llm"), a_dataset(val_lab, "etiqueta_llm")
ds_test = a_dataset(test_df, "etiqueta")   # sólo se usa en la evaluación final
print(len(ds_train), len(ds_val), len(ds_test))

def metricas(p):
    pred = p.predictions.argmax(-1)
    return {"accuracy": accuracy_score(p.label_ids, pred), "f1_macro": f1_score(p.label_ids, pred, average="macro")}

modelo = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=4, id2label=id2label, label2id=label2id)
args = TrainingArguments(output_dir="resultados_trainer", num_train_epochs=4, per_device_train_batch_size=16,
                         per_device_eval_batch_size=32, learning_rate=3e-5, weight_decay=0.01, warmup_ratio=0.1,
                         eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
                         metric_for_best_model="f1_macro", save_total_limit=1, logging_strategy="epoch",
                         report_to="none", seed=SEED)
trainer = Trainer(model=modelo, args=args, train_dataset=ds_train, eval_dataset=ds_val, compute_metrics=metricas)
t0 = time.perf_counter(); trainer.train(); t_train = time.perf_counter() - t0
print(f"Tiempo de entrenamiento: {t_train/60:.1f} min ({'GPU' if torch.cuda.is_available() else 'CPU'})")
hist = pd.DataFrame([l for l in trainer.state.log_history if "eval_f1_macro" in l])[["epoch", "eval_loss", "eval_accuracy", "eval_f1_macro"]]
hist
""")
code(r"""
trainer.save_model(MODELO); tok.save_pretrained(MODELO)
print(sorted(p.name for p in MODELO.iterdir()))
""")

md("## 5. Evaluación final en el conjunto de test reservado")
code(r"""
t0 = time.perf_counter()
out = trainer.predict(ds_test)
ft_lat = (time.perf_counter() - t0) / len(ds_test)
test_df = test_df.assign(pred_ft=[id2label[i] for i in out.predictions.argmax(-1)])
acc_ft = accuracy_score(test_df.etiqueta, test_df.pred_ft)
f1_ft = f1_score(test_df.etiqueta, test_df.pred_ft, average="macro")
print(f"BETO fine-tuned en TEST (n={len(test_df)})  Accuracy={acc_ft:.3f}  F1 macro={f1_ft:.3f}")
print(classification_report(test_df.etiqueta, test_df.pred_ft, labels=CATS, digits=3))
""")
code(r"""
cm = confusion_matrix(test_df.etiqueta, test_df.pred_ft, labels=CATS)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=CATS, yticklabels=CATS)
plt.xlabel("Predicción"); plt.ylabel("Etiqueta real (sección)")
plt.title(f"Matriz de confusión en test – BETO fine-tuned (F1 macro = {f1_ft:.3f})")
plt.tight_layout(); plt.show()
""")
code(r"""
print("Errores del modelo en test:")
test_df.loc[test_df.etiqueta != test_df.pred_ft, ["titular", "etiqueta", "pred_ft"]]
""")

md("""
## 6. Comparativa y decisión
Se añade como referencia adicional la línea base clásica vista en clase (**TF-IDF + regresión logística**), entrenada con las mismas etiquetas del LLM.
""")
code(r"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union
tfidf = make_pipeline(make_union(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                                 TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
                      LogisticRegression(C=10, max_iter=3000))
tfidf.fit(train_lab.titular, train_lab.etiqueta_llm)
t0 = time.perf_counter(); pred_tfidf = tfidf.predict(test_df.titular); tf_lat = (time.perf_counter() - t0) / len(test_df)
acc_tf, f1_tf = accuracy_score(test_df.etiqueta, pred_tfidf), f1_score(test_df.etiqueta, pred_tfidf, average="macro")
print(f"TF-IDF + LR en test: Accuracy={acc_tf:.3f}  F1 macro={f1_tf:.3f}")
import joblib
joblib.dump(tfidf, MODELO / "tfidf_lr.joblib")   # respaldo ligero para el dashboard si no están los pesos de BETO
""")
code(r"""
test_llm = df.loc[test_df.index]
acc_llm = accuracy_score(test_llm.etiqueta, test_llm.etiqueta_llm.fillna("sin_etiqueta"))
f1_llm = f1_score(test_llm.etiqueta, test_llm.etiqueta_llm.fillna("sin_etiqueta"), labels=CATS, average="macro")
ft40 = test_df.loc[zs_df.index]
lat_llm = json.load(open(MODELO / "latencia_llm.json"))["latencia_llm_s_por_titular"] if (MODELO / "latencia_llm.json").exists() else float("nan")

tabla = pd.DataFrame([
    {"modelo": "Zero-shot (BERT-es XNLI)", "evaluado_en": "40 de test", "accuracy": acc_zs, "f1_macro": f1_zs,
     "latencia_ms_titular": zs_lat * 1000, "costo": "Gratis, CPU local, 4 pasadas NLI por titular"},
    {"modelo": "LLM débil (Gemini)", "evaluado_en": f"test completo ({len(test_df)})", "accuracy": acc_llm, "f1_macro": f1_llm,
     "latencia_ms_titular": lat_llm * 1000, "costo": "API externa, cuota/pago por token, requiere internet"},
    {"modelo": "TF-IDF + Reg. logística", "evaluado_en": f"test completo ({len(test_df)})", "accuracy": acc_tf, "f1_macro": f1_tf,
     "latencia_ms_titular": tf_lat * 1000, "costo": "Gratis, CPU, < 5 MB"},
    {"modelo": "BETO fine-tuned", "evaluado_en": f"test completo ({len(test_df)})", "accuracy": acc_ft, "f1_macro": f1_ft,
     "latencia_ms_titular": ft_lat * 1000, "costo": "Gratis, CPU local, ~420 MB de pesos"},
    {"modelo": "BETO fine-tuned", "evaluado_en": "mismos 40 del zero-shot", "accuracy": accuracy_score(ft40.etiqueta, ft40.pred_ft),
     "f1_macro": f1_score(ft40.etiqueta, ft40.pred_ft, average="macro"), "latencia_ms_titular": ft_lat * 1000, "costo": "idem"},
]).round(3)
tabla
""")
code(r"""
resumen = {"f1_macro_test": round(f1_ft, 3), "accuracy_test": round(acc_ft, 3), "f1_zero_shot": round(f1_zs, 3),
           "f1_llm_test": round(f1_llm, 3), "acuerdo_llm_humano": f"{acuerdo_n}/20", "acuerdo_llm_humano_pct": acuerdo_n / 20,
           "acuerdo_llm_seccion": round(acuerdo_seccion, 3), "n_train": len(ds_train), "n_val": len(ds_val), "n_test": len(ds_test),
           "modelo_base": BASE_MODEL, "fecha": datetime.now().strftime("%Y-%m-%d")}
json.dump(resumen, open(MODELO / "metricas.json", "w"), indent=2, ensure_ascii=False)
tabla.to_csv(MODELO / "comparativa.csv", index=False)
print(f"RESULTADOS -> F1 Macro: {f1_ft:.3f} | Zero-shot: {f1_zs:.3f} | Acuerdo LLM-Humano: {acuerdo_n}/20")
""")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = Path(__file__).resolve().parents[1] / "02_clasificacion.ipynb"
nbf.write(nb, out)
print("escrito", out)
