# Tarea 4: agente de investigación socioeconómica (BCRP + ENAHO 2024)

Claude Code como agente que responde preguntas sobre la economía y la pobreza del Perú **con herramientas, no de memoria**. Usa dos fuentes:

- Las series del **BCRP**, por un servidor MCP propio.
- Los microdatos de la **ENAHO 2024 del INEI**, por cuatro Skills.

Cada cifra sale de una llamada que se puede repetir, y un script la vuelve a calcular de forma independiente.

**Pregunta de investigación:** ¿Cómo evolucionó la inflación de alimentos frente a la inflación general en el Perú entre 2020 y 2024, y qué brechas urbano/rural y departamentales presentaba la pobreza monetaria al cierre de ese período (ENAHO 2024)?

**Informe:** [`informes/informe_final.md`](informes/informe_final.md)

| Resultado | Valor |
|---|---|
| Pruebas del MCP | **10/10 passed** (8 del curso, sin cambios, y 2 propias) |
| Pobreza nacional 2024 | **27.58 %** (INEI 27.6 %) |
| Residentes habituales | **108,664** |
| Pobreza urbana / rural | **24.81 % / 39.30 %** (INEI 24.8 % / 39.3 %) |
| Unidades territoriales del mapa | **25/25** (Lima y Callao separados; 7/7 coinciden con la Sesión 16) |
| Evaluación: sin MCP/Skills | **6/10** correctas |
| Evaluación: con MCP/Skills | **10/10** correctas |
| Cifras del informe verificadas de forma independiente | **23/23** |

## Arquitectura

```
                    pregunta en lenguaje natural
                               │
                         Claude Code  ── CLAUDE.md (reglas: nada de memoria, sin causalidad)
                               │
                 skill investigando-peru (orquesta)
          ┌────────────────────┴─────────────────────┐
   MCP bcrp (mcp/server.py)                  Skills ENAHO (.claude/skills/)
   buscar_series · serie · resumen           limpiando-enaho → salidas/personas_2024.parquet,
   comparar_series · graficar_serie                            validacion.txt, indicadores.csv
   valor_actual · recurso · prompt           graficando-enaho → figuras/
          │                                  mapeando-enaho   → mapas/
   API estadisticas.bcrp.gob.pe              datos/966-Modulo34.zip, 966-Modulo02.zip, GeoJSON
          └────────────────────┬─────────────────────┘
               verificar.py (recalcula sin MCP ni Skills)
                               │
                    informes/informe_final.md
```

## Parte 1: servidor MCP del BCRP (`mcp/server.py`)

Está construido sobre el proyecto de la Sesión 04 con FastMCP.

| Herramienta | Qué hace |
|---|---|
| `buscar_series` | Busca en el catálogo oficial (más de 17 mil series) por palabras clave, sin importar tildes. |
| `serie` | Devuelve los datos de una serie entre dos fechas (diaria, mensual, trimestral o anual) con la URL de la fuente. |
| `resumen` | Calcula en Python el primer y el último dato, el cambio, la variación %, el promedio, el máximo y el mínimo, con su periodo. |
| **`comparar_series`** (propia) | Alinea dos series de la misma frecuencia y descarta e informa los periodos que faltan en alguna. Calcula, para cada una, primero, último y promedio, y para el par la brecha promedio, el mes de mayor brecha, cuántos periodos estuvo A por encima de B y la correlación de Pearson, marcada como descriptiva. Rechaza las frecuencias distintas con un error claro. |
| `graficar_serie` (propia) | Hace el gráfico de 1 a 4 series con título, leyenda con códigos y fuente, y lo guarda en `figuras/`. |
| `valor_actual` | Devuelve el último dato publicado y su variación frente al año anterior (viene de la Sesión 04). |
| Recurso `bcrp://serie/{codigo}` | Ficha de la serie: nombre, categoría, frecuencia, inicio y última actualización. |
| Prompt `informe(tema)` | Plantilla de informe con cifras citadas por código y periodo. |

**Pruebas** (`mcp/test_server.py`): las 8 del curso sin modificar, más:

- `test_comparar_alimentos_contra_ipc_total`: 60 meses alineados, dic-2024 con alimentos 1.25 % y total 1.97 % (cifras del BCRP), correlación > 0.9 y mayor brecha en 2022–2023.
- `test_comparar_rechaza_frecuencias_distintas`: una serie mensual contra una diaria da `ToolError`.

