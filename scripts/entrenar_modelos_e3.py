
from pathlib import Path
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import RidgeClassifier, LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier
)

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

RAIZ = Path(__file__).resolve().parents[1]

RUTA_DATOS = (
    RAIZ / "data/processed/dataset_modelado_semanal.parquet"
)

CARPETA_RESULTADOS = RAIZ / "reports/e3"
CARPETA_MODELOS = RAIZ / "models"

RUTA_COMPARACION = (
    CARPETA_RESULTADOS / "comparacion_modelos_2024.csv"
)

RUTA_EVALUACION = (
    CARPETA_RESULTADOS / "evaluacion_final_2025.csv"
)

RUTA_BOROUGHS = (
    CARPETA_RESULTADOS / "metricas_borough_2025.csv"
)

RUTA_MODELO = (
    CARPETA_MODELOS / "ridge_classifier_e3.joblib"
)

CLASES = ["Baja", "Media", "Alta"]

VARIABLES_ORIGINALES = [
    "borough",
    "mes",
    "semana_anio",
    "lag_1",
    "lag_2",
    "lag_4",
    "lag_52",
    "media_movil_4",
    "media_movil_12",
    "media_movil_52",
    "std_movil_4"
]

VARIABLES_RELATIVAS = [
    "demanda_relativa_lag1",
    "distancia_p33_lag1",
    "distancia_p67_lag1"
]

VARIABLES_FINALES = (
    VARIABLES_ORIGINALES + VARIABLES_RELATIVAS
)


# ============================================================
# 2. FUNCIONES REUTILIZABLES
# ============================================================

def calcular_umbrales(datos):

    umbrales = (
        datos.groupby("borough")["demanda_relativa"]
        .quantile([0.33, 0.67])
        .unstack()
    )

    umbrales.columns = ["P33", "P67"]

    if umbrales.isna().any().any():
        raise ValueError("No se pudieron calcular los umbrales")

    return umbrales


def obtener_limites(boroughs, umbrales):

    boroughs = pd.Series(
        boroughs
    ).reset_index(drop=True)

    p33 = boroughs.map(
        umbrales["P33"]
    ).to_numpy(dtype=float)

    p67 = boroughs.map(
        umbrales["P67"]
    ).to_numpy(dtype=float)

    if not np.isfinite(p33).all():
        raise ValueError("P33 contiene valores inválidos")

    if not np.isfinite(p67).all():
        raise ValueError("P67 contiene valores inválidos")

    return p33, p67


def convertir_clases(boroughs, demandas, umbrales):

    p33, p67 = obtener_limites(
        boroughs,
        umbrales
    )

    demandas = np.asarray(
        demandas,
        dtype=float
    )

    if not np.isfinite(demandas).all():
        raise ValueError("Demandas relativas inválidas")

    return np.where(
        demandas < p33,
        "Baja",
        np.where(
            demandas > p67,
            "Alta",
            "Media"
        )
    )


def agregar_variables_relativas(datos, umbrales):

    resultado = datos.copy()

    p33, p67 = obtener_limites(
        resultado["borough"],
        umbrales
    )

    lag1 = resultado[
        "lag_1"
    ].to_numpy(dtype=float)

    media52 = resultado[
        "media_movil_52"
    ].to_numpy(dtype=float)

    if not np.isfinite(lag1).all():
        raise ValueError("lag_1 contiene valores inválidos")

    if not np.isfinite(media52).all():
        raise ValueError(
            "media_movil_52 contiene valores inválidos"
        )

    if np.any(media52 <= 0):
        raise ValueError(
            "La media móvil de 52 semanas debe ser positiva"
        )

    demanda_lag1 = lag1 / media52

    resultado["demanda_relativa_lag1"] = (
        demanda_lag1
    )

    resultado["distancia_p33_lag1"] = (
        demanda_lag1 - p33
    )

    resultado["distancia_p67_lag1"] = (
        demanda_lag1 - p67
    )

    return resultado


