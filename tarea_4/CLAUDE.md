# Agente de investigación socioeconómica del Perú

- Datos macro: usa solo el servidor MCP `bcrp` (buscar_series, serie, resumen, comparar_series, graficar_serie).
- Microdatos: usa las skills de `.claude/skills/` (limpiando, graficando, mapeando-enaho e investigando-peru).
- Ninguna cifra de memoria: cada número sale de una herramienta o de un archivo en `salidas/`, `mapas/` o `figuras/`.
- Cita siempre el código de serie y el periodo (BCRP) o el archivo y el método de ponderación (ENAHO).
- Si una herramienta falla o no hay datos, dilo; no estimes.
- Describe asociaciones, nunca causalidad.