## Parte 2: Skills de la ENAHO (`.claude/skills/`)

| Skill | Qué hace | Salidas |
|---|---|---|
| `limpiando-enaho` | Lee los módulos 34 y 02 con las llaves como texto (`conglome`, `vivienda`, `hogar`, `codperso`, `ubigeo`). Normaliza los nombres y filtra residentes con `(p204==1 & p205==2) \| (p204==2 & p206==1)`. Une con `merge(..., validate="m:1")` y verifica que no haya duplicados ni filas perdidas. Construye pobreza, departamento (`ubigeo[:2]`) y área (`estrato ≤ 5`). Hace **10 validaciones**: nacional, extrema, urbana, rural, 108,664 residentes, llaves únicas, unión sin pérdidas, suma de factores y 25 departamentos. **Si alguna falla, borra la base y termina con error.** | `salidas/validacion.txt`, `salidas/indicadores.csv`, `salidas/personas_2024.parquet` |
| `graficando-enaho` | Hace barras ponderadas por área, sexo, edad o departamento. Área y departamento usan el método del INEI (`factor07 × mieperho`) y sexo y edad usan `facpob07`. Las barras empiezan en cero y van ordenadas, con el valor en cada barra, una línea del promedio nacional, título con qué y cuándo, y fuente y peso al pie. | `figuras/pobreza_*_2024.png` |
| `mapeando-enaho` | Hace un mapa coroplético uniendo `ubigeo[:2]` con `FIRST_IDDP` (nunca por nombre). Exige 25 unidades sin NA y Lima y Callao separados. Usa la escala Blues desde 0 con la leyenda «% de personas en pobreza». Compara los resultados con las cifras de referencia de la Sesión 16. | `mapas/pobreza_departamento.png`, `.csv`, `comparacion_sesion16.csv` |
| `investigando-peru` (adicional) | Orquesta la investigación en cinco pasos: plan, consultas al MCP, Skills de la ENAHO, verificación independiente (`scripts/verificar.py`) e informe. | `salidas/plan.md`, `cifras_bcrp.json`, `verificacion.md`, `informes/informe_final.md` |

Las Skills de gráfico y mapa ejecutan primero `limpiando-enaho` si no existe la base. En la evaluación (Modo B) cada pregunta empezó con `salidas/` vacía y el agente corrió la limpieza antes de responder.

## Parte 3: ejecución integrada

El pedido, en lenguaje natural ([`evidencias_ia/integracion/prompt.txt`](evidencias_ia/integracion/prompt.txt)), fue:

> Quiero investigar esto con datos oficiales y dejar un informe reproducible: ¿Cómo evolucionó la inflación de alimentos frente a la inflación general…?

En **una sola sesión** de `claude -p` (Opus), Claude Code:

- Activó **4 Skills**: `investigando-peru`, `limpiando-enaho`, `graficando-enaho` y `mapeando-enaho`.
- Usó **4 herramientas MCP distintas**: `buscar_series` ×2, `resumen` ×10, `comparar_series` y `graficar_serie`.
- Escribió el plan, el informe y la verificación (23/23 cifras coinciden).

| Archivo | Contenido |
|---|---|
| [`evidencias_ia/integracion/ejecucion.md`](evidencias_ia/integracion/ejecucion.md) | Transcripción legible |
| `ejecucion.jsonl` | Transcripción cruda |
| `corrida_1_slash/` | Una primera corrida invocada con `/investigando-peru` |

## Parte 4: evaluación

Consiste en 10 preguntas (4 BCRP, 4 ENAHO y 2 mixtas) con las respuestas esperadas calculadas antes del experimento. Cada pregunta se hizo en dos modos y en sesiones independientes. Ver [`evaluacion/comparacion.md`](evaluacion/comparacion.md) y [`evaluacion/resultados.csv`](evaluacion/resultados.csv).

| | Sin MCP/Skills (A) | Con MCP/Skills (B) |
|---|---|---|
| Correctas | 6/10 | 10/10 |
| Incorrectas / sin respuesta | 2 / 2 | 0 / 0 |
| Tiempo promedio | 27.8 s | 19.4 s |

## Datos

