### Definición de métricas de evaluación del modelo — Corrección R2

El proyecto plantea un problema de clasificación supervisada multiclase, cuyo objetivo es anticipar el nivel de demanda semanal de solicitudes NYC 311 en cada borough de Nueva York. La variable objetivo, `nivel_demanda`, contempla tres categorías: Baja, Media y Alta.

Para evaluar los modelos se utilizará **F1-macro como métrica principal**, dado que permite considerar de manera equilibrada el desempeño de las tres clases. Esta métrica calcula el promedio del F1-score obtenido individualmente para cada categoría, sin dar mayor importancia a aquellas que tengan más observaciones.

La selección de F1-macro también responde a los resultados del análisis exploratorio. Aunque la distribución global de las clases es relativamente equilibrada, se identificaron diferencias importantes entre distritos y períodos. En consecuencia, un modelo podría alcanzar una buena exactitud general y, al mismo tiempo, presentar dificultades para reconocer determinadas categorías.

Como métricas complementarias se utilizarán accuracy, precision y recall por clase, además de la matriz de confusión.

**Accuracy** permitirá conocer la proporción total de semanas clasificadas correctamente. **Precision** mostrará qué proporción de las predicciones asignadas a cada nivel de demanda son correctas, mientras que **recall** permitirá identificar qué porcentaje de las semanas pertenecientes a cada categoría fue reconocido por el modelo.

Se prestará especial atención al **recall de la categoría Alta**, debido a su importancia operativa. No identificar anticipadamente una semana de demanda elevada podría limitar la preparación de personal y recursos para atender un incremento de solicitudes.

La matriz de confusión complementará la evaluación al mostrar los errores entre las tres categorías, particularmente cuando una semana de demanda Alta se clasifique como Media o Baja.

#### Criterio de éxito

Se propone seleccionar el modelo que obtenga el mejor F1-macro sobre un conjunto de evaluación temporal, siempre que presente un desempeño consistente entre las tres categorías y supere un modelo de referencia.

Como criterio inicial de aceptación se propone alcanzar **F1-macro igual o superior a 0,60**, sujeto a validación con los resultados de los experimentos y a la comparación con el modelo base.

Este umbral constituye una meta inicial del proyecto, no un resultado alcanzado.

#### Estrategia de evaluación

Para evitar fuga de información, se respetará el orden cronológico de las observaciones. Los modelos se entrenarán con períodos anteriores y se evaluarán con semanas posteriores, sin realizar particiones aleatorias.

Asimismo, las variables predictoras se construirán utilizando exclusivamente información disponible antes de la semana que se desea predecir.

El desempeño se comparará entre modelos y se registrarán las métricas y parámetros de los experimentos en MLflow, permitiendo documentar y reproducir el proceso de selección.

La evaluación final considerará tanto las métricas globales como el comportamiento por categoría y borough, buscando que el modelo sea útil para apoyar la planificación operativa.