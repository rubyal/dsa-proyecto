"""
NYC 311 — Tablero de predicción de demanda semanal por borough
Despliegue de Soluciones Analíticas · MIAD · Entrega 2

Uso:
    streamlit run app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NYC 311 · Predicción de demanda",
    page_icon="🏙️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Paleta de colores
# ---------------------------------------------------------------------------
COLOR = {"bajo": "#2196F3", "medio": "#FFC107", "alto": "#F44336"}
BOROUGHS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]

# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    """Carga el parquet y construye la serie semanal por borough."""
    # Buscar el parquet en varias rutas posibles
    rutas = [
        Path("data/raw/nyc311_diario_borough_tipo.parquet"),
        Path("../data/raw/nyc311_diario_borough_tipo.parquet"),
    ]
    # Detectar raíz del repo
    repo = Path(".").resolve()
    while not (repo / ".git").exists() and repo != repo.parent:
        repo = repo.parent
    rutas.insert(0, repo / "data" / "raw" / "nyc311_diario_borough_tipo.parquet")

    df = None
    for ruta in rutas:
        if ruta.exists():
            df = pd.read_parquet(ruta)
            break
    if df is None:
        st.error("No se encontró el archivo parquet. Ejecuta `dvc pull` primero.")
        st.stop()

    df["dia"] = pd.to_datetime(df["dia"])
    d = df[df["borough"] != "Unspecified"].copy()
    d["semana"] = d["dia"].dt.to_period("W-SUN").dt.start_time

    ini, fin = df["dia"].min(), df["dia"].max()
    semanas = d["semana"].drop_duplicates().sort_values()
    completas = semanas[(semanas >= ini) & (semanas + pd.Timedelta(days=6) <= fin)]

    sem = (
        d[d["semana"].isin(completas)]
        .groupby(["semana", "borough"], as_index=False)["n"]
        .sum()
        .sort_values(["borough", "semana"])
    )
    return sem


@st.cache_data
def calcular_umbrales(sem):
    """Calcula p33/p66 globales por borough para etiquetar."""
    umbrales = {}
    for borough in BOROUGHS:
        serie = sem[sem["borough"] == borough]["n"]
        umbrales[borough] = {
            "p33": serie.quantile(0.33),
            "p66": serie.quantile(0.66),
        }
    return umbrales


def etiquetar(valor, p33, p66):
    if valor <= p33:
        return "bajo"
    elif valor <= p66:
        return "medio"
    else:
        return "alto"


def prediccion_dummy(sem, umbrales):
    """
    Genera predicciones dummy para la próxima semana.
    Cuando el modelo de Jorge esté listo, reemplazar esta función por:
        import joblib
        modelo = joblib.load("models/modelo_final.pkl")
        prediccion = modelo.predict(features)
    """
    ultima_semana = sem["semana"].max()
    proxima = ultima_semana + pd.Timedelta(weeks=1)

    predicciones = []
    for borough in BOROUGHS:
        serie_b = sem[sem["borough"] == borough].sort_values("semana")
        # Usar promedio de últimas 4 semanas como estimación
        ultimas_4 = serie_b.tail(4)["n"].mean()
        # Agregar algo de variación aleatoria para simular
        np.random.seed(hash(borough) % 2**31)
        estimado = ultimas_4 * np.random.uniform(0.9, 1.1)
        nivel = etiquetar(estimado, umbrales[borough]["p33"], umbrales[borough]["p66"])
        predicciones.append({
            "borough": borough,
            "semana": proxima,
            "solicitudes_estimadas": int(estimado),
            "nivel_demanda": nivel,
        })
    return pd.DataFrame(predicciones)


# ---------------------------------------------------------------------------
# Cargar datos
# ---------------------------------------------------------------------------
sem = cargar_datos()
umbrales = calcular_umbrales(sem)

# Etiquetar datos históricos
sem["nivel"] = sem.apply(
    lambda r: etiquetar(r["n"], umbrales[r["borough"]]["p33"], umbrales[r["borough"]]["p66"]),
    axis=1,
)

pred = prediccion_dummy(sem, umbrales)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏙️ NYC 311 — Predicción de demanda semanal")
st.markdown(
    "Tablero para planificadores de operaciones del 311. "
    "Muestra el historial de solicitudes por borough y la predicción "
    "del nivel de demanda (bajo / medio / alto) para la próxima semana."
)

# ---------------------------------------------------------------------------
# KPIs: predicción de la próxima semana
# ---------------------------------------------------------------------------
st.header("📊 Predicción para la próxima semana")
proxima_fecha = pred["semana"].iloc[0].strftime("%d %b %Y")
st.caption(f"Semana del {proxima_fecha}")

cols = st.columns(len(BOROUGHS))
for i, borough in enumerate(BOROUGHS):
    row = pred[pred["borough"] == borough].iloc[0]
    nivel = row["nivel_demanda"]
    color = COLOR[nivel]
    with cols[i]:
        st.markdown(
            f"""
            <div style="
                background: {color}22;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 16px;
                text-align: center;
            ">
                <div style="font-size: 14px; color: #888;">{borough}</div>
                <div style="font-size: 28px; font-weight: bold; color: {color};">
                    {nivel.upper()}
                </div>
                <div style="font-size: 13px; color: #666;">
                    ~{row['solicitudes_estimadas']:,} solicitudes
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
st.header("📈 Historial de solicitudes")

col_filtro1, col_filtro2 = st.columns([1, 2])
with col_filtro1:
    boroughs_sel = st.multiselect(
        "Boroughs",
        BOROUGHS,
        default=BOROUGHS,
    )
