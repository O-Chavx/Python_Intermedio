# Transcripción: B_E2

Archivo original: `B_E2.jsonl`

**Sesión:** modelo `claude-sonnet-5-5` · MCP: ['bcrp connected']

### → Herramienta `Bash`

```json
{
 "command": "ls -R salidas mapas figuras .claude/skills 2>&1 | head -50"
}
```

<details><summary>Resultado</summary>

```
.claude/skills:
graficando-enaho
investigando-peru
limpiando-enaho
mapeando-enaho

.claude/skills/graficando-enaho:
SKILL.md
scripts

.claude/skills/graficando-enaho/scripts:
graficar.py

.claude/skills/investigando-peru:
SKILL.md
scripts

.claude/skills/investigando-peru/scripts:
__pycache__
verificar.py

.claude/skills/investigando-peru/scripts/__pycache__:
verificar.cpython-313.pyc

.claude/skills/limpiando-enaho:
SKILL.md
reference.md
scripts

.claude/skills/limpiando-enaho/scripts:
limpiar.py

.claude/skills/mapeando-enaho:
SKILL.md
scripts

.claude/skills/mapeando-enaho/scripts:
mapear.py

figuras:

mapas:

salidas:
```
</details>

### → Herramienta `Bash`

```json
{
 "command": "cd /tmp/t4_B_fozjuitw/.claude/skills/limpiando-enaho && cat SKILL.md && head -60 scripts/limpiar.py && ls /tmp/t4_B_fozjuitw"
}
```

<details><summary>Resultado</summary>

```
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
4. Lee `salidas/validacion.txt`. Si dice `NO VALIDADA` o la pobreza difiere del INEI en más de 0.1 puntos, detente y reporta qué chequeo falló.
5. Responde con `salidas/personas_<año>.parquet`. Toda cifra va ponderada con `facpob07`, nunca como conteo de encuestas:
   `(pobre * facpob07).sum() / facpob07.sum() * 100`.
   Para una cifra regional que deba coincidir con la publicada por el INEI, usa un registro por hogar ponderado con `factor07 * m […]
```
</details>

### → Herramienta `Bash`

```json
{
 "command": "cd /tmp/t4_B_fozjuitw && ls datos; cat .claude/skills/limpiando-enaho/reference.md | head -60"
}
```

<details><summary>Resultado</summary>

```
966-Modulo02.zip
966-Modulo34.zip
catalogo_bcrp.csv
enaho01-2024-200.dta
peru_departamental_simple.geojson
referencia_sesion16.csv
sumaria-2024.dta
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

Por departamento o área las diferencias son de hasta 0.5 puntos (Puno 39.9 % vs 40.4 %). Las cifras publicadas por el […]
```
</details>

### → Herramienta `Bash`

```json
{
 "command": "uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024 2>&1 | tail -20; cat salidas/validacion.txt"
}
```

<details><summary>Resultado</summary>

```
Pobreza urbana, sumaria:                   24.81 %   (referencia: 24.8 %)
Pobreza rural, sumaria:                    39.30 %   (referencia: 39.3 %)
Pobreza, base de personas (facpob07):      27.53 %
Pobreza extrema, base de personas:          5.50 %

[OK] Llaves de hogar únicas en la sumaria
[OK] Llaves de persona únicas
[OK] La unión no perdió ni duplicó filas
[OK] Residentes habituales = 108,664
[OK] Pobreza (sumaria) a menos de 0.1 pts de 27.6 %
[OK] Pobreza extrema (sumaria) a menos de 0.1 pts de 5.5 %
[OK] Pobreza urbana a menos de 0.2 pts de 24.8 %
[OK] Pobreza rural a menos de 0.2 pts de 39.3 %
[OK] Suma de facpob07 entre 33 y 35 millones (población del Perú)
[OK] 25 departamentos con dato

Resultado: VALIDADA

Base guardada en salidas/personas_2024.parquet (108,664 filas, 26 columnas)
Indicadores en salidas/indicadores.csv
Validación ENAHO 2024 (código INEI 966)

Hogares en la sumaria:               33,691
Filas en el módulo 200:             117,721
Residentes habituales:              108,664
Población expandida (facpob07):      34,147,768

Pobreza, sumaria (factor07 × mieperho):    27.58 %   (INEI: 27.6 %)
Pobreza extrema, sumaria:                   5.50 %   (INEI: 5.5 %)
Pobreza urbana, sumaria:                   24.81 %   (referencia: 24.8 %)
Pobreza rural, sumaria:                    39.30 %   (referencia: 39.3 %)
Pobreza, base de personas (facpob07):      27.53 %
Pobreza extrema, base de personas:          5.50 %

[OK] Llaves de hogar únicas en la sumaria
[OK] Ll […]
```
</details>

### → Herramienta `Bash`

```json
{
 "command": "uv run python -I -c \"\nimport pandas as pd\nb=pd.read_parquet('salidas/personas_2024.parquet')\np=b[b.departamento=='21']\nprint(len(p),(p.pobre*p.facpob07).sum()/p.facpob07.sum()*100)\nh=p.drop_duplicates(['conglome','vivienda','hogar']);w=h.factor07*h.mieperho\nprint(len(h),(h.pobre*w).sum()/w.sum()*100)\n\""
}
```

<details><summary>Resultado</summary>

```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
warning: `VIRTUAL_ENV=tarea_4/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
3112 40.41768284216336
1123 39.93807599481281
```
</details>

### → Herramienta `StructuredOutput`

```json
{
 "valor": 39.9,
 "fuente": "ENAHO 2024 (INEI, código 966), módulos 34 (sumaria) y 02, base validada en salidas/personas_2024.parquet (VALIDADA, nacional 27.58 % vs 27.6 % del INEI). Departamento 21 (Puno), un registro por hogar (1,123 hogares) ponderado con factor07 × mieperho (método oficial INEI): 39.94 %. Con la base de personas ponderada con facpob07 sale 40.42 %.",
 "interpretacion": "Alrededor del 39.9 % de las personas en Puno vivían en pobreza monetaria en 2024, por encima del 27.6 % nacional; con ponderación por personas (facpob07) la cifra sería 40.4 %.",
 "valor_2": null
}
```

<details><summary>Resultado</summary>

```
Structured output provided successfully
```
</details>

---
**Fin:** success · 7 turnos · 14 s · US$ 0.10

Respuesta estructurada:

```json
{
 "valor": 39.9,
 "fuente": "ENAHO 2024 (INEI, código 966), módulos 34 (sumaria) y 02, base validada en salidas/personas_2024.parquet (VALIDADA, nacional 27.58 % vs 27.6 % del INEI). Departamento 21 (Puno), un registro por hogar (1,123 hogares) ponderado con factor07 × mieperho (método oficial INEI): 39.94 %. Con la base de personas ponderada con facpob07 sale 40.42 %.",
 "interpretacion": "Alrededor del 39.9 % de las personas en Puno vivían en pobreza monetaria en 2024, por encima del 27.6 % nacional; con ponderación por personas (facpob07) la cifra sería 40.4 %.",
 "valor_2": null
}
```
