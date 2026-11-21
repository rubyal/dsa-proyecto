
from fastapi.testclient import TestClient

from api.app.main import app


client = TestClient(app)


def test_health():
    respuesta = client.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"


def test_predict():
    datos = {
        "borough": "BRONX",
        "mes": 1,
        "semana_anio": 2,
        "lag_1": 36794.0,
        "lag_2": 19206.0,
        "lag_4": 16679.0,
        "lag_52": 13151.0,
        "media_movil_4": 24053.25,
        "media_movil_12": 18667.5,
        "media_movil_52": 14471.0,
        "std_movil_4": 8953.057703935567,
    }

    respuesta = client.post("/predict", json=datos)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "borough": "BRONX",
        "nivel_demanda": "Alta",
    }


def test_predict_datos_invalidos():
    respuesta = client.post(
        "/predict",
        json={"borough": "BRONX", "mes": 15}
    )

    assert respuesta.status_code == 422

def test_predict_next_week():
    respuesta = client.get("/predict/next-week/QUEENS")

    assert respuesta.status_code == 200

    resultado = respuesta.json()

    assert resultado["borough"] == "QUEENS"
    assert resultado["semana"] == "2025-12-29"
    assert resultado["nivel_demanda"] in [
        "Baja", "Media", "Alta"
    ]