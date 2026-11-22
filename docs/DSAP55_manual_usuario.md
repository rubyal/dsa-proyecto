# Manual de usuario — Tablero NYC 311

**Proyecto:** Despliegue de Soluciones Analíticas (MIAD) · Entrega 3  
**Aplicación:** NYC 311 — Predicción de demanda semanal por borough  
**Equipo:** Laura Vásquez, Ruby Alvarez y Jorge Lopera  
**Versión del manual:** 1.0 · 21 de noviembre de 2026

## 1. Propósito

El tablero ayuda a explorar las solicitudes de servicio NYC 311 y consultar el **nivel previsto de demanda semanal (Baja, Media o Alta)** para los cinco boroughs de Nueva York: Bronx, Brooklyn, Manhattan, Queens y Staten Island. Las predicciones se consultan a través de una API FastAPI que utiliza el modelo empaquetado; el tablero no vuelve a entrenarlo.

## 2. Acceso y estructura

Abra la dirección del tablero Streamlit proporcionada por el equipo de despliegue. En el menú lateral hay dos secciones:

- **🏠 Inicio:** resumen de solicitudes, predicciones por borough, tendencias y consulta por tipo de solicitud.
- **📊 Análisis:** exploración histórica, filtros por borough y años, distribución de niveles, umbrales y consulta individual.

La dirección pública de despliegue se añadirá cuando esté disponible. En pruebas locales, Streamlit suele utilizar `http://localhost:8501`.

## 3. Sección «Inicio»

1. Revise el indicador de **total de solicitudes** del período histórico representado.
2. Consulte las **tarjetas de predicción**: cada tarjeta presenta un borough y el nivel esperado (Baja, Media o Alta) para la semana mostrada.
3. Use el selector **Tipo de solicitud** para examinar tendencias de las categorías presentadas en la interfaz, como ruido, basuras y limpieza, calefacción/agua caliente y calles y vías.
4. Revise el gráfico de comparación entre boroughs y la gráfica temporal de la categoría seleccionada.
5. Revise la tabla por borough y categoría. **Importante:** los niveles por categoría se calculan con reglas históricas (medias móviles y percentiles), y no deben confundirse con las predicciones generales que devuelve la API del modelo.

## 4. Sección «Análisis»

1. En **Boroughs**, marque uno o varios territorios para mostrar únicamente sus series.
2. Ajuste **Rango de años** para restringir el período de los gráficos históricos.
3. Consulte las gráficas de **solicitudes semanales**, **distribución de niveles** y la tabla de **umbrales por borough**.
4. En **🔍 Consultar borough**, elija un territorio. El tablero muestra su nivel de demanda previsto y la serie histórica con líneas de referencia P33 y P66.
5. Revise los indicadores descriptivos: promedio semanal, máximo, mínimo y porcentaje de semanas clasificadas como altas.

## 5. Interpretación de resultados

- **Baja:** demanda relativamente baja según los criterios de clasificación aplicados.
- **Media:** nivel intermedio.
- **Alta:** demanda relativamente elevada.

Los niveles indican **categorías de demanda**, no el número exacto de solicitudes futuras. El conteo de la **última semana observada** que aparece junto a algunos resultados es un dato histórico, no una cantidad predicha por la API. Los colores permiten distinguir las categorías, pero siempre debe leerse también la etiqueta textual.

## 6. Fuente de predicción y disponibilidad

Las predicciones generales del tablero provienen de la API del modelo mediante `GET /predict/next-week/{borough}`. La disponibilidad del servicio se comprueba mediante `GET /health`. Si la API no responde, el tablero puede mostrar un error o no presentar las predicciones; comunique la incidencia al equipo técnico y verifique que ambos servicios estén activos.

La API calcula la semana siguiente al **último dato que existe en su historial**, no necesariamente la semana calendario actual. En las pruebas de integración se obtuvo la semana **2025-12-29**. Para predicciones actualizadas de 2026 haría falta actualizar la fuente de datos y el procesamiento correspondiente.

## 7. Limitaciones y precauciones

- Es una herramienta analítica de apoyo, no una garantía de volumen futuro ni un reemplazo del criterio operativo.
- Los resultados dependen de la calidad, cobertura y actualización de los datos históricos.
- Las categorías Baja/Media/Alta no representan probabilidades ni cantidades exactas de solicitudes.
- Las visualizaciones por tipo de solicitud utilizan estimaciones históricas distintas de la predicción general por borough de la API.
- La visualización histórica y los resultados del modelo pueden cubrir períodos diferentes; consulte siempre la fecha indicada en pantalla.
- La clasificación y las métricas del modelo deben interpretarse con las precisiones del reporte de evaluación final.

## 8. Comprobación rápida de funcionamiento

1. Abra **Inicio** y confirme que aparecen las cinco tarjetas de boroughs.
2. Compruebe que se muestra la fecha de la semana pronosticada.
3. Abra **Análisis**, modifique el filtro de boroughs y seleccione **BRONX** en «Consultar borough».
4. Confirme que el nivel de BRONX coincide con la tarjeta correspondiente de **Inicio**.
5. Si falta una predicción o hay un error de conexión, reporte el mensaje mostrado y la fecha de la prueba.

---

**Pendiente para la versión final:** incluir URL pública de AWS/Streamlit, capturas definitivas de Inicio y Análisis, y cualquier diferencia funcional que aparezca después de integrar el PR en `dev` y desplegar Docker.
