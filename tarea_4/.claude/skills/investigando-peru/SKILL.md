---
name: investigando-peru
description: Coordina una investigación socioeconómica del Perú que combina series del BCRP (servidor MCP bcrp) con la pobreza de la ENAHO 2024 (skills limpiando, graficando y mapeando-enaho) y escribe un informe reproducible en informes/. Úsala cuando pidan investigar, analizar o escribir un informe que cruce inflación, tipo de cambio, PBI u otro indicador macro con la pobreza, la desigualdad territorial o los hogares peruanos.
argument-hint: [pregunta de investigación]
---

# Investigar la realidad socioeconómica del Perú

La pregunta es `$ARGUMENTS`. Trabaja en este orden y no te saltes pasos.

## 1. Plan
Escribe en `salidas/plan.md`: la pregunta, qué parte responde el BCRP y qué parte la ENAHO, las series candidatas, los indicadores ENAHO, las figuras y qué **no** se puede concluir (nivel nacional/Lima frente a departamental, años distintos, sin causalidad).

## 2. BCRP por MCP (al menos 2 herramientas distintas)
- `buscar_series` para encontrar los códigos; nunca supongas un código.
- `resumen` o `comparar_series` para promedios, variaciones, máximos y brechas. Las cuentas las hace la herramienta, no tú.
- `graficar_serie` para la figura del BCRP (guarda en `figuras/`).
- Guarda cada cifra que uses con su código, periodo y URL de fuente en `salidas/cifras_bcrp.json`.

## 3. ENAHO por Skills (al menos 2 distintas)
Actívalas con la herramienta **Skill** (`Skill(skill="limpiando-enaho")`, etc.) y sigue lo que cada una indica; no leas sus SKILL.md a mano ni reescribas sus scripts. Así queda registrado qué skill se usó.
- `limpiando-enaho` si no existe `salidas/personas_2024.parquet` o la validación no dice `VALIDADA`. Si falla, detente y repórtalo.
- `graficando-enaho` para el gráfico (área, sexo, edad o departamento).
- `mapeando-enaho` para el mapa departamental.
- Las cifras ENAHO salen de `salidas/indicadores.csv`, `mapas/pobreza_departamento.csv` o de lo que imprimen los scripts. Nunca las escribas de memoria.

## 4. Verificación
Corre `uv run ${CLAUDE_SKILL_DIR}/scripts/verificar.py`. Recalcula de forma independiente tres o más cifras del informe (al menos una del BCRP, directo de la API, y una de la ENAHO, directo de los .dta) y escribe `salidas/verificacion.md`. Si una cifra no coincide, corrige el informe, no la verificación.

## 5. Informe
Escribe `informes/informe_final.md` con estas secciones: Pregunta de investigación · Fuentes y metodología · Resultados (3 hallazgos o más, cada uno con su cifra y su fuente: código de serie y periodo, o archivo de salida) · Visualizaciones (gráfico BCRP, gráfico ENAHO y mapa, con rutas relativas `../figuras/...`) · Interpretación · Limitaciones · Verificación (tabla de `salidas/verificacion.md`) · Reproducibilidad (comandos y series).

## Reglas
- Si una herramienta falla o no hay datos, dilo en el informe en vez de inventar.
- Lenguaje descriptivo: «coincide con», «se asocia con», nunca «causa» o «explica».
- La inflación del BCRP es de Lima Metropolitana y la pobreza es nacional y departamental: dilo.
