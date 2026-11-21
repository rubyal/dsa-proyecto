
from pathlib import Path

import pandas as pd

# ============================================================
# 1. CARGAR DATOS
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

ruta = RAIZ / "data/processed/dataset_modelado_semanal.parquet"

df = pd.read_parquet(ruta)
df["semana"] = pd.to_datetime(df["semana"])

# ============================================================
# 2. CALCULAR UMBRALES SIN FUGA TEMPORAL
# ============================================================

# Para la evaluación de 2025, los umbrales se
# calculan exclusivamente con 2023 y 2024.

train = df[df["semana"].dt.year.isin([2023, 2024])]

umbrales = (
    train.groupby("borough")["demanda_relativa"]
    .quantile([0.33, 0.67])
    .unstack()
)

umbrales.columns = ["P33", "P67"]

# ============================================================
# 3. OBTENER LA ÚLTIMA SEMANA HISTÓRICA
# ============================================================

# Se utiliza la última observación de 2025
# de cada borough, únicamente como ejemplo.
# No constituye una predicción de 2026.

historico = df[df["semana"].dt.year == 2025]

ultimas = (
    historico.sort_values("semana")
    .groupby("borough")
    .tail(1)
    .copy()
)

ultimas = ultimas.merge(
    umbrales,
    on="borough",
    how="left",
    suffixes=("_anterior", "")
)

# ============================================================
# 4. CALCULAR RANGOS DE SOLICITUDES
# ============================================================

# El promedio de 52 semanas está calculado con
# semanas anteriores a la observación seleccionada.

ultimas["limite_baja"] = (
    ultimas["media_movil_52"] * ultimas["P33"]
)

ultimas["limite_alta"] = (
    ultimas["media_movil_52"] * ultimas["P67"]
)

# ============================================================
# 5. MOSTRAR RESULTADOS
# ============================================================

print("\nRANGOS HISTÓRICOS POR BOROUGH - E3")
print("=" * 65)

for _, fila in ultimas.sort_values("borough").iterrows():

    print(f"\nBorough: {fila['borough']}")
    print(f"Semana de referencia: {fila['semana'].date()}")

    print(
        f"Promedio histórico: "
        f"{fila['media_movil_52']:,.0f} solicitudes"
    )

    print(
        f"Baja: menos de {fila['limite_baja']:,.0f}"
    )

    print(
        f"Media: entre {fila['limite_baja']:,.0f} "
        f"y {fila['limite_alta']:,.0f}"
    )

    print(
        f"Alta: más de {fila['limite_alta']:,.0f}"
    )

print("\n" + "=" * 65)
print("CÁLCULO COMPLETADO")
print("No se generaron archivos CSV.")
print("No se modificaron los datos originales.")
print("Estos rangos describen límites de clasificación.")
print("No representan intervalos de predicción.")