| Fuente | Enlace | Dónde va |
|---|---|---|
| ENAHO 2024, módulo 34 (sumaria) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip | `datos/` (ignorado por Git) |
| ENAHO 2024, módulo 02 (miembros) | https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip | `datos/` (ignorado por Git) |
| Límites departamentales | https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson | `datos/` (incluido) |
| BCRP | https://estadisticas.bcrp.gob.pe/estadisticas/series/ | El MCP consulta la API y la primera vez baja el catálogo a `datos/` |

## Instalación y reproducción

Se necesita [uv](https://docs.astral.sh/uv/) y [Claude Code](https://claude.com/claude-code) con la sesión iniciada.

```bash
cd tarea_4
uv sync

# datos del INEI (unos 21 MB)
curl -L -o datos/966-Modulo34.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip
curl -L -o datos/966-Modulo02.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip

# Parte 1: pruebas del MCP (consultan el BCRP en vivo)
uv run pytest -q                                   # 10 passed

# Parte 2: Skills a mano
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area      # sexo, edad, departamento
uv run .claude/skills/mapeando-enaho/scripts/mapear.py

# Parte 3: el agente completo
claude      # en esta carpeta; acepta el servidor "bcrp" de .mcp.json
#   > Quiero investigar con datos oficiales: ¿cómo evolucionó la inflación de alimentos ... ?
uv run .claude/skills/investigando-peru/scripts/verificar.py

# Parte 4: evaluación
uv run evaluacion/respuestas_esperadas.py
uv run evaluacion/evaluar.py
uv run evidencias_ia/convertir.py                  # transcripciones .jsonl a .md
```

**Conectar el MCP a Claude Code:** `.mcp.json` ya declara el servidor (`uv run mcp/server.py`). Al abrir `claude` en esta carpeta, Claude Code pide aprobarlo una vez. Se comprueba con `/mcp`, donde debe aparecer `bcrp · connected`. Para el modo no interactivo se usa `claude -p "..." --mcp-config .mcp.json`.

## Limitaciones y problemas encontrados

- **Fuentes que no miden lo mismo.** La inflación del BCRP es de Lima Metropolitana y la pobreza es nacional y departamental de 2024. El informe las pone una junto a la otra, sin afirmar causalidad.
- **Dos formas de ponderar.** La ponderación por hogares (`factor07 × mieperho`) replica las cifras del INEI, y `facpob07` sobre personas da 27.53 %, 24.7 % urbana y 39.4 % rural. Se usa la primera para el área y el departamento y la segunda para los atributos de la persona.
- **API del BCRP inestable.** En algunos momentos devuelve una página antibots en vez de JSON. El servidor reintenta 4 veces y, si sigue fallando, devuelve un error explícito en lugar de inventar datos.
- **Cómo se activan las Skills.** En la evaluación, el modelo a veces corrió los scripts de las Skills con Bash en vez de activarlas con la herramienta `Skill`. El resultado es el mismo, pero el registro de activaciones es menos explícito.
- **`variacion_pct` sobre tasas.** En una serie que ya es una variación porcentual, la `variacion_pct` de `resumen` y `comparar_series` tiene poco sentido económico. El informe no la usa.
- **Tamaño de la evaluación.** Son 10 preguntas y una corrida por modo, sin repeticiones.

## Evidencias del uso de IA

Todo está en [`evidencias_ia/`](evidencias_ia/), con un índice en su README:

| Carpeta | Contenido |
|---|---|
| `mcp/` | Desarrollo del servidor |
| `skills/` | Desarrollo de las Skills |
| `integracion/` | Ejecución integrada (transcripción completa) |
| `evaluacion/` | Las 20 sesiones del experimento (transcripciones completas) |

Las claves y rutas locales se ocultaron con `evidencias_ia/convertir.py`.

## Estructura

```
tarea_4/
├── README.md · CLAUDE.md · pyproject.toml · uv.lock · .mcp.json · .gitignore
├── mcp/                server.py, test_server.py
├── .claude/skills/     limpiando-enaho/ graficando-enaho/ mapeando-enaho/ investigando-peru/
├── datos/              GeoJSON, referencia_sesion16.csv (los .zip del INEI se descargan)
├── salidas/            validacion.txt, indicadores.csv, plan.md, cifras_bcrp.json, verificacion.md, scripts/
├── figuras/  mapas/    PNG y CSV generados
├── evaluacion/         preguntas.csv, resultados.csv, comparacion.md, respuestas_esperadas.py, evaluar.py
├── informes/           informe_final.md
└── evidencias_ia/      mcp/ skills/ integracion/ evaluacion/
```
