# Manual de usuario — Tablero NYC 311

**Proyecto:** Despliegue de Soluciones Analíticas (MIAD) · Entrega 3  
**Aplicación:** NYC 311 — Predicción de demanda semanal por borough  
**Equipo:** Laura Vásquez Cadena, Ruby Alvarez Rodríguez y Jorge Lopera  
**Versión del manual:** 2.0 · 24 de noviembre de 2026

---

## 1. Propósito

Este tablero permite explorar el historial de solicitudes del servicio NYC 311 y consultar el **nivel previsto de demanda semanal (Baja, Media o Alta)** para los cinco boroughs de Nueva York: Bronx, Brooklyn, Manhattan, Queens y Staten Island.

La herramienta está diseñada para que los gestores de servicios urbanos puedan **anticipar la carga operativa semanal por zona** y asignar recursos de manera preventiva, antes de que se acumulen las solicitudes.

Las predicciones provienen de una API REST (FastAPI) que utiliza un modelo RidgeClassifier empaquetado como librería Python (.whl). El tablero consume la API; no entrena ni modifica el modelo.

## 2. Requisitos previos

Para acceder al tablero y la API se necesita:

- Navegador web actualizado (Chrome, Firefox, Edge o Safari).
- Conexión a internet con acceso a los puertos **8501** (tablero) y **8000** (API) del servidor de despliegue.
- No se requiere instalación de software adicional ni credenciales de acceso.

## 3. URLs de acceso

| Servicio         | URL                            | Descripción                         |
|------------------|--------------------------------|-------------------------------------|
| Tablero          | `http://184.198.166.131:8501`         | Interfaz visual Streamlit           |
| API              | `http://184.198.166.131:8000`         | API REST de predicción              |
| Health check     | `http://184.198.166.131:8000/health`  | Verificación de estado del servicio |
| Documentación API| `http://184.198.166.131:8000/docs`    | Swagger UI interactivo              |

> **Nota:** la IP pública del servidor EC2 puede cambiar si la instancia se detiene y reinicia. Consulte al equipo técnico la IP vigente. En pruebas locales, sustituya `<IP_EC2>` por `localhost`.

## 4. Estructura del tablero

El tablero tiene dos secciones accesibles desde el menú lateral izquierdo:

| Sección          | Contenido principal                                                    |
|------------------|------------------------------------------------------------------------|
| 🏠 **Inicio**    | KPIs, predicciones por borough, tendencias por tipo de solicitud       |
| 📊 **Análisis**  | Exploración histórica, filtros, distribución de niveles, consulta individual |

El menú lateral también muestra:

- Indicador de conexión con la API (verde si está conectada).
- URL de la API en uso.
- Información del modelo (RidgeClassifier, alpha=0.1).
- Fuente y período de los datos.

## 5. Sección «Inicio»

### 5.1 Indicadores principales

- **Total de solicitudes:** cantidad acumulada en el período histórico cargado.
- **Semana de predicción:** la semana calendario para la cual el modelo genera la predicción.

### 5.2 Tarjetas de predicción por borough

Cinco tarjetas, una por borough, muestran:

- Nombre del borough.
- **Nivel de demanda predicho** (Baja, Media o Alta) con código de color: verde (Baja), amarillo (Media) y rojo (Alta).
- Cantidad de solicitudes de la última semana observada como referencia.

### 5.3 Visualizaciones comparativas

- **Gráfico de barras por borough:** compara visualmente el nivel predicho de los cinco boroughs.
- **Selector de tipo de solicitud:** permite filtrar por categorías como ruido, basuras y limpieza, calefacción/agua caliente, y calles y vías.
- **Gráfica temporal por categoría:** muestra la evolución semanal del tipo de solicitud seleccionado.

### 5.4 Tabla resumen por categoría y borough

Tabla cruzada que presenta el nivel estimado por cada combinación de borough y tipo de solicitud.

> **Importante:** los niveles por categoría se calculan con reglas históricas (medias móviles y percentiles) y son distintos de las predicciones generales que devuelve la API del modelo.

## 6. Sección «Análisis»

### 6.1 Filtros disponibles

- **Boroughs:** selección múltiple para incluir o excluir boroughs del análisis.
- **Rango de años:** deslizador para restringir el período de los gráficos históricos.

### 6.2 Visualizaciones

- **Solicitudes semanales:** serie de tiempo con la evolución de solicitudes, coloreada por nivel (Baja, Media, Alta).
- **Distribución de niveles por borough:** gráfico de barras agrupadas que muestra cuántas semanas se clasificaron en cada nivel.
- **Umbrales por borough:** tabla con los valores de los percentiles P33 y P66 que definen los cortes entre niveles.

### 6.3 Consulta individual de borough

