
import pandas as pd


def preparar_proxima_semana(historial: pd.DataFrame, borough: str) -> pd.DataFrame:
    """Prepara las 11 características para la semana siguiente."""

    datos = historial[
        historial["borough"] == borough
    ].copy()

    datos["semana"] = pd.to_datetime(datos["semana"])
    datos = datos.sort_values("semana")

    if len(datos) < 52:
        raise ValueError(
            "Se necesitan al menos 52 semanas de historial"
        )

    # Próxima semana respecto al último registro disponible.
    proxima_semana = datos["semana"].max() + pd.Timedelta(weeks=1)

    # Solicitudes históricas ordenadas por semana.
    serie = datos["total_solicitudes"].astype(float)

    entrada = pd.DataFrame([{
        "borough": borough,
        "mes": proxima_semana.month,
        "semana_anio": int(proxima_semana.isocalendar().week),
        "lag_1": serie.iloc[-1],
        "lag_2": serie.iloc[-2],
        "lag_4": serie.iloc[-4],
        "lag_52": serie.iloc[-52],
        "media_movil_4": serie.iloc[-4:].mean(),
        "media_movil_12": serie.iloc[-12:].mean(),
        "media_movil_52": serie.iloc[-52:].mean(),
        "std_movil_4": serie.iloc[-4:].std(),
    }])

    return entrada
