
from pathlib import Path
import pandas as pd

# Ruta del proyecto
RAIZ = Path(__file__).resolve().parents[1]
RUTA_DATOS = RAIZ / "data/processed/dataset_modelado_semanal.parquet"

# Cargar datos
df = pd.read_parquet(RUTA_DATOS)
df["semana"] = pd.to_datetime(df["semana"])

# Separación temporal
train_2023 = df[df["semana"].dt.year == 2023].copy()
val_2024 = df[df["semana"].dt.year == 2024].copy()

# Calcular umbrales SOLO con entrenamiento (2023)
umbrales = (
    train_2023.groupby("borough")["demanda_relativa"]
    .quantile([0.33, 0.67])
    .unstack()
)

umbrales.columns = ["P33", "P67"]

print("\nUmbrales calculados únicamente con 2023:")
print(umbrales)

def asignar_clases(datos, limites):
    resultado = datos.drop(
        columns=["P33", "P67", "nivel_demanda"],
        errors="ignore"
    ).merge(limites, on="borough", how="left", validate="many_to_one")

    if resultado[["P33", "P67"]].isna().any().any():
        raise ValueError("Faltan umbrales para algún borough")

    resultado["nivel_demanda"] = "Media"
    resultado.loc[
        resultado["demanda_relativa"] < resultado["P33"],
        "nivel_demanda"
    ] = "Baja"
    resultado.loc[
        resultado["demanda_relativa"] > resultado["P67"],
        "nivel_demanda"
    ] = "Alta"

    return resultado

# Aplicar los mismos umbrales a 2023 y 2024
train_corregido = asignar_clases(train_2023, umbrales)
val_corregido = asignar_clases(val_2024, umbrales)

print("\nDistribución de clases en entrenamiento 2023:")
print(train_corregido["nivel_demanda"].value_counts())

print("\nDistribución de clases en validación 2024:")
print(val_corregido["nivel_demanda"].value_counts())

# Comparar etiquetas de 2024 con las originales
comparacion = val_2024[["borough", "semana", "nivel_demanda"]].merge(
    val_corregido[["borough", "semana", "nivel_demanda"]],
    on=["borough", "semana"],
    suffixes=("_original", "_corregida"),
    validate="one_to_one"
)

cambios = (
    comparacion["nivel_demanda_original"]
    != comparacion["nivel_demanda_corregida"]
).sum()

print(f"\nEtiquetas modificadas en validación 2024: {cambios} de {len(comparacion)}")

