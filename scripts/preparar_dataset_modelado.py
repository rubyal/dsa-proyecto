

"""Reproduce el dataset semanal de modelado NYC311 — DSAP-40."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]

ENTRADA = RAIZ / "data/raw/nyc311_diario_borough_tipo.parquet"

# Salida de prueba por defecto: no sobrescribe el dataset oficial.
SALIDA_PREDETERMINADA = (
    RAIZ / "data/processed/dataset_modelado_prueba.parquet"
)

BOROUGHS = [
    "BRONX",
    "BROOKLYN",
    "MANHATTAN",
    "QUEENS",
    "STATEN ISLAND",
]


def main(salida):
    salida = Path(salida)

    # 1. Cargar datos originales
    df = pd.read_parquet(ENTRADA)
    df["dia"] = pd.to_datetime(df["dia"])

    df = df[df["borough"].isin(BOROUGHS)].copy()

    # 2. Agregar solicitudes por semana y borough
    df["semana"] = df["dia"].dt.to_period("W-SUN").dt.start_time

    semanal = (
        df.groupby(["borough", "semana"], as_index=False)["n"]
        .sum()
        .rename(columns={"n": "total_solicitudes"})
        .sort_values(["borough", "semana"])
        .reset_index(drop=True)
    )

    semanal = semanal[
        semanal["semana"].between("2022-01-03", "2025-12-22")
    ].copy()

    assert len(semanal) == 1040, (
        "Se esperaban 1040 observaciones semanales"
    )

    assert semanal.groupby("borough").size().eq(208).all(), (
        "Se esperaban 208 semanas por borough"
    )

    # 3. Construir variables predictoras
    datos = semanal.sort_values(
        ["borough", "semana"]
    ).reset_index(drop=True)

    # Variables de calendario
    datos["mes"] = datos["semana"].dt.month
    datos["semana_anio"] = (
        datos["semana"].dt.isocalendar().week.astype(int)
    )

    # Rezagos por borough
    grupo = datos.groupby("borough")["total_solicitudes"]

    for rezago in [1, 2, 4, 52]:
        datos[f"lag_{rezago}"] = grupo.shift(rezago)

    # Medias móviles históricas
    for ventana in [4, 12, 52]:
        datos[f"media_movil_{ventana}"] = grupo.transform(
            lambda x: x.shift(1).rolling(
                window=ventana,
                min_periods=ventana
            ).mean()
        )

    # Desviación estándar de las 4 semanas anteriores
    datos["std_movil_4"] = grupo.transform(
        lambda x: x.shift(1).rolling(
            window=4,
            min_periods=4
        ).std()
    )

    # 4. Conservar semanas con historial suficiente
    datos = datos.dropna(
        subset=["media_movil_52"]
    ).copy()

    # 5. Calcular demanda relativa
    datos["demanda_relativa"] = (
        datos["total_solicitudes"] /
        datos["media_movil_52"]
    )

    # 6. Calcular umbrales únicamente con 2023–2024
    entrenamiento = datos[
        datos["semana"].dt.year.isin([2023, 2024])
    ]

    umbrales = (
        entrenamiento.groupby("borough")["demanda_relativa"]
        .quantile([0.33, 0.67])
        .unstack()
        .rename(columns={0.33: "P33", 0.67: "P67"})
    )

    datos = datos.merge(
        umbrales,
        on="borough",
        how="left"
    )

    # 7. Construir variable objetivo
    datos["nivel_demanda"] = np.select(
        [
            datos["demanda_relativa"] < datos["P33"],
            datos["demanda_relativa"] <= datos["P67"]
        ],
        ["Baja", "Media"],
        default="Alta"
    )

    # 8. Validar el dataset generado
    assert datos.shape == (780, 17), (
        f"Dimensiones inesperadas: {datos.shape}"
    )

    assert not datos.isna().any().any(), (
        "El dataset contiene valores nulos"
    )

    assert datos.groupby("borough").size().eq(156).all(), (
        "Se esperaban 156 observaciones por borough"
    )

    # 9. Guardar el resultado en la ruta seleccionada
    salida.parent.mkdir(parents=True, exist_ok=True)

    datos.to_parquet(
        salida,
        index=False
    )

    # 10. Mostrar resultados
    print("\nDataset reconstruido correctamente")
    print("Archivo:", salida.resolve())
    print("Dimensiones:", datos.shape)
    print(
        "Período:",
        datos["semana"].min(),
        "a",
        datos["semana"].max()
    )

    print("\nObservaciones por borough:")
    print(datos.groupby("borough").size())

    print("\nDistribución de clases:")
    print(datos["nivel_demanda"].value_counts())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Reproduce el dataset semanal de modelado NYC311"
        )
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=SALIDA_PREDETERMINADA,
        help="Ruta donde se guardará el dataset reconstruido"
    )

    args = parser.parse_args()

    main(args.salida)
