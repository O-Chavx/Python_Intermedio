# 🗞️ Clasificador de titulares peruanos · Tarea 1 (Opción A)

> **¿Pueden convertir titulares peruanos en un clasificador de noticias?** **Sí.** Con solo 280 titulares de entrenamiento etiquetados por un LLM local, BETO afinado alcanza **F1 macro = 0.884** en el test reservado, frente a **0.722** del zero-shot, y clasifica cada titular en ~35 ms en CPU.

| | |
|---|---|
| **Opción** | A – La República (`larepublica.pe`): 400 noticias |
| **Categorías** | `politica` · `economia` · `deportes` · `ciencia_tecnologia` (100 por categoría) |
| **Stack** | requests · BeautifulSoup · pandas · Plotly · Qwen2.5-1.5B-Instruct (LLM local) · HF Transformers (BETO) · scikit-learn · Streamlit |
| **Resultados en test** | F1 macro **0.884** · Zero-shot **0.722** · Acuerdo LLM–humano **20/20** |

---

## 1. Pregunta del proyecto y objetivo
**Pregunta:** ¿se puede convertir un conjunto pequeño de titulares de prensa peruana en un clasificador temático confiable, sin anotar a mano todo el dataset?

**Objetivo:**
1. Recolectar titulares reales de La República respetando las reglas del medio.
2. Etiquetarlos de forma semisupervisada con un LLM, auditado por un humano.
3. Comparar cuatro enfoques: zero-shot, LLM débil, TF-IDF clásico y BETO afinado.
4. Desplegar el mejor en un dashboard que clasifique titulares nuevos en vivo.

| Paso | Archivo |
|---|---|
| Recolección, limpieza y EDA | [`01_recoleccion.ipynb`](01_recoleccion.ipynb) |
| Zero-shot, LLM, fine-tuning y evaluación | [`02_clasificacion.ipynb`](02_clasificacion.ipynb) |
| Dashboard | [`app.py`](app.py) |

## 2. Medio y fechas de extracción
| Medio | Fuentes usadas (en orden) | Noticias |
|---|---|---|
| **La República** (`larepublica.pe`) | RSS por sección (`/rss/<seccion>.xml`, `/rss/home.xml`) → sitemaps de noticias (`/sitemap/<seccion>.xml`, `/sitemap/noticias.xml`) → páginas de noticia enlazadas desde ellos (notas de la misma sección) | 400 |

- **Fecha de descarga:** 2026-10-17. Unas 480 solicitudes en ~14 min; solo 3 respondieron 404.
- **Fechas de publicación:** el **69 %** es de septiembre u octubre de 2026 (52 % solo de octubre). Hay 102 notas anteriores a agosto de 2026 (la más antigua es del 2024-03-30), sobre todo de economía (36). Llegaron siguiendo los enlaces internos de los artículos, que también apuntan a notas antiguas.
- **Bloqueos documentados (y no evadidos):**
  - Cada RSS de sección trae solo **7–25 notas**, y `/rss/tecnologia.xml` responde **410 Gone**.
  - El botón *"Ver más noticias"* usa `/api/search/articles`, que responde **403** a clientes que no son navegador. **No se intentó evadir** ese bloqueo.
  - `robots.txt` prohíbe paginar secciones (`/*/pag/*`). Por eso se siguieron los enlaces a notas relacionadas (páginas permitidas) en lugar de páginas siguientes.
- **Buenas prácticas:** User-Agent descriptivo, pausa de 1.5 s antes de cada solicitud, máximo 1 reintento y caché. Los respaldos crudos (RSS, sitemaps, `robots.txt` y `articulos.jsonl`) están en `datos/raw/` (~5 MB); al reejecutar el notebook no se vuelve a descargar nada.
- **Limpieza:** 607 registros crudos → **400 finales**. Se descartaron 144 notas de secciones fuera de las 4 categorías (sociedad 56, espectáculos 28, mundo 23…; no se creó una quinta categoría), 21 plantillas diarias repetidas ("Precio del dólar hoy…"), 38 excedentes para balancear, 3 errores HTTP y 1 titular duplicado.

## 3. Hallazgos analíticos
1. **Deportes y ciencia tienen "firma" propia; economía y política se mezclan.** El LLM coincide con la sección del diario en el **100 %** de deportes y el **97 %** de política, pero solo en el **82 %** de economía. Casi todos esos desacuerdos son *política económica* (presupuesto 2027, sueldo mínimo, el BCR en el Senado, reformas del MEF): el titular nombra a un actor político aunque el tema sea económico. BETO, entrenado con esas etiquetas, **hereda el mismo sesgo**: 5 de sus 7 errores en test son economía → política. El modelo aprende la frontera del etiquetador, no la del diario.
2. **Cada sección titula con un estilo distinto.** Ciencia/tecnología usa los titulares más largos (mediana **120** caracteres frente a **100.5** en política), narrativos y explicativos: el 35 % contiene "científicos…". Deportes repite fórmulas de servicio: el 20 % incluye "EN VIVO", "hora y canal" o "canal". Economía es la sección con más titulares en forma de pregunta (13 %): "¿Cuándo pagan…?", "¿Cuánto…?". Estas marcas explican por qué deportes (F1 1.00) y ciencia (F1 0.97) son las categorías más fáciles.
3. **Un LLM pequeño y local basta como etiquetador si el prompt es simple.** Con Qwen2.5-1.5B, un prompt largo con opciones A/B/C/D acertaba solo el **22 %** (respondía casi siempre lo mismo). Un prompt corto, puntuando la probabilidad de cada una de las 4 respuestas posibles, subió a **93.2 %** de acuerdo con la sección y **20/20** en la auditoría humana. Su confianza ayuda a detectar errores (media 0.92 en los errores frente a 0.98 en general), aunque no los separa por completo.

