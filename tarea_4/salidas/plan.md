# Plan de investigación

## Pregunta
¿Cómo evolucionó la inflación de alimentos frente a la inflación general en el Perú entre 2020 y 2024, y qué brechas urbano/rural y departamentales presentaba la pobreza monetaria al cierre de ese período según la ENAHO 2024?

## Qué responde cada fuente
- **BCRP (servidor MCP `bcrp`)**: evolución mensual 2020-01 a 2024-12 de la inflación interanual de alimentos y bebidas frente a la inflación general (IPC de **Lima Metropolitana**).
- **ENAHO 2024 (INEI, skills de `.claude/skills/`)**: tasa de pobreza monetaria ponderada (factor de expansión poblacional) a nivel nacional, por área urbana/rural y por departamento.

## Series BCRP candidatas (halladas con `buscar_series`)
| Código | Serie |
|---|---|
| PN09822PM | IPC Lima Metropolitana, Alimentos y Bebidas (var% 12 meses) |
| PN01273PM | IPC Lima Metropolitana, total (var% 12 meses) |
| PN09823PM | IPC Lima Metropolitana, sin Alimentos y Bebidas (var% 12 meses) — referencia opcional |

Herramientas: `comparar_series` (brecha, máximo, correlación), `resumen` (promedios, picos y valores de diciembre por año), `graficar_serie` (figura).

## Indicadores ENAHO
- Pobreza monetaria total nacional (personas residentes, ponderada), validada contra la cifra oficial.
- Pobreza por área (urbano/rural) y brecha en puntos porcentuales.
- Pobreza por departamento (25), con máximos y mínimos.

## Figuras
1. `figuras/` — inflación de alimentos vs. general 2020-2024 (BCRP, `graficar_serie`).
2. `figuras/` — barras de pobreza por área (skill `graficando-enaho`).
3. `mapas/` — coroplético de pobreza por departamento (skill `mapeando-enaho`).

## Qué NO se puede concluir
- La inflación del BCRP es de **Lima Metropolitana**; la pobreza es **nacional y departamental**. No hay inflación departamental en este análisis.
- Las series de inflación cubren 2020-2024; la pobreza es un corte transversal de **2024**. No se puede trazar una trayectoria de pobreza con estos datos.
- No se infiere causalidad: solo se describen coincidencias y asociaciones.
- La ENAHO es una muestra: las cifras departamentales tienen error muestral (no se calculan intervalos aquí salvo que el script los dé).
