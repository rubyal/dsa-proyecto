## Proyecto: Análisis de solicitudes ciudadanas NYC 311

### Problema de negocio

Analizar las solicitudes ciudadanas relacionadas con seguridad y convivencia urbana en Nueva York para identificar patrones que puedan apoyar la gestión de los servicios públicos.

### Pregunta de negocio

¿Cómo se distribuyen las solicitudes ciudadanas relacionadas con seguridad y convivencia en Nueva York y en qué medida es posible utilizar sus características para predecir su comportamiento?

### Alcance

El proyecto contempla:

- Análisis exploratorio y evaluación de la calidad de los datos.
- Limpieza y preparación de la información.
- Análisis descriptivo de patrones temporales, geográficos y por categoría.
- Evaluación de un enfoque predictivo, sujeto a la selección y validación de una variable objetivo.
- Desarrollo de visualizaciones y un prototipo.
- Versionamiento del código mediante Git y de los datos mediante DVC.

### Conjunto de datos

- **Archivo:** `data/raw/nyc_311_safety.parquet`
- **Registros:** 3.167.279
- **Variables:** 11
- **Formato:** Parquet
- **Estado:** descargado correctamente desde Amazon S3 mediante DVC.
- **Repositorio remoto DVC:** `s3://miad-dsa-proyecto-efc3d62b/dvcstore`

### Documentación

La definición completa del problema, los objetivos, el alcance y las limitaciones se encuentra en [docs/definicion_problema.md](docs/definicion_problema.md).

**Nota:** Los enfoques descriptivo y predictivo son preliminares hasta validar el contenido y la calidad de los datos.