## 4. Limitaciones técnicas
1. **Test pequeño y fronteras difusas.** Con 60 titulares de test, cada error mueve ~1.7 puntos de accuracy. En validación el F1 fue 0.847, así que el 0.884 tiene un margen amplio. Los errores se concentran en la frontera economía ↔ política, donde incluso un humano puede dudar (la auditoría tuvo 2 casos discutibles).
2. **Etiquetas débiles y diferencia de información.** BETO se entrena con las etiquetas del LLM (y su sesgo), y se evalúa contra la sección editorial del diario. Además, el LLM etiquetó con **titular + bajada**, pero BETO y el dashboard solo ven el **titular**, así que la comparación favorece algo al LLM.
3. **Cobertura del scraping.** Al no poder paginar ni usar "Ver más", el volumen se completó siguiendo enlaces internos. Eso favorece notas enlazadas o populares y mezcla fechas (desde 2024): no es una muestra aleatoria de lo que publica el diario.
4. **Archivos pesados.** `modelo/model.safetensors` pesa ~420 MB, por encima del límite de 100 MB de GitHub, así que está en `.gitignore` (junto a `*.bin` y `checkpoint-*/`). En el repo quedan `config.json`, el tokenizer, `metricas.json`, `comparativa.csv` y el respaldo ligero `tfidf_lr.joblib`. Si faltan los pesos, la app usa automáticamente el modelo TF-IDF y lo indica en pantalla.

## 5. Cómo ejecutarlo en local
```bash
# 1) Entorno (Python 3.13 probado en Windows 11)
cd tarea_1
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/Mac: source .venv/bin/activate)
pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2) (Opcional) Regenerar el modelo BETO: los pesos no están en GitHub
jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb
#   - Reutiliza datos/etiquetas_llm.csv: no vuelve a correr el LLM (~5 min en CPU).
#   - Si se borra etiquetas_llm.csv, Qwen vuelve a etiquetar todo (~16 min en CPU, ~6 GB de RAM).
#   - 01_recoleccion.ipynb reutiliza datos/raw/ (REDESCARGAR = False).

# 3) Lanzar el dashboard
streamlit run app.py
```
La app abre en `http://localhost:8501` y tiene:
- **Barra lateral:** filtros por medio, categoría y rango de fechas.
- **Indicadores:** noticias recolectadas, F1 macro en test, acuerdo LLM–humano y acuerdo LLM–sección.
- **Probador en vivo:** escribes un titular y ves la categoría predicha y la probabilidad de cada clase.
- **Exploración:** distribución de categorías y mapa de calor sección vs. LLM (Plotly), tabla interactiva con descarga CSV y la comparativa de modelos.

## 6. Resumen de resultados
| Método | Evaluado en | Accuracy | F1 macro | Latencia/titular (CPU) |
|---|---|---|---|---|
| Zero-shot `Recognai/bert-base-spanish-wwm-cased-xnli` | 40 titulares de test | 0.725 | 0.722 | ~160 ms |
| LLM débil `Qwen/Qwen2.5-1.5B-Instruct` (local, titular + bajada) | test (60) | 0.917 | 0.918 | ~2.6 s |
| TF-IDF + regresión logística (línea base del curso) | test (60) | 0.800 | 0.800 | < 1 ms |
| **BETO fine-tuned** `dccuchile/bert-base-spanish-wwm-cased` | test (60) | **0.883** | **0.884** | **~35 ms** |

- **F1 por categoría (BETO):** deportes 1.00 · ciencia_tecnologia 0.97 · politica 0.80 · economia 0.77.
- **Acuerdo LLM–humano** (auditoría de 20 casos al azar, revisados a mano y con comentarios en los dudosos): **20/20 (100 %)**. Acuerdo LLM–sección en todo el dataset: **93.2 %**.
- **Elección para producción: BETO fine-tuned.** Queda a pocos puntos del LLM, pero es **~75 veces más rápido**, corre en CPU sin costo por consulta, no depende de una API y siempre da la misma respuesta. El LLM queda como herramienta de pre-etiquetado (con auditoría humana) para ampliar el dataset, y TF-IDF como respaldo ultraligero del dashboard.

## 7. Uso de IA
Siguiendo lo permitido en el enunciado, se usó **Claude (Anthropic)** como asistente para escribir el código de scraping, los notebooks y la app. La elección del medio, la **auditoría humana de los 20 casos**, la revisión de resultados y las decisiones finales son del estudiante. Todas las métricas se calcularon sobre el test reservado, que nunca se usó para entrenar.

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb      # robots.txt, RSS + sitemaps + enlaces internos, limpieza, mapeo de secciones, EDA (Plotly)
├── 02_clasificacion.ipynb    # split 70/15/15, zero-shot, LLM débil + auditoría, BETO, evaluación, comparativa
├── app.py                    # dashboard Streamlit
├── requirements.txt          # versiones exactas
├── .gitignore                # excluye pesos del modelo, .venv y .env
├── .streamlit/config.toml
├── scripts/                  # generadores de los notebooks (build_nb1.py, build_nb2.py)
├── datos/
│   ├── raw/                  # respaldos crudos: robots.txt, RSS, sitemaps, articulos.jsonl
│   ├── noticias.csv          # 400 filas: titular, bajada, medio, seccion_original, url, fecha, etiqueta
│   ├── etiquetas_llm.csv     # titular, etiqueta_llm, confianza, modelo_llm, fecha
│   └── auditoria_humana.csv  # 20 casos: etiqueta del LLM vs. etiqueta humana + comentario
└── modelo/                   # config, tokenizer, metricas.json, comparativa.csv, tfidf_lr.joblib (pesos en .gitignore)
```
