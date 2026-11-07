# Evidencias del uso de IA

Asistente usado: Claude (Claude Code y claude.ai). Las transcripciones `.jsonl` son la salida cruda de `claude -p --output-format stream-json`. Los `.md` son la versión legible, generada con `convertir.py`, que también oculta las rutas locales y cualquier clave.

| Carpeta | Qué contiene | Etapa |
|---|---|---|
| `mcp/` | `conversacion_mcp_bcrp_sesion04.md`: conversación del desarrollo del servidor del BCRP (Sesión 04). `pytest_10_passed.txt`: salida de las pruebas | Desarrollo del MCP y pruebas |
| `skills/` | `conversacion_skills_enaho_sesion16.md`: conversación del desarrollo de las Skills de la ENAHO (Sesión 16) | Desarrollo de las Skills |
| `integracion/` | `ejecucion.md`/`.jsonl`: la sesión en que Claude Code respondió la pregunta de investigación usando 4 Skills y 4 herramientas MCP. `prompt.txt` es el pedido exacto. `corrida_1_slash/` es una primera corrida invocada con `/investigando-peru`. | Integración e informe |
| `evaluacion/` | `A_<id>.md` y `B_<id>.md`: las 20 sesiones independientes del experimento (10 preguntas × 2 modos), con `log_evaluar.txt` | Evaluación |
| `desarrollo/` | `conversacion_tarea4.md`: conversación con el asistente que construyó la Tarea 4 (plan, extensión del MCP y las Skills, integración, evaluación, correcciones y entrega) | Integración, correcciones y documentación |

## Cronología

1. **29-oct-2026:** servidor MCP del BCRP (Sesión 04): `server.py`, 8 pruebas y evaluación memoria/web/MCP.
2. **31-oct-2026:** Skills `limpiando`, `graficando` y `mapeando-enaho` (Sesión 16), validadas en 27.58 % y 108,664.
3. **04-nov-2026:** Tarea 4. Se agregaron `comparar_series` y `graficar_serie` con 2 pruebas (10 passed), las validaciones urbano/rural, `indicadores.csv`, la comparación del mapa con la Sesión 16, la Skill `investigando-peru` con `verificar.py`, la ejecución integrada, las preguntas, los Modos A/B y la documentación.