with col_filtro2:
    anios = sorted(sem["semana"].dt.year.unique())
    rango_anios = st.slider(
        "Rango de años",
        min_value=int(min(anios)),
        max_value=int(max(anios)),
        value=(int(min(anios)), int(max(anios))),
    )

# Filtrar
mask = (
    sem["borough"].isin(boroughs_sel)
    & (sem["semana"].dt.year >= rango_anios[0])
    & (sem["semana"].dt.year <= rango_anios[1])
)
datos_filtrados = sem[mask].copy()

# ---------------------------------------------------------------------------
# Serie temporal
# ---------------------------------------------------------------------------
if not datos_filtrados.empty:
    fig_serie = px.line(
        datos_filtrados,
        x="semana",
        y="n",
        color="borough",
        labels={"n": "Solicitudes semanales", "semana": "Semana", "borough": "Borough"},
        title="Solicitudes semanales por borough",
    )
    fig_serie.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
    )
    st.plotly_chart(fig_serie, use_container_width=True)

# ---------------------------------------------------------------------------
# Distribución de niveles de demanda
# ---------------------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Distribución de niveles por borough")
    if not datos_filtrados.empty:
        dist = (
            datos_filtrados.groupby(["borough", "nivel"])
            .size()
            .reset_index(name="semanas")
        )
        fig_dist = px.bar(
            dist,
            x="borough",
            y="semanas",
            color="nivel",
            color_discrete_map=COLOR,
            barmode="group",
            labels={"semanas": "Número de semanas", "borough": "Borough", "nivel": "Nivel"},
        )
        fig_dist.update_layout(height=400)
        st.plotly_chart(fig_dist, use_container_width=True)

with col_b:
    st.subheader("Umbrales por borough")
    umb_df = pd.DataFrame(umbrales).T.reset_index()
    umb_df.columns = ["Borough", "P33 (bajo/medio)", "P66 (medio/alto)"]
    umb_df["P33 (bajo/medio)"] = umb_df["P33 (bajo/medio)"].apply(lambda x: f"{x:,.0f}")
    umb_df["P66 (medio/alto)"] = umb_df["P66 (medio/alto)"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(umb_df, use_container_width=True, hide_index=True)

    st.markdown("""
    **Criterio de clasificación:**
    - **Bajo:** solicitudes ≤ percentil 33
    - **Medio:** entre percentil 33 y 66
    - **Alto:** solicitudes > percentil 66

    *Umbrales calculados sobre las 208 semanas (2022–2025) por borough.*
    """)

st.divider()

# ---------------------------------------------------------------------------
# Consulta individual por borough
# ---------------------------------------------------------------------------
st.header("🔍 Consultar borough")

col_q1, col_q2 = st.columns([1, 2])
with col_q1:
    borough_sel = st.selectbox("Selecciona un borough", BOROUGHS)

serie_borough = sem[sem["borough"] == borough_sel].sort_values("semana").copy()
pred_borough = pred[pred["borough"] == borough_sel].iloc[0]

with col_q2:
    st.metric(
        label=f"Predicción próxima semana — {borough_sel}",
        value=pred_borough["nivel_demanda"].upper(),
        delta=f"~{pred_borough['solicitudes_estimadas']:,} solicitudes esperadas",
    )

# Serie individual con colores por nivel
fig_ind = go.Figure()

for nivel, color in COLOR.items():
    sub = serie_borough[serie_borough["nivel"] == nivel]
    fig_ind.add_trace(go.Scatter(
        x=sub["semana"],
        y=sub["n"],
        mode="markers",
        name=nivel.capitalize(),
        marker=dict(color=color, size=6),
        hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} solicitudes<extra></extra>",
    ))

# Línea de tendencia
fig_ind.add_trace(go.Scatter(
    x=serie_borough["semana"],
    y=serie_borough["n"],
    mode="lines",
    name="Tendencia",
    line=dict(color="#999", width=1),
    hoverinfo="skip",
))

# Umbrales
fig_ind.add_hline(
    y=umbrales[borough_sel]["p33"],
    line_dash="dash",
    line_color=COLOR["bajo"],
    annotation_text="P33",
)
fig_ind.add_hline(
    y=umbrales[borough_sel]["p66"],
    line_dash="dash",
    line_color=COLOR["alto"],
    annotation_text="P66",
)

fig_ind.update_layout(
    title=f"Serie semanal — {borough_sel}",
    xaxis_title="Semana",
    yaxis_title="Solicitudes",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_ind, use_container_width=True)

# Estadísticas del borough
col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.metric("Promedio semanal", f"{serie_borough['n'].mean():,.0f}")
with col_s2:
    st.metric("Máximo", f"{serie_borough['n'].max():,.0f}")
with col_s3:
    st.metric("Mínimo", f"{serie_borough['n'].min():,.0f}")
with col_s4:
    pct_alto = (serie_borough["nivel"] == "alto").mean() * 100
    st.metric("% semanas altas", f"{pct_alto:.0f}%")

st.divider()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.caption(
    "Proyecto MIAD — Despliegue de Soluciones Analíticas · "
    "Laura Vásquez, Ruby Alvarez, Jorge Lopera · "
    "Datos: NYC Open Data 311 Service Requests (2022–2025)"
)
st.caption(
    "⚠️ Las predicciones actuales usan un modelo dummy (promedio móvil 4 semanas). "
    "Se reemplazarán por el modelo supervisado entrenado en MLflow."
)
