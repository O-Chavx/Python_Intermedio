# 🗞️ Tarea 1 – Noticias peruanas: del titular al clasificador

## 1. Pregunta del proyecto
**¿Pueden convertir titulares peruanos en un clasificador de noticias?**
Se recolectaron titulares reales de La República, se etiquetaron con un LLM local (Qwen2.5-1.5B-Instruct; supervisión débil, auditada a mano), se ajustó un Transformer en español (BETO) y se publicó un dashboard en Streamlit que clasifica titulares nuevos en vivo.

| Paso | Archivo |
|---|---|
| Recolección, limpieza y EDA | [`01_recoleccion.ipynb`](01_recoleccion.ipynb) |
| Zero-shot, LLM, fine-tuning y evaluación | [`02_clasificacion.ipynb`](02_clasificacion.ipynb) |
| Dashboard | [`app.py`](app.py) |
| Datos | [`datos/noticias.csv`](datos/noticias.csv), [`datos/etiquetas_llm.csv`](datos/etiquetas_llm.csv), [`datos/auditoria_humana.csv`](datos/auditoria_humana.csv) |

## 2. Medio y fechas de extracción
- **Opción A – La República** (`https://larepublica.pe`).
- Fecha de descarga: **2026-10-17**. Noticias publicadas entre **2024-03-30** y **2026-10-17 (63 % del último mes)**.
- Fuentes: RSS oficiales (`/rss/{politica,economia,deportes,ciencia,home}.xml`), sitemaps de noticias (`/sitemap/...`) y páginas de noticia enlazadas desde ellos (todo permitido por `robots.txt`).
- El endpoint “Ver más noticias” (`/api/search/articles`) responde **403** a clientes que no son navegador: el bloqueo se documenta en el notebook y **no se evade**. `/rss/tecnologia.xml` responde **410**.
- Buenas prácticas: User-Agent descriptivo, pausa de 1.5 s, máx. 1 reintento, caché en `datos/raw/`.

## 3. Resultados

400 noticias (100 por categoría) · split estratificado 70/15/15 (`random_state=42`) → 280 / 60 / 60.

| Modelo | Evaluado en | F1 macro | Accuracy | Latencia (CPU) |
|---|---|---|---|---|
| Zero-shot `Recognai/bert-base-spanish-wwm-cased-xnli` | 40 titulares de test | **0.722** | 0.725 | ~140 ms |
| LLM débil `Qwen/Qwen2.5-1.5B-Instruct` (titular + bajada) | test (60) | 0.918 | 0.917 | ~2.4 s |
| TF-IDF + regresión logística | test (60) | 0.800 | 0.800 | < 1 ms |
| **BETO fine-tuned** `dccuchile/bert-base-spanish-wwm-cased` | test (60) | **0.884** | 0.883 | ~30 ms |

- **Auditoría humana del LLM:** 19/20 (95 %) casos de acuerdo · **LLM vs. sección del diario:** 93.2 %.
- **Modelo elegido:** BETO fine-tuned (justificación en la sección 6 del notebook 2).

## 4. Hallazgos analíticos
1. **Un LLM pequeño y local basta como etiquetador, pero tiene un sesgo claro.** Qwen2.5-1.5B coincide con la sección del diario en 93.2 % de las notas y en 19/20 (95 %) de la auditoría humana. Sus errores se concentran en **economía → política**: notas de *política económica* (presupuesto, sueldo mínimo, reformas del MEF) cuyo titular nombra a un actor político. BETO, entrenado con esas etiquetas, **hereda el mismo error**: es la frontera del etiquetador, no la del diario.
2. **El fine-tuning paga con muy pocos datos.** Con solo 280 titulares, BETO pasa de F1 0.722 (zero-shot) a **0.884** y es ~75× más rápido que el LLM. `deportes` es casi perfecta (léxico propio: clubes, torneos, “EN VIVO”), mientras que `economia` es la categoría más difícil. En el EDA, los titulares de ciencia son los más largos (mediana 120 caracteres frente a 100 en política): son titulares explicativos, del tipo “científicos descubren que…”.

## 5. Limitaciones técnicas
1. **Muestreo y tamaño.** El RSS solo trae las notas más recientes y el endpoint “Ver más” está bloqueado (403). Por eso el volumen se completó siguiendo enlaces internos, que favorecen notas enlazadas o populares y mezclan fechas (algunas de 2024). El test tiene solo 60 notas: cada error mueve ~1.7 puntos de accuracy, así que las métricas tienen varianza alta.
2. **Etiquetas débiles y modelo pesado.** El entrenamiento usa etiquetas del LLM (con su sesgo economía/política), y el LLM etiqueta con titular + bajada mientras BETO solo ve el titular. Los pesos de BETO (~420 MB) no pueden ir a GitHub: en un despliegue en Streamlit Cloud la app usa el respaldo TF-IDF, salvo que se publique el modelo en Hugging Face Hub (variable `HF_MODEL_ID`).

## 6. Cómo ejecutar en local
```bash
cd tarea_1
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

**Dashboard:**
```bash
streamlit run app.py
```
Los pesos de BETO (`modelo/model.safetensors`, ~420 MB) no se suben a GitHub (`.gitignore`). Si no están, la app usa automáticamente el respaldo ligero `modelo/tfidf_lr.joblib`. Para regenerarlos, ejecutar `02_clasificacion.ipynb`.

**Notebooks (reproducir todo):**
```bash
jupyter nbconvert --to notebook --execute --inplace 01_recoleccion.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb
```
Los notebooks reutilizan la caché (`datos/raw/articulos.jsonl`, `datos/etiquetas_llm.csv`), así que no vuelven a descargar ni a re-etiquetar con el LLM si ya existen.

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb
├── 02_clasificacion.ipynb
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── scripts/            # generadores de los notebooks
├── datos/
│   ├── noticias.csv
│   ├── etiquetas_llm.csv
│   ├── auditoria_humana.csv
│   └── raw/            # respaldo crudo (RSS, sitemaps, artículos)
└── modelo/             # config, tokenizer, métricas y modelo ligero (sin pesos pesados)
```