def crear_pipeline(estimador, variables):

    numericas = [
        variable
        for variable in variables
        if variable != "borough"
    ]

    preprocesador = ColumnTransformer([
        (
            "borough",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            ),
            ["borough"]
        ),
        (
            "numericas",
            StandardScaler(),
            numericas
        )
    ])

    return Pipeline([
        ("preprocesamiento", preprocesador),
        ("modelo", clone(estimador))
    ])


def calcular_metricas(nombre, reales, predicciones):

    matriz = confusion_matrix(
        reales,
        predicciones,
        labels=CLASES
    )

    return {
        "Modelo": nombre,
        "N": len(reales),
        "Accuracy": accuracy_score(
            reales,
            predicciones
        ),
        "F1-macro": f1_score(
            reales,
            predicciones,
            labels=CLASES,
            average="macro",
            zero_division=0
        ),
        "Precision Media": precision_score(
            reales,
            predicciones,
            labels=["Media"],
            average="macro",
            zero_division=0
        ),
        "Recall Baja": recall_score(
            reales,
            predicciones,
            labels=["Baja"],
            average="macro",
            zero_division=0
        ),
        "Recall Media": recall_score(
            reales,
            predicciones,
            labels=["Media"],
            average="macro",
            zero_division=0
        ),
        "Recall Alta": recall_score(
            reales,
            predicciones,
            labels=["Alta"],
            average="macro",
            zero_division=0
        ),
        "Alta->Baja": int(matriz[2, 0])
    }


def entrenar_y_evaluar(
    nombre,
    estimador,
    variables,
    entrenamiento,
    validacion,
    y_entrenamiento,
    y_validacion
):

    pipeline = crear_pipeline(
        estimador,
        variables
    )

    pipeline.fit(
        entrenamiento[variables],
        y_entrenamiento
    )

    predicciones = pipeline.predict(
        validacion[variables]
    )

    metricas = calcular_metricas(
        nombre,
        y_validacion,
        predicciones
    )

    return pipeline, predicciones, metricas


def mostrar_detalle(nombre, reales, predicciones):

    print(f"\nREPORTE: {nombre}")

    print(
        classification_report(
            reales,
            predicciones,
            labels=CLASES,
            zero_division=0
        )
    )

    matriz = confusion_matrix(
        reales,
        predicciones,
        labels=CLASES
    )

    print("\nMatriz de confusión:")

    print(
        pd.DataFrame(
            matriz,
            index=[
                f"Real {clase}"
                for clase in CLASES
            ],
            columns=[
                f"Pred {clase}"
                for clase in CLASES
            ]
        ).to_string()
    )


# ============================================================
# 3. CARGAR Y VALIDAR DATASET
# ============================================================

df = pd.read_parquet(RUTA_DATOS)

df["semana"] = pd.to_datetime(
    df["semana"]
)

df = df.sort_values(
    ["borough", "semana"]
).reset_index(drop=True)

if df.duplicated(["borough", "semana"]).any():
    raise ValueError(
        "Hay semanas duplicadas por borough"
    )

train_2023 = df[
    df["semana"].dt.year == 2023
].copy()

val_2024 = df[
    df["semana"].dt.year == 2024
].copy()

test_2025 = df[
    df["semana"].dt.year == 2025
].copy()

if any(
    datos.empty
    for datos in [
        train_2023,
        val_2024,
        test_2025
    ]
):
    raise ValueError(
        "Faltan datos de alguno de los períodos"
    )

print("\n" + "=" * 75)
print("ENTRENAMIENTO DE MODELOS - ENTREGA 3")
print("=" * 75)

print("Dataset:", df.shape)

print(
    "Entrenamiento inicial 2023:",
    len(train_2023)
)

print(
    "Validación 2024:",
    len(val_2024)
)

print(
    "Prueba final 2025:",
    len(test_2025)
)


# ============================================================
# 4. PREPARACIÓN PARA VALIDACIÓN 2024
# ============================================================

