# Inflación de alimentos y pobreza monetaria en el Perú, 2020-2024

## Pregunta de investigación

¿Cómo evolucionó la inflación de alimentos frente a la inflación general en el Perú entre 2020 y 2024, y qué brechas urbano/rural y departamentales presentaba la pobreza monetaria al cierre de ese período (ENAHO 2024)?

## Fuentes y metodología

**Inflación (BCRP, servidor MCP `bcrp`).** Las series se ubicaron con `buscar_series` («ipc 12 meses», «alimentos 12 meses»; frecuencia mensual):

| Código | Serie | Cobertura |
|---|---|---|
| `PN01273PM` | Índice de precios Lima Metropolitana (var. % 12 meses) – IPC | Lima Metropolitana |
| `PN09822PM` | Índice de precios Lima Metropolitana (var. % 12 meses) – IPC Alimentos y Bebidas | Lima Metropolitana |

Se descartó `PN09819PM` (alimentos **y energía**) porque mezcla energía. Las cifras salen de `resumen` (promedios, máximos, mínimos, valores puntuales) y `comparar_series` (brecha alimentos − general, mes de mayor brecha, meses en que alimentos supera al general, correlación de Pearson), en 60 meses comunes de 2020-01 a 2024-12 sin periodos descartados. La figura se hizo con `graficar_serie`. Todas las cifras están en `salidas/cifras_bcrp.json` y `salidas/cifras_bcrp_comparacion.json`, con código, periodo y URL.

**Pobreza (ENAHO 2024, INEI, código 966, módulos 34 y 02).** Se siguieron tres skills:
- `limpiando-enaho`: armó `salidas/personas_2024.parquet` (108,664 residentes habituales; 33,691 hogares) y `salidas/indicadores.csv`. La validación (`salidas/validacion.txt`) dice **VALIDADA**: pobreza nacional 27.58 % (INEI: 27.6 %).
- `graficando-enaho --por area` y `--por departamento`.
- `mapeando-enaho`: mapa coroplético unido por `ubigeo[:2]` = `FIRST_IDDP`, 25 departamentos, Lima (15) y Callao (07) separados. Coincide al decimal con 7 de 7 cifras de referencia (`mapas/comparacion_sesion16.csv`).

**Ponderación.** Las cifras de área y departamento usan el método oficial del INEI: un registro por hogar, ponderado con `factor07 × mieperho`. Pobre = `pobreza ≤ 2` en la sumaria.

## Resultados

**Hallazgo 1. Entre 2020 y 2024, la inflación de alimentos fue en promedio más alta y más volátil que la inflación general.**
- La inflación de alimentos y bebidas promedió **5.88 %** (`PN09822PM`, 2020-01 a 2024-12) y la general **4.47 %** (`PN01273PM`, mismo periodo). La brecha promedio fue **1.42 puntos porcentuales** (`comparar_series`).
- Los alimentos superaron al índice general en **44 de 60 meses** (`comparar_series`, 2020-01 a 2024-12).
- Las dos series se movieron juntas. La correlación de Pearson fue **0.98**, una medida descriptiva.

**Hallazgo 2. El pico de 2022-2023 fue más alto y más tardío en alimentos, y en 2024 la relación se invirtió.**
- La inflación general tocó su máximo en **junio de 2022 con 8.81 %**. La de alimentos lo tocó en **febrero de 2023 con 13.16 %** (`resumen`, 2020-01 a 2024-12).
- La mayor brecha fue en **mayo de 2023: 5.18 puntos**. Ese mes, alimentos marcó 13.07 % y el índice general 7.89 % (`comparar_series`; `resumen` 2023-05).
- En 2024, alimentos promedió **2.01 %** frente a **2.35 %** del índice general, con una brecha promedio de **−0.34 puntos**. Alimentos superó al general en solo 3 de 12 meses (`comparar_series`, 2024-01 a 2024-12). El mínimo del periodo para alimentos fue **0.69 % en septiembre de 2024**.
- En diciembre de 2024, alimentos estaba en **1.25 %** y la inflación general en **1.97 %**. En enero de 2020 habían estado en 1.11 % y 1.89 %, respectivamente (`PN09822PM`, `PN01273PM`).

**Hallazgo 3. En 2024, la pobreza monetaria rural fue mucho mayor que la urbana.**
- Pobreza nacional: **27.6 %** (27.58 %).
- Pobreza rural: **39.3 %**. Pobreza urbana: **24.8 %** (`salidas/indicadores.csv`, `factor07 × mieperho`).
- La pobreza extrema muestra una distancia todavía mayor: **15.52 %** rural frente a **3.14 %** urbana (`salidas/indicadores.csv`).
- La población expandida es de 27.9 millones en zonas urbanas y 6.6 millones en zonas rurales (`salidas/indicadores.csv`, columna `poblacion_expandida`). Una tasa urbana menor puede corresponder igual a más personas pobres. Ese conteo no se calculó aquí.

