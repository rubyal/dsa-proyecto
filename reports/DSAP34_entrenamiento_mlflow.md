# DSAP-34 — Entrenamiento de modelos y registro en MLflow

**Proyecto:** Predicción de demanda semanal NYC 311  
**Actividad Jira:** DSAP-34  
**Estado:** Entrenamiento y registro local completados

## 1. Objetivo

Entrenar y comparar modelos de clasificación supervisada para
anticipar el nivel de demanda semanal de solicitudes NYC 311
en los cinco boroughs de Nueva York.

## 2. Datos y metodología

Se utilizaron 780 observaciones semanales clasificadas entre
2023 y 2025, con 11 variables predictoras.

La variable objetivo `nivel_demanda` contempla tres categorías:
Baja, Media y Alta, definidas mediante los percentiles 33 y 67
de la demanda relativa de cada borough.

Se aplicó una separación temporal:

- Entrenamiento inicial: 2023 (260 observaciones).
- Validación: 2024 (265 observaciones).
- Entrenamiento final: 2023–2024 (525 observaciones).
- Evaluación final: 2025 (255 observaciones).

## 3. Comparación de modelos

Se evaluaron Regresión Logística, Random Forest,
HistGradientBoosting, árboles de decisión, Gaussian Naive Bayes
y RidgeClassifier.

RidgeClassifier presentó el mejor comportamiento durante
la validación de 2024.

### Optimización de RidgeClassifier

| Alpha | Accuracy | F1-macro | Recall Alta |
|---|---:|---:|---:|
| 0.10 | 0.6000 | 0.5900 | 0.6533 |
| 0.01 | 0.5849 | 0.5784 | 0.6267 |
| 1.00 | 0.5887 | 0.5561 | 0.7200 |
| 10.00 | 0.4755 | 0.4387 | 0.6800 |
| 100.00 | 0.4566 | 0.4180 | 0.6133 |

Se seleccionó `alpha=0.1` porque obtuvo el mayor F1-macro,
métrica principal definida en DSAP-31.

## 4. Resultados sobre 2025

| Métrica | Random Forest | RidgeClassifier |
|---|---:|---:|
| Accuracy | 0.5255 | 0.5686 |
| F1-macro | 0.5267 | 0.5386 |
| Recall Alta | 0.6143 | 0.7571 |

### Matriz de confusión de RidgeClassifier

| Clase real | Pred Baja | Pred Media | Pred Alta |
|---|---:|---:|---:|
| Baja | 74 | 5 | 8 |
| Media | 56 | 18 | 24 |
| Alta | 12 | 5 | 53 |

El modelo identifica correctamente el 75.71 % de las semanas
con demanda Alta, pero presenta dificultades con la categoría
Media, cuyo recall es de aproximadamente 18.37 %.

## 5. Registro de experimentos

Se utilizó MLflow 3.18.0 con un backend local SQLite para
registrar las métricas, los parámetros y los modelos.

El experimento se denominó:

`DSAP34_NYC311_Clasificacion_Demanda`

Se registraron ejecuciones de Dummy, Random Forest y
RidgeClassifier, incluyendo el modelo seleccionado con
`alpha=0.1`.

La serialización de modelos se realizó mediante `skops`.

## 6. Conclusiones

RidgeClassifier fue el mejor candidato entre los modelos
evaluados, con un accuracy del 56.86 % y F1-macro de 0.5386
sobre el conjunto de 2025.

Aunque mejora el desempeño de Random Forest, todavía no
alcanza la meta inicial propuesta de F1-macro de 0.60.

Se recomienda incorporar nuevas variables predictoras y
continuar evaluando la estabilidad temporal del modelo.

La evaluación de 2025 debe interpretarse con cautela porque
durante el desarrollo también se consultaron resultados de
otros modelos sobre ese período.

## 7. Evidencias

- `notebooks/04_validacion_historico_2022_2025.ipynb`
- `notebooks/06_entrenamiento_MLflow_DSAP34.ipynb`
- `reports/figures/DSAP34_mlflow_randomforest.png`
- `reports/figures/DSAP34_mlflow_ridge.png`
- `reports/figures/DSAP34_mlflow_artefactos.png`

**Pendiente:** coordinar la integración de los experimentos
con el servidor MLflow del equipo, si así lo exige la entrega.