# Los umbrales de validación se calculan
# exclusivamente utilizando 2023.

umbrales_2023 = calcular_umbrales(
    train_2023
)

train = agregar_variables_relativas(
    train_2023,
    umbrales_2023
)

val = agregar_variables_relativas(
    val_2024,
    umbrales_2023
)

y_train = convertir_clases(
    train["borough"],
    train["demanda_relativa"],
    umbrales_2023
)

y_val = convertir_clases(
    val["borough"],
    val["demanda_relativa"],
    umbrales_2023
)

print("\nUmbrales de validación calculados con 2023:")

print(
    umbrales_2023.round(4).to_string()
)


# ============================================================
# 5. ETAPA 1: COMPARACIÓN INICIAL
# ============================================================

modelos_iniciales = {

    "Dummy": DummyClassifier(
        strategy="most_frequent"
    ),

    "Ridge_0.1": RidgeClassifier(
        alpha=0.1
    ),

    "Logistica_C_1": LogisticRegression(
        C=1,
        max_iter=2000
    ),

    "RandomForest": RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ),

    "HistGradientBoosting": (
        HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.05,
            random_state=42
        )
    )
}

resultados_2024 = []

for nombre, estimador in modelos_iniciales.items():

    _, _, metricas = entrenar_y_evaluar(
        nombre,
        estimador,
        VARIABLES_ORIGINALES,
        train,
        val,
        y_train,
        y_val
    )

    metricas["Etapa"] = "Comparacion inicial"
    resultados_2024.append(metricas)


# ============================================================
# 6. ETAPA 2: AJUSTES DE RIDGE
# ============================================================

configuraciones_ridge = {

    "Ridge_alpha_0.01": (
        RidgeClassifier(alpha=0.01),
        VARIABLES_ORIGINALES
    ),

    "Ridge_alpha_1": (
        RidgeClassifier(alpha=1),
        VARIABLES_ORIGINALES
    ),

    "Ridge_balanceado": (
        RidgeClassifier(
            alpha=0.1,
            class_weight="balanced"
        ),
        VARIABLES_ORIGINALES
    ),

    "Ridge_variables_relativas": (
        RidgeClassifier(
            alpha=0.1,
            class_weight="balanced"
        ),
        VARIABLES_FINALES
    )
}

for nombre, (estimador, variables) in (
    configuraciones_ridge.items()
):

    _, _, metricas = entrenar_y_evaluar(
        nombre,
        estimador,
        variables,
        train,
        val,
        y_train,
        y_val
    )

    metricas["Etapa"] = "Ajustes Ridge"
    resultados_2024.append(metricas)


# ============================================================
# 7. ETAPA 3: BASELINE HISTÓRICO
# ============================================================

pred_referencia_2024 = convertir_clases(
    val["borough"],
    val["demanda_relativa_lag1"],
    umbrales_2023
)

metricas_referencia = calcular_metricas(
    "Referencia_semana_anterior",
    y_val,
    pred_referencia_2024
)

metricas_referencia["Etapa"] = "Baseline historico"

resultados_2024.append(
    metricas_referencia
)


# ============================================================
# 8. GUARDAR COMPARACIÓN DE 2024
# ============================================================

CARPETA_RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

comparacion_2024 = pd.DataFrame(
    resultados_2024
)

columnas_comparacion = [
    "Etapa",
    "Modelo",
    "N",
    "Accuracy",
    "F1-macro",
    "Precision Media",
    "Recall Baja",
    "Recall Media",
    "Recall Alta",
    "Alta->Baja"
]

comparacion_2024 = comparacion_2024[
    columnas_comparacion
]

comparacion_2024.to_csv(
    RUTA_COMPARACION,
    index=False,
    encoding="utf-8-sig",
    float_format="%.6f"
)

print("\n" + "=" * 75)
print("ETAPAS 1-3: COMPARACIÓN Y MEJORAS EN 2024")
print("=" * 75)

