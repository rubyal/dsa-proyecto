import os
import mlflow


def configurar_mlflow():
    """
    Configura MLflow para registrar experimentos
    en el servidor remoto de AWS EC2.
    """

    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000"
    )

    nombre_experimento = os.getenv(
        "MLFLOW_EXPERIMENT_NAME",
        "DSAP34_NYC311_Clasificacion_Demanda"
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(nombre_experimento)

    print(f"Servidor MLflow: {tracking_uri}")
    print(f"Experimento: {nombre_experimento}")

    return tracking_uri


if __name__ == "__main__":
    configurar_mlflow()