## Dashboard interactivo NYC 311

### Descripción

Se desarrolló un dashboard interactivo en **Streamlit** para el análisis histórico y la predicción semanal de los niveles de demanda de solicitudes NYC 311 en los cinco distritos de Nueva York, utilizando información correspondiente al periodo 2022–2025.

El tablero integra un modelo de clasificación **RidgeClassifier (α=0.1)**, entrenado con información de 2023–2024, para predecir niveles de demanda baja, media y alta.

### Funcionalidades

El dashboard dispone de dos secciones:

- **Inicio:** indicadores generales, predicciones semanales por distrito, tendencias históricas por tipo de solicitud y estimaciones de demanda por categoría.
- **Análisis:** filtros por distrito y periodo, series temporales, distribución de niveles de demanda, umbrales estadísticos e indicadores descriptivos.

### Datasets utilizados

Los datos están almacenados en formato Parquet y gestionados mediante DVC.

| Dataset | Descripción |
|---|---|
| `data/raw/nyc311_diario_borough_tipo.parquet` | Información histórica de solicitudes por fecha, distrito y tipo de solicitud. |
| `data/processed/dataset_modelado_semanal.parquet` | Dataset preparado para el modelado, con variables temporales, rezagos, estadísticas móviles y niveles de demanda. |

El dataset de modelado semanal fue preparado por Jorge y se encuentra referenciado mediante `data/processed/dataset_modelado_semanal.parquet.dvc`.

### Requisitos

- Python y pip.
- Dependencias del proyecto definidas en `requirements.txt`.
- DVC con soporte para Amazon S3.
- Credenciales AWS vigentes y permisos de lectura sobre el almacenamiento remoto de DVC.

### Ejecución local

**1. Clonar el repositorio**

```bash
git clone https://github.com/rubyal/dsa-proyecto.git
cd dsa-proyecto
```

**2. Crear y activar un entorno virtual**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Instalar dependencias**

```bash
pip install -r requirements.txt
```

Si DVC con soporte S3 no está incluido en las dependencias:

```bash
pip install "dvc[s3]"
```

**4. Recuperar los datasets**

Con las credenciales AWS configuradas y los permisos correspondientes:

```bash
dvc pull
```

**5. Ejecutar el dashboard**

```bash
streamlit run dashboard/app.py
```

**6. Acceder a la aplicación**

Abrir en el navegador:

http://localhost:8501/

### Disponibilidad

Actualmente, el dashboard se ejecuta en un entorno local y no cuenta con un despliegue público. Su código fuente está disponible en el repositorio de GitHub del proyecto.

### Consideraciones técnicas

- Los datos se cargan desde archivos Parquet locales recuperados mediante DVC.
- El modelo RidgeClassifier se entrena al iniciar la aplicación y se reutiliza mediante la caché de Streamlit.
- Las predicciones del modelo corresponden a niveles de demanda, no a cantidades exactas de solicitudes.
- Las estimaciones por categoría utilizan promedios móviles y percentiles históricos.
- El acceso al almacenamiento remoto requiere credenciales autorizadas, que no deben incorporarse al repositorio.