print(
    comparacion_2024
    .round(4)
    .to_string(index=False)
)

print("\nCSV guardado:", RUTA_COMPARACION)


# ============================================================
# 9. SELECCIÓN DEL MODELO DE MACHINE LEARNING
# ============================================================

# Selección basada en la validación de 2024.
#
# Se conserva Ridge con variables relativas como
# candidato de ML, priorizando el equilibrio entre
# clases y la identificación de demanda Alta.
#
# La referencia semanal se mantiene como baseline.
#
# No se utilizarán datos de 2025 para modificar
# esta configuración.

MODELO_SELECCIONADO = "Ridge_variables_relativas"

ESTIMADOR_FINAL = RidgeClassifier(
    alpha=0.1,
    class_weight="balanced"
)

print("\n" + "=" * 75)
print("MODELO SELECCIONADO")
print("=" * 75)

print("Modelo ML:", MODELO_SELECCIONADO)
print("Algoritmo: RidgeClassifier")
print("Alpha: 0.1")
print("Pesos: balanced")
print("Variables:", len(VARIABLES_FINALES))
print("Baseline: referencia de semana anterior")

print(
    "\nNota: el baseline histórico superó ligeramente "
    "a Ridge en F1-macro de 2024."
)


# ============================================================
# 10. ENTRENAMIENTO FINAL: 2023-2024
# ============================================================

train_final = df[
    df["semana"].dt.year.isin([2023, 2024])
].copy()

# Para la prueba de 2025 se permite utilizar
# 2023 y 2024, pero nunca las etiquetas de 2025
# para calcular los umbrales.

umbrales_finales = calcular_umbrales(
    train_final
)

train_final = agregar_variables_relativas(
    train_final,
    umbrales_finales
)

test_final = agregar_variables_relativas(
    test_2025,
    umbrales_finales
)

y_train_final = convertir_clases(
    train_final["borough"],
    train_final["demanda_relativa"],
    umbrales_finales
)

y_test_final = convertir_clases(
    test_final["borough"],
    test_final["demanda_relativa"],
    umbrales_finales
)

modelo_final = crear_pipeline(
    ESTIMADOR_FINAL,
    VARIABLES_FINALES
)

modelo_final.fit(
    train_final[VARIABLES_FINALES],
    y_train_final
)


# ============================================================
# 11. EVALUACIÓN FINAL DE 2025
# ============================================================

pred_ridge_2025 = modelo_final.predict(
    test_final[VARIABLES_FINALES]
)

pred_referencia_2025 = convertir_clases(
    test_final["borough"],
    test_final["demanda_relativa_lag1"],
    umbrales_finales
)

predicciones_2025 = {
    "Ridge_variables_relativas": pred_ridge_2025,
    "Referencia_semana_anterior": pred_referencia_2025
}

resultados_finales = []

for nombre, pred in predicciones_2025.items():

    metricas = calcular_metricas(
        nombre,
        y_test_final,
        pred
    )

    metricas["Periodo entrenamiento"] = (
        "2023-2024" if nombre.startswith("Ridge")
        else "No aplica; umbrales 2023-2024"
    )

    metricas["Periodo prueba"] = "2025"

    resultados_finales.append(metricas)

evaluacion_2025 = pd.DataFrame(
    resultados_finales
)

columnas_finales = [
    "Modelo",
    "Periodo entrenamiento",
    "Periodo prueba",
    "N",
    "Accuracy",
    "F1-macro",
    "Precision Media",
    "Recall Baja",
    "Recall Media",
    "Recall Alta",
    "Alta->Baja"
]

evaluacion_2025 = evaluacion_2025[
    columnas_finales
]

evaluacion_2025.to_csv(
    RUTA_EVALUACION,
    index=False,
    encoding="utf-8-sig",
    float_format="%.6f"
)

print("\n" + "=" * 75)
print("ETAPA 4: EVALUACIÓN FINAL DE 2025")
print("=" * 75)