**Hallazgo 4. La pobreza departamental de 2024 va de 6.0 % a 45.0 %.**
- Los departamentos con más pobreza son **Cajamarca (45.0 %)**, **Loreto (43.0 %)** y **Puno (39.9 %)**. Les siguen Pasco y Huánuco, ambos con 39.0 %.
- Los departamentos con menos pobreza son **Ica (6.0 %)**, **Moquegua (11.0 %)** y **Madre de Dios (11.1 %)** (`mapas/pobreza_departamento.csv`, `factor07 × mieperho`).
- Callao (**33.9 %**) está por encima de Lima (**27.1 %**). Ambos forman la zona a la que corresponde el IPC de Lima Metropolitana (`mapas/pobreza_departamento.csv`).

## Visualizaciones

**Gráfico BCRP.** Inflación general y de alimentos y bebidas (var. % 12 meses), Lima Metropolitana, 2020-2024 (`PN01273PM`, `PN09822PM`):

![Inflación general vs alimentos](../figuras/inflacion_alimentos_vs_general_2020_2024.png)

**Gráfico ENAHO.** Pobreza monetaria por área de residencia, Perú 2024:

![Pobreza por área](../figuras/pobreza_area_2024.png)

**Gráfico ENAHO complementario.** Pobreza por departamento, en barras:

![Pobreza por departamento (barras)](../figuras/pobreza_departamento_2024.png)

**Mapa.** Pobreza monetaria por departamento, Perú 2024:

![Mapa de pobreza departamental](../mapas/pobreza_departamento.png)

## Interpretación

Entre 2020 y 2024, la inflación de alimentos de Lima Metropolitana siguió el ciclo del índice general (correlación 0.98) con más amplitud. Subió más, tocó su máximo ocho meses después y se mantuvo por encima del general durante la mayor parte del periodo. En 2024 bajó por debajo de la inflación general.

Al cierre del periodo, la ENAHO 2024 muestra fuertes desigualdades territoriales en la pobreza monetaria:
- La tasa rural (39.3 %) es mayor que la urbana (24.8 %).
- Varios departamentos de sierra y selva (Cajamarca, Loreto, Puno, Pasco, Huánuco) tienen tasas cercanas al 40 % o mayores, mientras que Ica está en 6.0 %.

Que la inflación de alimentos haya sido alta en 2022-2023 **coincide** con el periodo previo a la medición de 2024. Este análisis **no** permite decir que una cosa explique la otra. No se modeló ninguna relación, no hay serie de pobreza en el tiempo y las dos fuentes miden territorios distintos.

## Limitaciones

- **Cobertura geográfica distinta.** La inflación del BCRP (`PN01273PM`, `PN09822PM`) es **solo de Lima Metropolitana**. La pobreza es nacional, por área y por departamento. No se puede suponer que los precios de cada departamento o de las zonas rurales siguieron la trayectoria de Lima.
- **Años distintos.** La inflación cubre 60 meses (2020-2024). La pobreza es un solo corte transversal (ENAHO 2024). Este informe no mide cómo cambió la pobreza entre 2020 y 2024.
- **Sin causalidad.** Las correlaciones y coincidencias son descriptivas.
- **Variación % de una tasa.** Las herramientas devuelven un campo `variacion_pct` de las series de inflación, que mide el cambio porcentual de una tasa. No se usa porque no tiene una interpretación económica útil.
- **Error muestral.** Las cifras departamentales de la ENAHO tienen error muestral (entre 603 y 4,544 hogares por departamento, según `n_muestra` en `salidas/indicadores.csv`). Las diferencias pequeñas, como Pasco frente a Huánuco o Lima frente a Ucayali, no deben leerse como distintas. No se calcularon intervalos de confianza.
- **Método de ponderación.** Con `facpob07` (base de personas), la tasa nacional sale 27.53 % (`salidas/validacion.txt`). Este informe usa `factor07 × mieperho` para replicar las cifras oficiales.

## Verificación

Primero se corrió `uv run .claude/skills/investigando-peru/scripts/verificar.py`. Ese script vuelve a pedir los datos a la API del BCRP con httpx, vuelve a leer `sumaria-2024.dta` con pandas y no usa el MCP ni los scripts de las skills. Dio **18/18 cifras coinciden**. Después, `uv run salidas/verif_extra.py` recalculó de forma independiente las cifras de par (brecha, mayor brecha, meses, correlación) y los extremos departamentales: **11/11 coinciden**. El detalle completo está en `salidas/verificacion.md`.

