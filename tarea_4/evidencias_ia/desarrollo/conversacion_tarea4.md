# Conversación con Claude: construcción de la Tarea 4 (4 al 7 de noviembre de 2026)

Esta es la exportación de los mensajes del hilo «Construir agente socioeconómico Tarea 4» del proyecto en claude.ai. Se omitieron las tarjetas automáticas de estado; sus contenidos se resumen entre corchetes. El trabajo técnico de este hilo (comandos, ediciones y resultados) quedó registrado en los archivos del repositorio y en las transcripciones completas de `../integracion/` y `../evaluacion/`, que son sesiones de Claude Code ejecutadas por el agente.

**Oscar (04-nov, 02:04):** *(pega el enunciado completo del issue «2026_Tarea_4» #201 de d2cml-ai/Data-Science-Python)* «mira tenemos un nuevo ejercicio, crees que me podrias ayudar?»

**Claude (02:05):** ¡Sí, claro! La buena noticia es que ya tienes casi la mitad hecha. El MCP del BCRP de la sesión 04 pasa las 8 pruebas, tiene recurso y prompt, y las 3 Skills de la sesión 16 ya validan 108,664 personas, 27.58 % y las 25 unidades del mapa.

Lo que falta:
1. Una herramienta propia más fuerte, `comparar_series` (alinea dos series por período y calcula variaciones y correlación), con sus 2 pruebas para llegar a 10 passed.
2. Juntar todo en `tarea_4/` con la estructura que pide el issue.
3. Una ejecución de Claude Code que use 2 herramientas MCP y 2 Skills, y que genere `informe_final.md` con la verificación de 3 cifras.
4. Las 10 preguntas nuevas (4 BCRP, 4 ENAHO, 2 mixtas), los Modos A/B, `comparacion.md`, el README y `evidencias_ia/`.

Pregunta que te propongo: *¿Cómo evolucionó la inflación de alimentos frente a la inflación general entre 2020 y 2024, y qué brechas urbano/rural y departamentales de pobreza monetaria había en 2024?* Tiene sentido porque los alimentos pesan más en la canasta de los hogares pobres. La presentaría como contexto descriptivo, no como causa.

[Avance registrado en las tarjetas de estado:
- MCP con `comparar_series` y `graficar_serie`: 10 passed.
- Validación urbano/rural en `limpiando-enaho`: 24.81 % y 39.30 %, más `indicadores.csv` y la comparación del mapa con la Sesión 16.
- Skill `investigando-peru` y `verificar.py`.
- Ejecución integrada con un pedido en lenguaje natural: 4 Skills y 4 herramientas MCP.
- Informe con 23/23 cifras verificadas.
- Evaluación: A 6/10 y B 10/10.
- README.]

**Claude (02:30):** Ya tienes la `tarea_4/` completa y probada. Solo falta subirla a GitHub y completar las evidencias de IA.
- **MCP:** 10/10 passed. Las 8 pruebas del curso no se tocaron, y las 2 nuevas prueban `comparar_series`.
- **ENAHO:** 27.58 % de pobreza, 108,664 residentes y 25/25 departamentos. Urbana 24.81 % y rural 39.30 %.
- **Agente:** con un pedido en lenguaje natural, una sola sesión de Claude Code usó 4 Skills y 4 herramientas MCP y escribió el informe. Tiene 4 hallazgos y 23/23 cifras recalculadas por otro script.
- **Evaluación:** sin MCP/Skills acertó 6/10 y con MCP/Skills 10/10.

Durante la evaluación se encontró y se corrigió un error del calificador. El criterio «no afirma causalidad» castigaba la frase «no es una relación causal». Se documentó en `evaluacion/comparacion.md` sin cambiar respuestas esperadas ni tolerancias.

**Oscar (07-nov, 16:05):** si necesito retomar ese y ver si falta algo para entregarla de una vez

**Claude (07-nov):** Revisé la entrega contra la lista de verificación del issue y volví a correr las pruebas: 10 passed. Agregué a `evidencias_ia/` las conversaciones del desarrollo del MCP (Sesión 04), de las Skills (Sesión 16) y de este hilo. Subí `tarea_4/` al repositorio del curso `O-Chavx/Python_Intermedio` en la rama `tarea-4`, con un pull request para unirla a `main`.
