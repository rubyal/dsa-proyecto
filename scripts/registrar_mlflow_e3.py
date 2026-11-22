

from pathlib import Path

import mlflow
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
REPORTES = RAIZ / "reports" / "e3"

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("DSAP_E3_Modelos_NYC311")

ARCHIVOS = [
    ("Validacion_2024", "comparacion_modelos_2024.csv"),
    ("Prueba_2025", "evaluacion_final_2025.csv"),
]

METRICAS = {
    "Accuracy": "accuracy",
    "F1-macro": "f1_macro",
    "Precision Media": "precision_media",
    "Recall Baja": "recall_baja",
    "Recall Media": "recall_media",
    "Recall Alta": "recall_alta",
    "Alta->Baja": "errores_alta_a_baja",
}

for periodo, archivo in ARCHIVOS:
    ruta = REPORTES / archivo
    datos = pd.read_csv(ruta)

    for _, fila in datos.iterrows():
        nombre = str(fila["Modelo"])

        with mlflow.start_run(run_name=f"{periodo}_{nombre}"):
            mlflow.set_tags({
                "proyecto": "DSAP_E3",
                "periodo_evaluacion": periodo,
                "origen": "Resultados previamente calculados",
                "reentrenamiento": "No",
            })

            mlflow.log_param("modelo", nombre)
            mlflow.log_param("n_observaciones", int(fila["N"]))

            if "Etapa" in datos.columns:
                mlflow.log_param("etapa", str(fila["Etapa"]))

            for columna, clave in METRICAS.items():
                valor = fila[columna]
                if pd.notna(valor):
                    mlflow.log_metric(clave, float(valor))

            mlflow.log_artifact(str(ruta))

            if periodo == "Prueba_2025" and nombre == "Ridge_variables_relativas":
                modelo = RAIZ / "models" / "ridge_classifier_e3.joblib"
                if modelo.exists():
                    mlflow.log_artifact(str(modelo), artifact_path="modelo")

            print(f"Registrado: {periodo} / {nombre}")

print("\nRegistro de resultados E3 completado.")
