
from fastapi import FastAPI
import pandas as pd
from fastapi import HTTPException
from nyc311_model import predecir
from api.app.schemas.predict import PrediccionEntrada, PrediccionSalida
from api.app.data import cargar_historial
from api.app.features import preparar_proxima_semana
from nyc311_model import cargar_modelo

app = FastAPI(
    title="NYC311 - API de Predicción de Demanda",
    description="API para predecir la demanda semanal de solicitudes NYC311 por borough.",
    version="0.1.0"
)


@app.get("/")
def inicio():
    return {
        "mensaje": "Bienvenido a la API de prediccion NYC311"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "servicio": "NYC311 API"
    }

@app.post("/predict", response_model=PrediccionSalida)
def predict(datos: PrediccionEntrada):
    try:
        entrada = pd.DataFrame([datos.model_dump()])
        resultado = predecir(entrada)

        return PrediccionSalida(
            borough=datos.borough,
            nivel_demanda=resultado.iloc[0]["nivel_demanda_predicho"]
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error


@app.get("/predict/next-week/{borough}")
def predict_next_week(borough: str):
    """Predice la semana posterior al último registro histórico."""

    borough = borough.strip().upper()

    # Verificar que el borough exista en el modelo.
    artefacto = cargar_modelo()
    if borough not in artefacto["umbrales"].index:
        raise HTTPException(
            status_code=422,
            detail=f"Borough no válido: {borough}"
        )

    try:
        # Cargar el historial disponible.
        historial = cargar_historial()

        # Preparar las 11 características originales.
        entrada = preparar_proxima_semana(historial, borough)

        # Predecir utilizando el paquete .whl.
        resultado = predecir(entrada)

        # Identificar la semana pronosticada.
        ultima_semana = pd.to_datetime(
            historial.loc[
                historial["borough"] == borough, "semana"
            ]
        ).max()

        semana_predicha = ultima_semana + pd.Timedelta(weeks=1)

        return {
            "borough": borough,
            "semana": semana_predicha.strftime("%Y-%m-%d"),
            "nivel_demanda": resultado.iloc[0][
                "nivel_demanda_predicho"
            ]
        }

    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error)
        ) from error