print(
    evaluacion_2025
    .round(4)
    .to_string(index=False)
)

print("\nCSV guardado:", RUTA_EVALUACION)


# ============================================================
# 12. MATRICES DE CONFUSIÓN Y REPORTE
# ============================================================

mostrar_detalle(
    "Ridge final - 2025",
    y_test_final,
    pred_ridge_2025
)

mostrar_detalle(
    "Referencia semanal - 2025",
    y_test_final,
    pred_referencia_2025
)


# ============================================================
# 13. EVALUACIÓN POR BOROUGH
# ============================================================

resultados_borough = []

boroughs_test = (
    test_final["borough"].to_numpy()
)

for borough in sorted(
    test_final["borough"].unique()
):

    mascara = boroughs_test == borough

    reales = y_test_final[mascara]

    for nombre, pred in predicciones_2025.items():

        estimadas = pred[mascara]

        metricas = calcular_metricas(
            nombre,
            reales,
            estimadas
        )

        metricas["Borough"] = borough

        resultados_borough.append(metricas)

metricas_borough = pd.DataFrame(
    resultados_borough
)

columnas_borough = [
    "Borough",
    "Modelo",
    "N",
    "Accuracy",
    "F1-macro",
    "Precision Media",
    "Recall Baja",
    "Recall Media",
    "Recall Alta",
    "Alta->Baja"
]

metricas_borough = metricas_borough[
    columnas_borough
]

metricas_borough.to_csv(
    RUTA_BOROUGHS,
    index=False,
    encoding="utf-8-sig",
    float_format="%.6f"
)

print("\n" + "=" * 75)
print("ETAPA 5: EVALUACIÓN POR BOROUGH - 2025")
print("=" * 75)

print(
    metricas_borough
    .round(4)
    .to_string(index=False)
)

print("\nCSV guardado:", RUTA_BOROUGHS)


# ============================================================
# 14. GUARDAR MODELO FINAL
# ============================================================

CARPETA_MODELOS.mkdir(
    parents=True,
    exist_ok=True
)

artefacto = {
    "modelo": modelo_final,
    "umbrales": umbrales_finales,
    "variables": VARIABLES_FINALES,
    "clases": CLASES,
    "algoritmo": "RidgeClassifier",
    "alpha": 0.1,
    "class_weight": "balanced",
    "periodo_entrenamiento": "2023-2024",
    "periodo_prueba": "2025",
    "fecha_generacion_utc": (
        datetime.now(timezone.utc).isoformat()
    ),
    "regla_variables_relativas": (
        "demanda_relativa_lag1 = lag_1 / media_movil_52; "
        "distancia_p33_lag1 = demanda_relativa_lag1 - P33; "
        "distancia_p67_lag1 = demanda_relativa_lag1 - P67"
    )
}

joblib.dump(
    artefacto,
    RUTA_MODELO
)

# Comprobar que el modelo guardado
# conserva las mismas predicciones.

artefacto_cargado = joblib.load(
    RUTA_MODELO
)

pred_recargada = (
    artefacto_cargado["modelo"].predict(
        test_final[VARIABLES_FINALES]
    )
)

if not np.array_equal(
    pred_ridge_2025,
    pred_recargada
):
    raise ValueError(
        "El modelo recargado produjo predicciones diferentes"
    )


# ============================================================
# 15. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 75)
print("ENTRENAMIENTO E3 COMPLETADO")
print("=" * 75)

print("\nArchivos generados:")

print("1.", RUTA_COMPARACION)
print("2.", RUTA_EVALUACION)
print("3.", RUTA_BOROUGHS)
print("4.", RUTA_MODELO)

print("\nModelo recargado: verificado correctamente")

print("\nNo se modificaron los datos originales.")
print("Los umbrales se calcularon sin fuga temporal.")
print("No se utilizaron datos de 2025 para ajustar el modelo.")

print(
    "\nPendiente: registrar experimentos "
    "y artefactos en MLflow EC2."
)
