# Transcripción: B_E1

Archivo original: `B_E1.jsonl`

**Sesión:** modelo `claude-sonnet-5-5` · MCP: ['bcrp connected']

### → Herramienta `Bash`

```json
{
 "command": "ls -R . | head -80; cat .claude/skills/limpiando-enaho/SKILL.md"
}
```

<details><summary>Resultado</summary>

```
.:
CLAUDE.md
datos
figuras
mapas
mcp
pyproject.toml
salidas
uv.lock

./datos:
966-Modulo02.zip
966-Modulo34.zip
catalogo_bcrp.csv
enaho01-2024-200.dta
peru_departamental_simple.geojson
referencia_sesion16.csv
sumaria-2024.dta

./figuras:

./mapas:

./mcp:
__pycache__
server.py
test_server.py

./mcp/__pycache__:
server.cpython-313.pyc
test_server.cpython-313-pytest-9.2.0.pyc

./salidas:
---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas residentes con pobreza y factor de expansión, validada contra la cifra oficial. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular la pobreza del Perú por región, departamento, área, sexo o edad.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---

# Limpiar la ENAHO

El año es `$0`; si viene vacío, usa 2024.

1. Revisa que existan `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` (966 = ENAHO 2024). Si faltan, pide al usuario bajarlos de
   `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip` y `...966-Modulo02.zip` y guardarlos en `datos/`.
2. Si `salidas/personas_<año>.parquet` y `salidas/validacion.txt` ya existen y la validación dice `VALIDADA`, sáltate el paso 3.
3. Corre exactamente, desde la raíz del repo:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio <año>`
   No reescribas la limpieza a mano ni cambies el filtro, las llaves o los pesos.
4. Lee `salidas/validacion.txt`. Si dice `NO VALIDADA` o la  […]
```
</details>

### → Herramienta `Bash`

```json
{
 "command": "cat .claude/skills/limpiando-enaho/reference.md | head -60; uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 | tail -30; cat salidas/validacion.txt"
}
```

<details><summary>Resultado</summary>

```
# Referencia: ENAHO 2024 (código INEI 966)

## Módulos

| Módulo | Archivo | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|---|
| 34 · Sumaria | sumaria-2024.dta | hogar | 33,691 | conglome, vivienda, hogar | factor07 |
| 02 · Miembros | enaho01-2024-200.dta | persona | 117,721 | las tres + codperso | facpob07 |

## Variables usadas

- `pobreza` (sumaria): 1 pobre extremo, 2 pobre no extremo, 3 no pobre. Es categoría: pobre = `pobreza <= 2`, nunca un promedio.
- `mieperho`: miembros del hogar (excluye trabajadores del hogar y pensionistas).
- `estrato`: 1 a 5 urbano, 6 a 8 rural.
- `dominio`: 1-3 costa, 4-6 sierra, 7 selva, 8 Lima Metropolitana.
- `ubigeo`: departamento (2) + provincia (2) + distrito (2). Siempre texto.
- `p203` parentesco · `p204` ¿es miembro del hogar? · `p205` ¿estuvo ausente más de 30 días? · `p206` ¿estuvo presente más de 30 días? · `p207` sexo (1 hombre, 2 mujer) · `p208a` edad.

## Residente habitual

`(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)` → 108,664 personas en 2024.

## Dos formas de ponderar

| Método | Cómo | Pobreza 2024 |
|---|---|---|
| Hogares (oficial INEI) | sumaria, `factor07 * mieperho` | 27.58 % |
| Personas | base de personas, `facpob07` | 27.53 % |

Por departamento o área las diferencias son de hasta 0.5 puntos (Puno 39.9 % vs 40.4 %). Las cifras publicadas por el INEI salen con el método de hogares: desde la base de personas se obtiene con `base.drop_duplicates(["conglome","vivienda","hogar"])` y peso `facto […]
```
</details>

### → Herramienta `StructuredOutput`

```json
{
 "valor": 5.5,
 "fuente": "ENAHO 2024 (INEI, código 966), módulo 34 sumaria (datos/sumaria-2024.dta), variable pobreza==1, ponderada por factor07 × mieperho (método de hogares, el oficial del INEI). Resultado en salidas/validacion.txt (VALIDADA): 5.50 %. Con la base de personas ponderada por facpob07 también da 5.50 %.",
 "interpretacion": "Según la ENAHO 2024, el 5.5 % de la población peruana vivía en pobreza extrema, cifra que coincide con la publicada por el INEI."
}
```

<details><summary>Resultado</summary>

```
Structured output provided successfully
```
</details>

---
**Fin:** success · 4 turnos · 8 s · US$ 0.07

Respuesta estructurada:

```json
{
 "valor": 5.5,
 "fuente": "ENAHO 2024 (INEI, código 966), módulo 34 sumaria (datos/sumaria-2024.dta), variable pobreza==1, ponderada por factor07 × mieperho (método de hogares, el oficial del INEI). Resultado en salidas/validacion.txt (VALIDADA): 5.50 %. Con la base de personas ponderada por facpob07 también da 5.50 %.",
 "interpretacion": "Según la ENAHO 2024, el 5.5 % de la población peruana vivía en pobreza extrema, cifra que coincide con la publicada por el INEI."
}
```
