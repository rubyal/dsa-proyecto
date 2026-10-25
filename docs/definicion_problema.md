Definición del problema – Proyecto DSA

1. Identificación del proyecto

Nombre provisional: Análisis de solicitudes ciudadanas relacionadas con seguridad y convivencia en Nueva York.

Fuente de datos: Sistema NYC 311.

Conjunto de datos seleccionado: nyc_311_safety.parquet.

Estado de disponibilidad: El conjunto de datos está registrado mediante DVC, pero aún está pendiente recuperarlo desde el almacenamiento S3.

2. Contexto

El proyecto propone utilizar información de solicitudes ciudadanas registradas en el sistema NYC 311 para estudiar problemáticas relacionadas con la seguridad y la convivencia urbana.

El propósito inicial es identificar patrones en las solicitudes que puedan contribuir a comprender las necesidades reportadas por la ciudadanía y apoyar la toma de decisiones mediante técnicas de analítica de datos.

Nota: El alcance definitivo y las variables de análisis deberán validarse una vez se recupere y explore el conjunto de datos.

3. Pregunta de negocio

**¿Cómo se distribuyen las solicitudes ciudadanas relacionadas con seguridad y convivencia en Nueva York y en qué medida es posible utilizar sus características para predecir su comportamiento?**

Esta pregunta contempla dos componentes:

- **Descriptivo:** identificar los tipos de solicitudes más frecuentes, su distribución geográfica y su evolución temporal, siempre que el conjunto de datos contenga las variables necesarias.
- **Predictivo:** evaluar la posibilidad de construir un modelo que permita anticipar una característica relevante de las solicitudes, por ejemplo, su volumen por zona o período.

La variable objetivo y la técnica predictiva se definirán después de explorar el conjunto de datos y validar su calidad.

4. Objetivo general

Analizar las solicitudes ciudadanas relacionadas con seguridad y convivencia registradas en el sistema NYC 311, mediante técnicas descriptivas y predictivas, para identificar patrones que puedan contribuir a la comprensión de las necesidades ciudadanas y apoyar la toma de decisiones.

5. Alcance del proyecto

El proyecto contempla el análisis descriptivo y predictivo de las solicitudes ciudadanas relacionadas con seguridad y convivencia registradas en el sistema NYC 311 de Nueva York.

**El alcance incluye:**

- **Exploración de datos:** identificar la estructura del conjunto de datos, las variables disponibles, sus tipos y su calidad.
- **Preparación de datos:** revisar valores faltantes, registros duplicados e inconsistencias para definir las transformaciones necesarias.
- **Análisis descriptivo:** estudiar la frecuencia de las solicitudes y los patrones temporales, geográficos y por categoría que permitan las variables disponibles.
- **Análisis predictivo:** seleccionar una variable objetivo y evaluar modelos apropiados para estimar su comportamiento.
- **Visualización:** presentar los principales resultados mediante gráficos y un prototipo que facilite su interpretación.
- **Versionamiento:** utilizar Git para el código y la documentación, y DVC para gestionar las versiones de los datos.

6. Limitaciones

El proyecto presenta las siguientes limitaciones iniciales:

- **Calidad y cobertura:** aún no se han verificado las variables, los períodos disponibles ni la representatividad de los registros.
- **Interpretación:** las solicitudes ciudadanas no equivalen necesariamente a delitos confirmados.
- **Predicción:** la selección de la variable objetivo y la viabilidad del modelo dependerán de la información disponible.

El proyecto no contempla implementar directamente intervenciones de seguridad pública ni demostrar relaciones causales entre las variables analizadas.