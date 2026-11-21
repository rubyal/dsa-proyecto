
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from .features import agregar_variables_relativas


@lru_cache(maxsize=1)
def cargar_modelo():
    """Carga el modelo entrenado y sus umbrales."""
    ruta = (
        Path(__file__).resolve().parent
        / "artifacts"
        / "ridge_classifier_e3.joblib"
    )
    return joblib.load(ruta)


def predecir(datos: pd.DataFrame) -> pd.DataFrame:
    """Predice la demanda usando las variables históricas preparadas."""

    artefacto = cargar_modelo()
    variables = artefacto["variables"]

    # Calcular las tres variables adicionales.
    entrada = agregar_variables_relativas(
        datos,
        artefacto["umbrales"]
    )

    faltantes = [
        columna for columna in variables
        if columna not in entrada.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan variables: {faltantes}")

    resultado = datos.copy()
    resultado["nivel_demanda_predicho"] = (
        artefacto["modelo"].predict(entrada[variables])
    )

    return resultado