1. Seleccione un borough en el desplegable **«Consultar borough»**.
2. Se muestra una tarjeta con el **nivel predicho** para la próxima semana.
3. La **serie temporal individual** incluye:
   - Puntos coloreados por nivel (verde, amarillo, rojo).
   - Línea de tendencia en gris.
   - Líneas de referencia punteadas para los umbrales P33 y P66.
4. Indicadores descriptivos debajo del gráfico:
   - **Promedio semanal** de solicitudes.
   - **Máximo** y **mínimo** histórico.
   - **% de semanas altas** respecto al total.

## 7. Interpretación de resultados

| Nivel     | Significado                                                 | Color       |
|-----------|-------------------------------------------------------------|-------------|
| **Baja**  | Demanda por debajo del percentil 33 histórico del borough   | 🟢 Verde    |
| **Media** | Demanda entre los percentiles 33 y 66                       | 🟡 Amarillo |
| **Alta**  | Demanda por encima del percentil 66 histórico del borough   | 🔴 Rojo     |

**Consideraciones clave:**

- Los niveles indican **categorías relativas** al historial de cada borough, no cantidades exactas de solicitudes futuras.
- Cada borough tiene sus propios umbrales, calculados sobre su historial individual (2022–2025).
- El conteo de «última semana observada» es un dato histórico de referencia, no una predicción.
- Los colores facilitan la lectura rápida, pero siempre debe consultarse también la etiqueta textual.

## 8. API REST de predicción

El tablero consume los siguientes endpoints de la API FastAPI:

| Método | Endpoint                       | Descripción                                       |
|--------|--------------------------------|---------------------------------------------------|
| GET    | `/`                            | Mensaje de bienvenida y versión                   |
| GET    | `/health`                      | Estado del servicio (OK si responde)              |
| POST   | `/predict`                     | Predicción a partir de features enviados en JSON  |
| GET    | `/predict/next-week/{borough}` | Predicción de la próxima semana para un borough   |

**Ejemplo de consulta directa:**

```
GET http://<IP_EC2>:8000/predict/next-week/BRONX
```

Respuesta esperada:

```json
{
  "borough": "BRONX",
  "semana": "2025-12-29",
  "nivel_demanda": "Media",
  "solicitudes_estimadas": 12345
}
```

La documentación interactiva (Swagger UI) está disponible en `http://<IP_EC2>:8000/docs`.

## 9. Comprobación rápida de funcionamiento

1. Abra `http://<IP_EC2>:8000/health` y confirme que responde `{"status": "ok"}`.
2. Abra `http://<IP_EC2>:8501` y verifique que el tablero carga sin errores.
3. En el menú lateral, confirme el indicador verde **«API de predicción conectada»**.
4. En **Inicio**, verifique que aparecen las cinco tarjetas de predicción con la fecha de la semana pronosticada.
5. En **Análisis**, seleccione **BRONX** en «Consultar borough» y confirme que el nivel coincide con la tarjeta de Inicio.
6. Si aparece un error de conexión, verifique que ambos contenedores Docker estén activos (`docker ps`).

## 10. Solución de problemas comunes

| Problema                                 | Causa probable                      | Solución                                          |
|------------------------------------------|-------------------------------------|---------------------------------------------------|
| Tablero no carga                         | Contenedor dashboard detenido       | Ejecutar `docker compose up -d` en el servidor    |
| "No fue posible cargar las predicciones" | API no disponible                   | Verificar contenedor api: `docker compose logs api`|
| Tarjetas sin predicción                  | Endpoint `/predict/next-week` falla | Revisar logs: `docker compose logs api`           |
| IP no funciona                           | EC2 se detuvo y la IP cambió        | Consultar la nueva IP en la consola AWS           |
| Gráficos vacíos                          | Archivo parquet faltante            | Ejecutar `dvc pull` para restaurar los datos      |

## 11. Limitaciones y precauciones

- Esta es una herramienta analítica de apoyo; no reemplaza el criterio operativo ni garantiza volúmenes futuros exactos.
- Los resultados dependen de la calidad, cobertura y actualización de los datos históricos (NYC Open Data, 2022–2025).
- Las categorías Baja/Media/Alta son relativas al historial de cada borough y no representan probabilidades.
- Las visualizaciones por tipo de solicitud usan estimaciones históricas (medias móviles y percentiles), distintas del modelo de clasificación de la API.
- La API calcula la semana siguiente al **último dato disponible en su historial**, no necesariamente la semana calendario actual. Para predicciones posteriores a diciembre 2025, se requiere actualizar la fuente de datos.
- La clasificación y las métricas del modelo deben interpretarse junto con el reporte de evaluación final del proyecto.

---

**Datos:** NYC Open Data — 311 Service Requests (2022–2025)  
**Modelo:** RidgeClassifier (alpha=0.1) empaquetado como `nyc311_model-0.1.0`  
**Infraestructura:** Docker Compose (API + Dashboard) en AWS EC2  
**Código fuente:** [github.com/rubyal/dsa-proyecto](https://github.com/rubyal/dsa-proyecto)
