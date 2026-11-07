# Comparación: Claude Code sin y con MCP + Skills

## Diseño

- **10 preguntas** (`preguntas.csv`): 4 del BCRP (B1–B4), 4 de la ENAHO 2024 (E1–E4) y 2 que combinan ambas (C1–C2).
- **Respuestas esperadas** calculadas *antes* de correr el experimento con `respuestas_esperadas.py`, que no usa el MCP ni las Skills: pide los datos a la API del BCRP con httpx y lee los `.dta` del INEI con pandas. Las tolerancias se fijaron ahí: ±0.01 en tasas del BCRP, ±0.005 S/ en el tipo de cambio, ±0.1 pp en la ENAHO y ±0.05 en cada cifra de las mixtas.
- **Mismo modelo** (`sonnet`) y **misma instrucción** en ambos modos. Cada pregunta es una sesión nueva de `claude -p --no-session-persistence`, y las 20 corrieron el 2026-11-04.
- **Respuesta en JSON** (`valor`, `valor_2`, `fuente`, `interpretacion`). Si no puede obtener la cifra, el modelo debe responder `null`.

| | Modo A: sin MCP ni Skills | Modo B: con MCP y Skills |
|---|---|---|
| Carpeta | Temporal y vacía, sin archivos del proyecto ni respuestas | Copia del proyecto **sin** `evaluacion/`, `informes/`, `evidencias_ia/` ni resultados previos (`salidas/`, `figuras/` y `mapas/` vacías) |
| MCP | Ninguno (`--strict-mcp-config`) | `bcrp` (`.mcp.json`) |
| Skills | Bloqueadas (`--disallowedTools Skill`) | Las 4 del proyecto |
| Otras herramientas | WebSearch y WebFetch | WebSearch, WebFetch, Read, Glob y `Bash(uv run *)` (para correr los scripts de las Skills) |

Para las mixtas, una respuesta cuenta como correcta solo si **las dos cifras** están dentro de la tolerancia y la interpretación **no afirma causalidad**.

## Resultados

| | Modo A | Modo B |
|---|---|---|
| Correctas | **6/10** | **10/10** |
| Incorrectas | 2 (B4, C1) | 0 |
| No contestadas (`null`) | 2 (E3, E4) | 0 |
| Tiempo promedio por pregunta | 27.8 s | 19.4 s |
| BCRP (4) | 3 | 4 |
| ENAHO (4) | 2 | 4 |
| Mixtas (2) | 1 | 2 |

El detalle por pregunta (respuesta, fuente citada, herramientas usadas, tiempo y error) está en `resultados.csv`. Las 20 transcripciones completas están en `evidencias_ia/evaluacion/` (`A_B1.md`, `B_B1.md`, …).

### Preguntas que mejoraron con MCP + Skills

| Pregunta | Esperado | Modo A | Modo B | Qué pasó en el Modo A |
|---|---|---|---|---|
| B4: máximo de la inflación de alimentos 2020–2024 | 13.16 % | 15.21 % ✗ | 13.16 % ✓ | Usó la división «alimentos y bebidas **no alcohólicas**» del INEI a dic-2022, que es otra serie. El MCP usa la serie del BCRP que pide la pregunta (PN09822PM). |
| E3: pobreza de niños de 0 a 13 años | 37.96 % | null | 37.96 % ✓ | En la web solo halló 0–17 años (UNICEF). Sin microdatos no pudo calcular el grupo y respondió que no sabía. |
| E4: pobreza del departamento de Lima (15) | 27.07 % | null | 27.07 % ✓ | El INEI publica «Lima Metropolitana» y «Lima región» por separado, no el departamento 15. Encontró 27.1 % en un repositorio no oficial y no lo aceptó como fuente. |
| C1: brecha alimentos − total y rural − urbana | −0.72 y 14.50 | −1.91 y 14.50 ✗ | −0.72 y 14.49 ✓ | La pobreza estuvo bien, pero volvió a usar la división del INEI (0.06 %) en lugar de la serie del BCRP (1.25 %). |

**Ninguna pregunta empeoró.**

### Principales errores y observaciones

1. **El error del Modo A no es inventar, es usar otra definición.** En B4 y C1 citó cifras reales del INEI, pero de una serie distinta («alimentos y bebidas no alcohólicas» frente a «alimentos y bebidas» del BCRP). El MCP obliga a pasar por un código de serie y elimina esa ambigüedad.
2. **Cuando la cifra no está publicada, el Modo A no puede responder.** Esto pasa con los grupos de edad o el departamento de Lima sin Callao, que solo salen de los microdatos. Lo bueno es que respondió `null` en vez de estimar, como pedía la instrucción.
3. **Las cifras publicadas las acierta sin herramientas.** B1, B3 y E1 las respondió de memoria y lo declaró en la fuente («lo cité de memoria»). B2 y E2 las sacó de la web. Por eso la mejora real del Modo B está en las preguntas que requieren **cálculo** (B4, E3, E4, C1), no en las que repiten un titular.
4. **En el Modo B las Skills se ejecutaron sobre todo con `Bash(uv run …)`, no con la herramienta `Skill`.** El modelo leyó los SKILL.md y corrió sus scripts. Como `salidas/` empezaba vacía, en cada pregunta de la ENAHO corrió primero `limpiar.py` (con validación) y luego leyó los indicadores. En la ejecución integrada (`evidencias_ia/integracion/`) sí aparecen las cuatro activaciones con `Skill`.
5. **El Modo B fue más rápido** (19.4 s frente a 27.8 s). Una llamada al MCP cuesta menos que varias búsquedas y lecturas de páginas web.
6. **Corrección del calificador (documentada).** La primera versión del criterio «no afirma causalidad» buscaba la cadena `causa`. Por eso marcaba como incorrecta la respuesta del Modo B en C1, que decía «una asociación…, **no una relación causal**». Se cambió el criterio a verbos causales afirmativos («causó», «provocó», «debido a», «explica»…) y se recalificó con `evaluar.py --recalificar`. No se cambió ninguna respuesta esperada ni ninguna tolerancia. Con el criterio original el resultado era A 6/10 y B 9/10.

## Conclusión

Con MCP y Skills, Claude Code pasó de 6 a 10 respuestas correctas y no empeoró en ninguna pregunta. La ganancia se concentra en las preguntas que exigen una **serie exacta** (el código del BCRP) o un **cálculo con microdatos ponderados** (grupos de edad, departamentos que el INEI no publica por separado y brechas). Las cifras que ya circulan en titulares las responde bien con su conocimiento previo o con la web. Esto es lo esperable y muestra que el valor de las herramientas está en la verificabilidad y en lo que no está publicado.

**Límites del experimento:** son 10 preguntas y una sola corrida por modo y pregunta, con un único modelo. El Modo A tenía búsqueda web, así que no mide el «conocimiento puro» del modelo. Para medir variabilidad habría que repetir cada pregunta varias veces, como se hizo en la Sesión 04.

## Cómo reproducir

```bash
uv run evaluacion/respuestas_esperadas.py      # recalcula preguntas.csv (respuestas esperadas)
uv run evaluacion/evaluar.py                    # 20 sesiones de claude -p (unos 10 min, 4 en paralelo)
uv run evaluacion/evaluar.py --recalificar      # solo vuelve a calificar resultados.csv
```
