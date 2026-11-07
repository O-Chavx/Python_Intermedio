# Verificación independiente de cifras

Generado por `.claude/skills/investigando-peru/scripts/verificar.py`. Los valores recalculados no usan el servidor MCP ni los scripts de las skills: salen de la API del BCRP y de los .dta del INEI.

| Fuente   | Afirmación                                                            |   Valor en el informe |   Valor recalculado |   Diferencia |   Tolerancia | Coincide   | Cómo se verificó                                                             |
|:---------|:----------------------------------------------------------------------|----------------------:|--------------------:|-------------:|-------------:|:-----------|:-----------------------------------------------------------------------------|
| BCRP     | Inflación de alimentos y bebidas, promedio ene-2020 a dic-2024 (%)    |                  5.88 |                5.88 |       -0     |         0.01 | Sí         | API BCRP PN09822PM 2020-01–2024-12, promedio con pandas                      |
| BCRP     | Inflación general (IPC), promedio ene-2020 a dic-2024 (%)             |                  4.47 |                4.47 |        0     |         0.01 | Sí         | API BCRP PN01273PM 2020-01–2024-12, promedio con pandas                      |
| BCRP     | Máximo de la inflación de alimentos y bebidas 2020-2024 (feb-2023, %) |                 13.16 |               13.16 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2020-01–2024-12, maximo con pandas                        |
| BCRP     | Máximo de la inflación general 2020-2024 (jun-2022, %)                |                  8.81 |                8.81 |        0     |         0.01 | Sí         | API BCRP PN01273PM 2020-01–2024-12, maximo con pandas                        |
| BCRP     | Mínimo de la inflación de alimentos y bebidas 2020-2024 (set-2024, %) |                  0.69 |                0.69 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2020-01–2024-12, minimo con pandas                        |
| BCRP     | Inflación de alimentos y bebidas, ene-2020 (%)                        |                  1.11 |                1.11 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2020-01–2024-12, primero con pandas                       |
| BCRP     | Inflación general, ene-2020 (%)                                       |                  1.89 |                1.89 |        0     |         0.01 | Sí         | API BCRP PN01273PM 2020-01–2024-12, primero con pandas                       |
| BCRP     | Inflación de alimentos y bebidas, dic-2024 (%)                        |                  1.25 |                1.25 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2020-01–2024-12, ultimo con pandas                        |
| BCRP     | Inflación general, dic-2024 (%)                                       |                  1.97 |                1.97 |        0     |         0.01 | Sí         | API BCRP PN01273PM 2020-01–2024-12, ultimo con pandas                        |
| BCRP     | Inflación de alimentos y bebidas, may-2023 (%)                        |                 13.07 |               13.07 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2023-05–2023-05, valor con pandas                         |
| BCRP     | Inflación general, may-2023 (%)                                       |                  7.89 |                7.89 |        0     |         0.01 | Sí         | API BCRP PN01273PM 2023-05–2023-05, valor con pandas                         |
| BCRP     | Inflación de alimentos y bebidas, promedio 2024 (%)                   |                  2.01 |                2.01 |        0     |         0.01 | Sí         | API BCRP PN09822PM 2024-01–2024-12, promedio con pandas                      |
| BCRP     | Inflación general, promedio 2024 (%)                                  |                  2.35 |                2.35 |       -0     |         0.01 | Sí         | API BCRP PN01273PM 2024-01–2024-12, promedio con pandas                      |
| ENAHO    | Pobreza monetaria nacional 2024 (%)                                   |                 27.58 |               27.58 |        0.001 |         0.05 | Sí         | sumaria-2024.dta leída de nuevo, factor07 × mieperho; referencia INEI 27.6 % |
| ENAHO    | Pobreza rural 2024 (%)                                                |                 39.3  |               39.3  |       -0.003 |         0.05 | Sí         | estrato 6-8; referencia 39.3 %                                               |
| ENAHO    | Pobreza urbana 2024 (%)                                               |                 24.81 |               24.81 |        0.003 |         0.05 | Sí         | estrato 1-5; referencia 24.8 %                                               |
| ENAHO    | Departamento con más pobreza: Cajamarca (%)                           |                 45    |               45.01 |       -0.007 |         0.05 | Sí         | sumaria por ubigeo[:2] = 06; referencia Sesión 16 45.0 %                     |
| ENAHO    | Departamentos en el mapa                                              |                 25    |               25    |        0     |         0    | Sí         | ubigeo[:2] distintos en la sumaria                                           |

