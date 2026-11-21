
from pathlib import Path
import pandas as pd


RUTA_DATOS = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "dataset_modelado_semanal.parquet"
)


def cargar_historial():
    """Carga el historial semanal para las predicciones."""

    if not RUTA_DATOS.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset: {RUTA_DATOS}"
        )

    datos = pd.read_parquet(RUTA_DATOS)

    columnas = ["borough", "semana", "total_solicitudes"]

    return datos[columnas].copy()
