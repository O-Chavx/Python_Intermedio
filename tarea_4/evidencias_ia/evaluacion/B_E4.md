# Transcripción: B_E4

Archivo original: `B_E4.jsonl`

**Sesión:** modelo `claude-sonnet-5-5` · MCP: ['bcrp connected']

### → Herramienta `Bash`

```json
{
 "command": "cd /tmp/t4_B_4oo3hx1j; ls -R . | head -80; cat .claude/skills/limpiando-enaho/SKILL.md"
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
 "command": "cd /tmp/t4_B_4oo3hx1j; cat .claude/skills/limpiando-enaho/reference.md; ls salidas; uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 | tail -20; cat salidas/validacion.txt"
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

### → Herramienta `Bash`

```json
{
 "command": "cd /tmp/t4_B_4oo3hx1j; uv run python -I -c \"\nimport pandas as pd\nd=pd.read_parquet('salidas/personas_2024.parquet')\nprint(d.departamento.unique()[:5])\nl=d[d.departamento=='15']\nprint(len(l), l.ubigeo.str[:2].unique())\nprint((l.pobre*l.facpob07).sum()/l.facpob07.sum()*100)\nh=l.drop_duplicates(['conglome','vivienda','hogar'])\nw=h.factor07*h.mieperho\nprint((h.pobre*w).sum()/w.sum()*100, len(h))\n\""
}
```

<details><summary>Resultado</summary>

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
warning: `VIRTUAL_ENV=tarea_4/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
<ArrowStringArray>
['15', '22', '01', '02', '03']
Length: 5, dtype: str
14823 <ArrowStringArray>
['15']
Length: 1, dtype: str
26.888768492697483
27.068941667982422 4544
```
</details>

### → Herramienta `StructuredOutput`

```json
{
 "valor": 27.07,
 "fuente": "ENAHO 2024 (INEI, código 966), módulos 34 (sumaria) y 02, base salidas/personas_2024.parquet (validada contra la cifra oficial). Departamento 15 (Lima, sin Callao). Método de hogares (oficial INEI): un registro por hogar, ponderado con factor07 × mieperho, pobre = pobreza ≤ 2. Con la base de personas ponderada con facpob07 da 26.89 %.",
 "interpretacion": "En 2024 el 27.07 % de la población del departamento de Lima (sin Callao) vivía en hogares con gasto por debajo de la línea de pobreza monetaria, según el método de hogares del INEI."
}
```

<details><summary>Resultado</summary>

```
Structured output provided successfully
```
</details>

---
**Fin:** success · 5 turnos · 12 s · US$ 0.08

Respuesta estructurada:

```json
{
 "valor": 27.07,
 "fuente": "ENAHO 2024 (INEI, código 966), módulos 34 (sumaria) y 02, base salidas/personas_2024.parquet (validada contra la cifra oficial). Departamento 15 (Lima, sin Callao). Método de hogares (oficial INEI): un registro por hogar, ponderado con factor07 × mieperho, pobre = pobreza ≤ 2. Con la base de personas ponderada con facpob07 da 26.89 %.",
 "interpretacion": "En 2024 el 27.07 % de la población del departamento de Lima (sin Callao) vivía en hogares con gasto por debajo de la línea de pobreza monetaria, según el método de hogares del INEI."
}
```
