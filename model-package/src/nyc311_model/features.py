
import numpy as np
import pandas as pd


def agregar_variables_relativas(datos, umbrales):
    """Calcula las tres variables relativas del RidgeClassifier."""

    resultado = datos.copy()

    # Obtener los umbrales correspondientes a cada borough.
    p33 = resultado["borough"].map(umbrales["P33"])
    p67 = resultado["borough"].map(umbrales["P67"])

    if p33.isna().any() or p67.isna().any():
        raise ValueError("Hay boroughs sin umbrales definidos")

    lag1 = resultado["lag_1"].to_numpy(dtype=float)
    media52 = resultado["media_movil_52"].to_numpy(dtype=float)

    if not np.isfinite(lag1).all():
        raise ValueError("lag_1 contiene valores inválidos")

    if not np.isfinite(media52).all():
        raise ValueError("media_movil_52 contiene valores inválidos")

    if np.any(media52 <= 0):
        raise ValueError(
            "La media móvil de 52 semanas debe ser positiva"
        )

    demanda_lag1 = lag1 / media52

    resultado["demanda_relativa_lag1"] = demanda_lag1
    resultado["distancia_p33_lag1"] = (
        demanda_lag1 - p33.to_numpy(dtype=float)
    )
    resultado["distancia_p67_lag1"] = (
        demanda_lag1 - p67.to_numpy(dtype=float)
    )

    return resultado