**Resultado:** 18/18 cifras coinciden.

## Verificación complementaria (cifras de par y extremos departamentales)

Generado por un script aparte (`salidas/verif_extra.py`; correr con `uv run salidas/verif_extra.py` después de `verificar.py`) con la misma lógica: API del BCRP con httpx y sumaria-2024.dta con pandas; no usa el servidor MCP ni los scripts de las skills. Compara contra `salidas/cifras_bcrp_comparacion.json` y `mapas/pobreza_departamento.csv`.

| Fuente   | Afirmación                                               |   Valor en el informe |   Valor recalculado |   Diferencia |   Tolerancia | Coincide   | Cómo se verificó                                                                    |
|:---------|:---------------------------------------------------------|----------------------:|--------------------:|-------------:|-------------:|:-----------|:------------------------------------------------------------------------------------|
| BCRP     | Brecha promedio alimentos − general 2020-01–2024-12 (pp) |                1.4179 |              1.4179 |      -0      |        0.01  | Sí         | API BCRP PN09822PM − PN01273PM 2020-01–2024-12, pandas                              |
| BCRP     | Mayor brecha 2020-01–2024-12 (pp, 2023-05)               |                5.1775 |              5.1775 |       0      |        0.01  | Sí         | API BCRP PN09822PM − PN01273PM 2020-01–2024-12, pandas; periodo recalculado 2023-05 |
| BCRP     | Meses con alimentos > general 2020-01–2024-12            |               44      |             44      |       0      |        0     | Sí         | API BCRP PN09822PM − PN01273PM 2020-01–2024-12, pandas                              |
| BCRP     | Correlación de Pearson 2020-01–2024-12                   |                0.9807 |              0.9807 |       0      |        0.001 | Sí         | API BCRP PN09822PM − PN01273PM 2020-01–2024-12, pandas                              |
| BCRP     | Brecha promedio alimentos − general 2024-01–2024-12 (pp) |               -0.3403 |             -0.3403 |       0      |        0.01  | Sí         | API BCRP PN09822PM − PN01273PM 2024-01–2024-12, pandas                              |
| BCRP     | Mayor brecha 2024-01–2024-12 (pp, 2024-01)               |                1.2554 |              1.2554 |       0      |        0.01  | Sí         | API BCRP PN09822PM − PN01273PM 2024-01–2024-12, pandas; periodo recalculado 2024-01 |
| BCRP     | Meses con alimentos > general 2024-01–2024-12            |                3      |              3      |       0      |        0     | Sí         | API BCRP PN09822PM − PN01273PM 2024-01–2024-12, pandas                              |
| BCRP     | Correlación de Pearson 2024-01–2024-12                   |                0.9743 |              0.9743 |      -0      |        0.001 | Sí         | API BCRP PN09822PM − PN01273PM 2024-01–2024-12, pandas                              |
| ENAHO    | Departamento con menos pobreza: Ica (%)                  |                6      |              6.0142 |      -0.0142 |        0.05  | Sí         | sumaria-2024.dta leída de nuevo, factor07 × mieperho, ubigeo[:2]                    |
| ENAHO    | Pobreza Lima (%)                                         |               27.1    |             27.0689 |       0.0311 |        0.05  | Sí         | sumaria-2024.dta leída de nuevo, factor07 × mieperho, ubigeo[:2]                    |
| ENAHO    | Pobreza Callao (%)                                       |               33.9    |             33.8599 |       0.0401 |        0.05  | Sí         | sumaria-2024.dta leída de nuevo, factor07 × mieperho, ubigeo[:2]                    |

**Resultado complementario:** 11/11 cifras coinciden.
