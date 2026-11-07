"""Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO y arma una base de personas.

Uso: uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Siete pasos, siempre en el mismo orden: leer, normalizar, filtrar, unir,
construir, validar y guardar.
"""
import argparse
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

# Código del portal de microdatos del INEI para cada año de la ENAHO
CODIGOS = {2024: "966"}
# Cifras oficiales del INEI: (pobreza %, pobreza extrema %, residentes habituales)
OFICIAL = {2024: (27.6, 5.5, 108_664)}
# Referencias de la Tarea 4: pobreza urbana y rural (%)
OFICIAL_AREA = {2024: (24.8, 39.3)}

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
TEXTO = LLAVES_PERSONA + ["ubigeo"]

COLS_SUMARIA = LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07"]
COLS_MIEMBROS = LLAVES_PERSONA + ["p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]


def normalizar(nombre: str) -> str:
    """'aÑo' -> 'anio'; quita tildes y pasa a minúscula."""
    nombre = nombre.strip().lower().replace("ñ", "ni")
    return unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()


def extraer(datos: Path, codigo: str, modulo: str, archivo: str) -> Path:
    """Devuelve la ruta al .dta; si no existe, lo saca del zip del INEI."""
    destino = datos / archivo
    if destino.exists():
        return destino
    zip_path = datos / f"{codigo}-Modulo{modulo}.zip"
    if not zip_path.exists():
        sys.exit(
            f"Falta {zip_path}. Bájalo de "
            f"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"
        )
    with zipfile.ZipFile(zip_path) as z:
        miembro = next(n for n in z.namelist() if n.lower().endswith("/" + archivo))
        destino.write_bytes(z.read(miembro))
    return destino


def leer(ruta: Path, columnas: list[str]) -> pd.DataFrame:
    # 1 · Leer: sin categorías, para quedarnos con los códigos numéricos del INEI
    df = pd.read_stata(ruta, convert_categoricals=False)
    # 2 · Normalizar nombres
    df.columns = [normalizar(c) for c in df.columns]
    df = df[columnas].copy()
    # Llaves como texto, sin perder ceros a la izquierda
    for c in TEXTO:
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    if "ubigeo" in df:
        df["ubigeo"] = df["ubigeo"].str.zfill(6)
    return df


def ponderada(serie: pd.Series, peso: pd.Series) -> float:
    return float((serie * peso).sum() / peso.sum() * 100)


def indicadores(base: pd.DataFrame, sumaria: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Tabla larga de indicadores ponderados para el informe: nacional, área, departamento (método de hogares)
    y sexo y grupo de edad (método de personas, facpob07)."""
    filas = []
    hog = sumaria.assign(peso=sumaria.factor07 * sumaria.mieperho, pobre=(sumaria.pobreza <= 2).astype(int),
                         extremo=(sumaria.pobreza == 1).astype(int),
                         area=(sumaria.estrato <= 5).map({True: "Urbana", False: "Rural"}),
                         departamento=sumaria.ubigeo.str[:2])
    for grupo, col in [("Nacional", None), ("Área", "area"), ("Departamento", "departamento")]:
        g = hog.groupby(col) if col else [("Perú", hog)]
        for k, d in g:
            filas.append({"anio": anio, "dimension": grupo, "categoria": k, "metodo": "hogares: factor07 × mieperho",
                          "pobreza_pct": ponderada(d.pobre, d.peso), "pobreza_extrema_pct": ponderada(d.extremo, d.peso),
                          "n_muestra": len(d), "poblacion_expandida": float(d.peso.sum())})
    for grupo, col in [("Sexo", "sexo"), ("Grupo de edad", "grupo_edad")]:
        for k, d in base.groupby(col):
            filas.append({"anio": anio, "dimension": grupo, "categoria": k, "metodo": "personas: facpob07",
                          "pobreza_pct": ponderada(d.pobre, d.facpob07),
                          "pobreza_extrema_pct": ponderada(d.pobre_extremo, d.facpob07),
                          "n_muestra": len(d), "poblacion_expandida": float(d.facpob07.sum())})
    return pd.DataFrame(filas).round({"pobreza_pct": 2, "pobreza_extrema_pct": 2, "poblacion_expandida": 0})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--datos", type=Path, default=Path("datos"))
    ap.add_argument("--salidas", type=Path, default=Path("salidas"))
    a = ap.parse_args()
    if a.anio not in CODIGOS:
        sys.exit(f"Año {a.anio} sin código INEI registrado; agrégalo en CODIGOS.")
    codigo = CODIGOS[a.anio]

    sumaria = leer(extraer(a.datos, codigo, "34", f"sumaria-{a.anio}.dta"), COLS_SUMARIA)
    miembros = leer(extraer(a.datos, codigo, "02", f"enaho01-{a.anio}-200.dta"), COLS_MIEMBROS)
    filas_miembros = len(miembros)

    # 3 · Filtrar residentes habituales (definición del INEI)
    residente = ((miembros.p204 == 1) & (miembros.p205 == 2)) | (
        (miembros.p204 == 2) & (miembros.p206 == 1)
    )
    personas = miembros[residente].copy()

    # 4 · Unir: cada persona con un único hogar
    assert not sumaria.duplicated(LLAVES_HOGAR).any(), "Hogares repetidos en la sumaria"
    assert not personas.duplicated(LLAVES_PERSONA).any(), "Personas repetidas en miembros"
    base = personas.merge(sumaria, on=LLAVES_HOGAR, how="inner", validate="m:1")
    assert len(base) == len(personas), "La unión perdió o duplicó filas"

    # 5 · Construir variables
    base["anio"] = a.anio
    base["departamento"] = base.ubigeo.str[:2]
    base["urbano"] = (base.estrato <= 5).astype(int)
    base["area"] = base.urbano.map({1: "Urbana", 0: "Rural"})
    base["pobre"] = (base.pobreza <= 2).astype(int)
    base["pobre_extremo"] = (base.pobreza == 1).astype(int)
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(
        base.edad, [-1, 13, 17, 29, 44, 59, 200],
        labels=["0-13", "14-17", "18-29", "30-44", "45-59", "60+"],
    ).astype(str)

    # 6 · Validar contra el INEI
    peso_hogar = sumaria.factor07 * sumaria.mieperho
    pob_sum = ponderada((sumaria.pobreza <= 2).astype(int), peso_hogar)
    ext_sum = ponderada((sumaria.pobreza == 1).astype(int), peso_hogar)
    pob_per = ponderada(base.pobre, base.facpob07)
    ext_per = ponderada(base.pobre_extremo, base.facpob07)
    urb = (sumaria.estrato <= 5)
    pob_urb = ponderada((sumaria.pobreza[urb] <= 2).astype(int), peso_hogar[urb])
    pob_rur = ponderada((sumaria.pobreza[~urb] <= 2).astype(int), peso_hogar[~urb])
    pob_of, ext_of, n_of = OFICIAL[a.anio]
    urb_of, rur_of = OFICIAL_AREA[a.anio]
    chequeos = {
        "Llaves de hogar únicas en la sumaria": not sumaria.duplicated(LLAVES_HOGAR).any(),
        "Llaves de persona únicas": not base.duplicated(LLAVES_PERSONA).any(),
        "La unión no perdió ni duplicó filas": len(base) == len(personas),
        f"Residentes habituales = {n_of:,}": len(base) == n_of,
        f"Pobreza (sumaria) a menos de 0.1 pts de {pob_of} %": abs(pob_sum - pob_of) < 0.1,
        f"Pobreza extrema (sumaria) a menos de 0.1 pts de {ext_of} %": abs(ext_sum - ext_of) < 0.1,
        f"Pobreza urbana a menos de 0.2 pts de {urb_of} %": abs(pob_urb - urb_of) < 0.2,
        f"Pobreza rural a menos de 0.2 pts de {rur_of} %": abs(pob_rur - rur_of) < 0.2,
        "Suma de facpob07 entre 33 y 35 millones (población del Perú)": 33e6 < base.facpob07.sum() < 35e6,
        "25 departamentos con dato": base.departamento.nunique() == 25,
    }
    ok = all(chequeos.values())
    lineas = [
        f"Validación ENAHO {a.anio} (código INEI {codigo})",
        "",
        f"Hogares en la sumaria:            {len(sumaria):>9,}",
        f"Filas en el módulo 200:           {filas_miembros:>9,}",
        f"Residentes habituales:            {len(base):>9,}",
        f"Población expandida (facpob07):   {base.facpob07.sum():>13,.0f}",
        "",
        f"Pobreza, sumaria (factor07 × mieperho):   {pob_sum:6.2f} %   (INEI: {pob_of} %)",
        f"Pobreza extrema, sumaria:                 {ext_sum:6.2f} %   (INEI: {ext_of} %)",
        f"Pobreza urbana, sumaria:                  {pob_urb:6.2f} %   (referencia: {urb_of} %)",
        f"Pobreza rural, sumaria:                   {pob_rur:6.2f} %   (referencia: {rur_of} %)",
        f"Pobreza, base de personas (facpob07):     {pob_per:6.2f} %",
        f"Pobreza extrema, base de personas:        {ext_per:6.2f} %",
        "",
        *[f"[{'OK' if v else 'FALLA'}] {k}" for k, v in chequeos.items()],
        "",
        f"Resultado: {'VALIDADA' if ok else 'NO VALIDADA, no uses la base'}",
    ]

    # 7 · Guardar
    a.salidas.mkdir(parents=True, exist_ok=True)
    salida = a.salidas / f"personas_{a.anio}.parquet"
    base.to_parquet(salida, index=False)
    (a.salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    indicadores(base, sumaria, a.anio).to_csv(a.salidas / "indicadores.csv", index=False)
    print("\n".join(lineas))
    if not ok:
        salida.unlink()   # una base que no valida no debe quedar disponible para las otras skills
        sys.exit("\nERROR: la validación falló; se borró la base. Revisa los chequeos marcados FALLA.")
    print(f"\nBase guardada en {salida} ({len(base):,} filas, {base.shape[1]} columnas)")
    print(f"Indicadores en {a.salidas / 'indicadores.csv'}")


if __name__ == "__main__":
    main()
