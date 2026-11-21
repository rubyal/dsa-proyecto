
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# 1. CARGAR DATOS HISTÓRICOS
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

ruta = RAIZ / "data/raw/nyc311_diario_borough_tipo.parquet"

df = pd.read_parquet(ruta)
df["dia"] = pd.to_datetime(df["dia"])

boroughs = [
    "BRONX",
    "BROOKLYN",
    "MANHATTAN",
    "QUEENS",
    "STATEN ISLAND"
]

# Solo utilizamos 2022 y 2023 para el análisis exploratorio
df = df[
    df["borough"].isin(boroughs)
    & df["dia"].dt.year.isin([2022, 2023])
].copy()

df["anio"] = df["dia"].dt.year
df["mes"] = df["dia"].dt.month

print("\nDATOS DE ESTACIONALIDAD")
print("Periodo:", df["dia"].min(), "-", df["dia"].max())
print("Filas:", len(df))


# ============================================================
# 2. AGRUPAR CATEGORÍAS PARA ANÁLISIS
# ============================================================

tipos = df["complaint_type"].str.upper()

# Estas agrupaciones son solo para el análisis histórico.
# No representan nuevas clases objetivo del modelo.

df["grupo"] = np.select(
    [
        tipos.str.contains("NOISE", regex=False, na=False),
        tipos.str.contains(
            "HEAT|HOT WATER",
            regex=True,
            na=False
        )
    ],
    [
        "Ruido",
        "Calefaccion"
    ],
    default="Otros"
)

print("\nCATEGORÍAS ORIGINALES IDENTIFICADAS")

for grupo in ["Ruido", "Calefaccion"]:
    categorias = sorted(
        df.loc[
            df["grupo"] == grupo,
            "complaint_type"
        ].unique()
    )

    print(f"\n{grupo}:")
    for categoria in categorias:
        print(" -", categoria)


# ============================================================
# 3. SOLICITUDES MENSUALES
# ============================================================

mensual = (
    df.groupby(["anio", "mes", "grupo"])["n"]
    .sum()
    .unstack(fill_value=0)
)

for columna in ["Ruido", "Calefaccion", "Otros"]:
    if columna not in mensual.columns:
        mensual[columna] = 0

mensual["Total"] = mensual[
    ["Ruido", "Calefaccion", "Otros"]
].sum(axis=1)

mensual["Porcentaje_Ruido"] = (
    mensual["Ruido"] / mensual["Total"] * 100
)

mensual["Porcentaje_Calefaccion"] = (
    mensual["Calefaccion"] / mensual["Total"] * 100
)

print("\n" + "=" * 65)
print("SOLICITUDES MENSUALES - 2022 Y 2023")
print("=" * 65)

print(
    mensual[
        [
            "Ruido",
            "Calefaccion",
            "Total",
            "Porcentaje_Ruido",
            "Porcentaje_Calefaccion"
        ]
    ].round(2).to_string()
)


# ============================================================
# 4. MESES CON MAYOR PARTICIPACIÓN POR CATEGORÍA
# ============================================================

for grupo, columna in [
    ("Ruido", "Porcentaje_Ruido"),
    ("Calefaccion", "Porcentaje_Calefaccion")
]:

    print(f"\nMESES CON MAYOR PARTICIPACIÓN DE {grupo.upper()}")

    for anio in [2022, 2023]:

        datos_anio = mensual.loc[anio]

        principales = (
            datos_anio[columna]
            .sort_values(ascending=False)
            .head(3)
        )

        print(f"\nAño {anio}:")
        print(principales.round(2).to_string())


# ============================================================
# 5. FINALIZACIÓN
# ============================================================

print("\n" + "=" * 65)
print("ANÁLISIS EXPLORATORIO DE ESTACIONALIDAD COMPLETADO")
print("=" * 65)

print("Años analizados: 2022 y 2023")
print("No se modificaron los datos originales.")
print("No se crearon archivos CSV.")
print("No se entrenaron modelos.")