| Fuente | Afirmación | Informe | Recalculado | Coincide | Cómo se verificó |
|:--|:--|--:|--:|:--|:--|
| BCRP | Alimentos y bebidas, promedio 2020-01–2024-12 (%) | 5.88 | 5.88 | Sí | API BCRP `PN09822PM`, promedio con pandas |
| BCRP | IPC general, promedio 2020-01–2024-12 (%) | 4.47 | 4.47 | Sí | API BCRP `PN01273PM`, promedio |
| BCRP | Máximo alimentos (feb-2023, %) | 13.16 | 13.16 | Sí | API BCRP `PN09822PM`, máximo |
| BCRP | Máximo IPC general (jun-2022, %) | 8.81 | 8.81 | Sí | API BCRP `PN01273PM`, máximo |
| BCRP | Mínimo alimentos (set-2024, %) | 0.69 | 0.69 | Sí | API BCRP `PN09822PM`, mínimo |
| BCRP | Alimentos ene-2020 / dic-2024 (%) | 1.11 / 1.25 | 1.11 / 1.25 | Sí | API BCRP `PN09822PM`, primero/último |
| BCRP | IPC general ene-2020 / dic-2024 (%) | 1.89 / 1.97 | 1.89 / 1.97 | Sí | API BCRP `PN01273PM`, primero/último |
| BCRP | Alimentos / general, may-2023 (%) | 13.07 / 7.89 | 13.07 / 7.89 | Sí | API BCRP, valor puntual |
| BCRP | Promedio 2024 alimentos / general (%) | 2.01 / 2.35 | 2.01 / 2.35 | Sí | API BCRP 2024-01–2024-12, promedio |
| BCRP | Brecha promedio 2020-2024 (pp) | 1.4179 | 1.4179 | Sí | API BCRP, diferencia con pandas |
| BCRP | Mayor brecha 2020-2024 (pp, may-2023) | 5.1775 | 5.1775 | Sí | API BCRP; periodo recalculado 2023-05 |
| BCRP | Meses con alimentos > general, 2020-2024 | 44 | 44 | Sí | API BCRP |
| BCRP | Correlación 2020-2024 | 0.9807 | 0.9807 | Sí | API BCRP, `corr` de pandas |
| BCRP | Brecha promedio 2024 (pp) / meses con alimentos > general | −0.3403 / 3 | −0.3403 / 3 | Sí | API BCRP 2024 |
| ENAHO | Pobreza nacional 2024 (%) | 27.58 | 27.58 | Sí | `sumaria-2024.dta`, `factor07 × mieperho` |
| ENAHO | Pobreza rural 2024 (%) | 39.30 | 39.30 | Sí | estrato 6-8 |
| ENAHO | Pobreza urbana 2024 (%) | 24.81 | 24.81 | Sí | estrato 1-5 |
| ENAHO | Cajamarca (%) | 45.0 | 45.01 | Sí | sumaria, `ubigeo[:2]` = 06 |
| ENAHO | Ica (%) | 6.0 | 6.01 | Sí | sumaria, `ubigeo[:2]` = 11 |
| ENAHO | Lima / Callao (%) | 27.1 / 33.9 | 27.07 / 33.86 | Sí | sumaria, `ubigeo[:2]` = 15 / 07 |
| ENAHO | Departamentos en el mapa | 25 | 25 | Sí | `ubigeo[:2]` distintos |

## Reproducibilidad

Desde la raíz del repositorio:

```bash
# ENAHO
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por departamento
uv run .claude/skills/mapeando-enaho/scripts/mapear.py
# Verificación
uv run .claude/skills/investigando-peru/scripts/verificar.py
uv run salidas/verif_extra.py
```

Llamadas al servidor MCP `bcrp`:
- `buscar_series("ipc 12 meses", "Mensual")` y `buscar_series("alimentos 12 meses", "Mensual")`.
- `comparar_series("PN09822PM", "PN01273PM", "2020-01", "2024-12")` y `comparar_series("PN09822PM", "PN01273PM", "2024-01", "2024-12")`.
- `resumen("PN09822PM", "2020-01", "2024-12")` y `resumen("PN01273PM", "2020-01", "2024-12")`.
- `resumen(<código>, "2023-05", "2023-05")` para cada serie.
- `graficar_serie(["PN01273PM", "PN09822PM"], "2020-01", "2024-12")`, que guarda `figuras/inflacion_alimentos_vs_general_2020_2024.png`.

Fuentes:
- BCRP: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/html/2020-1/2024-12` y `.../PN09822PM/html/2020-1/2024-12`.
- INEI: ENAHO 2024, `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip`.
- Geometría: `datos/peru_departamental_simple.geojson`.
