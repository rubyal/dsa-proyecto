# DSAP-32 — Tabla de variables predictoras

## Definición de variables predictoras — Corrección R3

El proyecto busca predecir el nivel de demanda semanal de solicitudes NYC 311 en los cinco boroughs de Nueva York mediante un modelo de clasificación supervisada multiclase.

Para ello, se propone utilizar variables geográficas, temporales e históricas, incluyendo indicadores de calendario, rezagos y estadísticas móviles de las solicitudes.

La selección de estas variables responde a los hallazgos de la exploración inicial, en la que se identificaron diferencias importantes entre distritos, variaciones temporales y comportamientos estacionales de la demanda.

### Variables predictoras candidatas

| Variable | Tipo | Rol | Justificación |
|---|---|---|---|
| borough | Categórica | Predictora | Identifica el distrito y las diferencias geográficas de demanda. |
| semana_anio | Numérica | Predictora | Representa la estacionalidad semanal. |
| mes | Numérica | Predictora | Identifica cambios asociados a diferentes períodos del año. |
| feriado_semana | Binaria | Predictora candidata | Identifica semanas con feriados, que podrían presentar comportamientos particulares. |
| lag_1 | Numérica | Predictora candidata | Recoge la demanda registrada una semana atrás. |
| lag_2 | Numérica | Predictora candidata | Incorpora información histórica de dos semanas atrás. |
| lag_4 | Numérica | Predictora candidata | Captura la demanda observada cuatro semanas antes. |
| lag_52 | Numérica | Predictora candidata | Aporta una referencia estacional anual. |
| media_movil_4 | Numérica | Predictora candidata | Resume el comportamiento reciente. |
| media_movil_12 | Numérica | Predictora candidata | Representa una tendencia de mediano plazo. |
| media_movil_52 | Numérica | Predictora candidata | Resume el comportamiento histórico anual. |
| std_movil_4 | Numérica | Predictora candidata | Mide cambios en la variabilidad reciente. |

### Variable objetivo

La variable objetivo es `nivel_demanda`, definida mediante las categorías Baja, Media y Alta.

Para construirla se utiliza la demanda relativa semanal de cada borough:

Demanda relativa = Total de solicitudes de la semana / Promedio de solicitudes de las 52 semanas anteriores.

Los límites de clasificación corresponden a los percentiles 33 y 67 de la demanda relativa de cada distrito, calculados con información del período de entrenamiento, conforme a la metodología documentada en DSAP-30.

### Variables descartadas como predictoras

Se excluyen como variables de entrada el total real de solicitudes y la demanda relativa correspondientes a la semana que se desea predecir, debido a que solo se conocen una vez finalizada esa semana.

También se descarta `n_no_urgentes` como indicador diferenciado de demanda, dado que proviene de un filtro provisional de tipos de quejas que no resulta necesario bajo la definición de NYC 311 adoptada en la corrección R2.

### Prevención de fuga de información

Las variables históricas se calcularán de manera independiente para cada borough, respetando el orden cronológico de las observaciones.

Los rezagos y promedios móviles utilizarán exclusivamente semanas anteriores a la semana objetivo. Para ello se aplicarán operaciones de desplazamiento temporal antes de calcular las estadísticas móviles.

Los indicadores de calendario corresponderán a información conocida anticipadamente para la semana que se pretende predecir.

### Validación posterior

Esta tabla establece las variables candidatas para el proceso de modelado. La selección definitiva se realizará durante DSAP-34 mediante experimentos de entrenamiento, comparación de modelos y evaluación temporal.

Se documentarán las variables utilizadas en cada experimento y su desempeño en MLflow, para facilitar la reproducibilidad y comparación de resultados.