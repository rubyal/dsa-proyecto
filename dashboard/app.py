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
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RidgeClassifier

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NYC 311 · Predicción de demanda",
    page_icon="🏙️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Estilos CSS personalizados
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Header bar */
    .header-bar {
        background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .header-bar h1 {
        margin: 0; font-size: 28px; font-weight: 700; color: white;
    }
    .header-bar .subtitle {
        font-size: 14px; opacity: 0.85; margin-top: 4px;
    }

    /* KPI principal */
    .kpi-main {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    .kpi-main .number {
        font-size: 36px; font-weight: 700; color: #1a237e;
    }
    .kpi-main .label {
        font-size: 13px; color: #666; margin-top: 4px;
    }

    /* Tarjetas de predicción por borough */
    .pred-card {
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .pred-card .borough-name {
        font-size: 13px; color: #555; font-weight: 600;
        margin-bottom: 6px;
    }
    .pred-card .nivel {
        font-size: 22px; font-weight: 700;
    }
    .pred-card .detalle {
        font-size: 12px; color: #777; margin-top: 4px;
    }

    /* Tabla de predicción por categoría */
    .tabla-pred {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        font-size: 14px;
    }
    .tabla-pred th {
        background: #1a237e;
        color: white;
        padding: 10px 12px;
        text-align: center;
        font-weight: 600;
    }
    .tabla-pred td {
        padding: 8px 12px;
        text-align: center;
        border-bottom: 1px solid #eee;
    }
    .tabla-pred tr:nth-child(even) { background: #fafafa; }
    .tabla-pred tr:hover { background: #f0f4ff; }

    .badge-baja {
        background: #e3f2fd; color: #1565c0;
        padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 13px;
    }
    .badge-media {
        background: #fff8e1; color: #f57f17;
        padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 13px;
    }
    .badge-alta {
        background: #ffebee; color: #c62828;
        padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 13px;
    }

    /* Ocultar el menú hamburguesa de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
COLOR = {"Baja": "#2196F3", "Media": "#FFC107", "Alta": "#F44336"}
BOROUGHS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]

# Coordenadas centrales de cada borough para el mapa
BOROUGH_COORDS = {
    "BRONX":         {"lat": 40.8448, "lon": -73.8648},
    "BROOKLYN":      {"lat": 40.6782, "lon": -73.9442},
    "MANHATTAN":     {"lat": 40.7831, "lon": -73.9712},
    "QUEENS":        {"lat": 40.7282, "lon": -73.7949},
    "STATEN ISLAND": {"lat": 40.5795, "lon": -74.1502},
}

# Categorías principales (como en el mockup)
CATEGORIAS_PRINCIPALES = {
    "Ruido": ["Noise - Residential", "Noise - Street/Sidewalk",
              "Noise - Commercial", "Noise", "Noise - Vehicle",
              "Noise - Helicopter", "Noise - Park"],
    "Basuras y limpieza": ["UNSANITARY CONDITION", "Dirty Condition",
                           "Sanitation Condition", "Illegal Dumping",
                           "Residential Disposal Complaint", "Rodent"],
    "Calefacción / Agua caliente": ["HEAT/HOT WATER", "HEATING",
                                     "PLUMBING", "Water System",
                                     "General Construction/Plumbing",
                                     "PAINT/PLASTER"],
    "Calles y vías": ["Illegal Parking", "Blocked Driveway",
                      "Street Condition", "Street Light Condition",
                      "Traffic Signal Condition", "Sidewalk Condition",
                      "Derelict Vehicles", "Abandoned Vehicle"],
}

VARIABLES = [
    "borough", "mes", "semana_anio",
    "lag_1", "lag_2", "lag_4", "lag_52",
    "media_movil_4", "media_movil_12",
    "media_movil_52", "std_movil_4",
]
OBJETIVO = "nivel_demanda"

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def _buscar_raiz_repo():
    repo = Path(".").resolve()
    while not (repo / ".git").exists() and repo != repo.parent:
        repo = repo.parent
    return repo


def _buscar_parquet(nombre, subcarpeta):
    repo = _buscar_raiz_repo()
    rutas = [
        repo / "data" / subcarpeta / nombre,
        Path(f"data/{subcarpeta}/{nombre}"),
        Path(f"../data/{subcarpeta}/{nombre}"),
    ]
    for ruta in rutas:
        if ruta.exists():
            return ruta
    return None


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data
def cargar_datos_diarios():
    """Carga el parquet diario y construye la serie semanal por borough."""
    ruta = _buscar_parquet("nyc311_diario_borough_tipo.parquet", "raw")
    if ruta is None:
        st.error(
            "No se encontró `nyc311_diario_borough_tipo.parquet`. "
            "Ejecuta `dvc pull` primero."
        )
        st.stop()

    df = pd.read_parquet(ruta)
    df["dia"] = pd.to_datetime(df["dia"])
    return df


@st.cache_data
def construir_serie_semanal(df):
    """Construye la serie semanal agregada por borough."""
    d = df[df["borough"] != "Unspecified"].copy()
    d["semana"] = d["dia"].dt.to_period("W-SUN").dt.start_time

    ini, fin = df["dia"].min(), df["dia"].max()
    semanas = d["semana"].drop_duplicates().sort_values()
    completas = semanas[
        (semanas >= ini) & (semanas + pd.Timedelta(days=6) <= fin)
    ]

    sem = (
        d[d["semana"].isin(completas)]
        .groupby(["semana", "borough"], as_index=False)["n"]
        .sum()
        .sort_values(["borough", "semana"])
    )
    return sem


def construir_serie_por_categoria(df):
    """Construye serie semanal por borough y categoría principal."""
    d = df[df["borough"] != "Unspecified"].copy()
    d["semana"] = d["dia"].dt.to_period("W-SUN").dt.start_time

    # Mapear complaint_type a categoría principal (case-insensitive)
    tipo_a_cat = {}
    for cat, tipos in CATEGORIAS_PRINCIPALES.items():
        for t in tipos:
            tipo_a_cat[t.upper()] = cat
    d["categoria"] = (
        d["complaint_type"]
        .str.upper()
        .map(tipo_a_cat)
        .fillna("Otros")
    )

    sem_cat = (
        d.groupby(["semana", "borough", "categoria"], as_index=False)["n"]
        .sum()
        .sort_values(["borough", "semana"])
    )
    return sem_cat


@st.cache_data
def cargar_datos_modelado():
    """Carga el dataset de modelado semanal."""
    ruta = _buscar_parquet("dataset_modelado_semanal.parquet", "processed")
    if ruta is None:
        st.error(
            "No se encontró `dataset_modelado_semanal.parquet`. "
            "Ejecuta `dvc pull` primero."
        )
        st.stop()

    datos = pd.read_parquet(ruta)
    datos["semana"] = pd.to_datetime(datos["semana"])
    return datos


@st.cache_data
def calcular_umbrales(sem):
    """Calcula p33/p66 globales por borough."""
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
        return "Baja"
    elif valor <= p66:
        return "Media"
    else:
        return "Alta"


def badge_html(nivel):
    """Retorna HTML con badge coloreado según nivel."""
    clase = f"badge-{nivel.lower()}"
    return f'<span class="{clase}">{nivel}</span>'


# ---------------------------------------------------------------------------
# Modelo: RidgeClassifier alpha=0.1
# ---------------------------------------------------------------------------
@st.cache_resource
def entrenar_modelo(_datos_modelado):
    """Entrena el RidgeClassifier alpha=0.1 (notebook 06 de Jorge)."""
    numericas = [c for c in VARIABLES if c != "borough"]

    preprocesador = ColumnTransformer([
        ("categoria",
         OneHotEncoder(handle_unknown="ignore", sparse_output=False),
         ["borough"]),
        ("numericas", StandardScaler(), numericas),
    ])

    pipeline = Pipeline([
        ("preprocesamiento", preprocesador),
        ("clasificador", RidgeClassifier(alpha=0.1)),
    ])

    train = _datos_modelado[
        _datos_modelado["semana"].dt.year.isin([2023, 2024])
    ].copy()

    pipeline.fit(train[VARIABLES], train[OBJETIVO])
    return pipeline


def predecir_proxima_semana(modelo, datos_modelado):
    """Genera predicción para la próxima semana."""
    ultima_semana = datos_modelado["semana"].max()
    proxima = ultima_semana + pd.Timedelta(weeks=1)

    predicciones = []
    for borough in BOROUGHS:
        serie_b = datos_modelado[
            datos_modelado["borough"] == borough
        ].sort_values("semana")

        if serie_b.empty:
            continue

        ultima = serie_b.iloc[-1]
        proxima_dt = proxima
        features = {
            "borough": borough,
            "mes": proxima_dt.month,
            "semana_anio": proxima_dt.isocalendar()[1],
            "lag_1": ultima["total_solicitudes"],
            "lag_2": ultima["lag_1"],
            "lag_4": ultima["lag_2"],
            "lag_52": ultima["lag_52"],
            "media_movil_4": (
                ultima["total_solicitudes"] * 0.25
                + ultima["lag_1"] * 0.25
                + ultima["lag_2"] * 0.25
                + ultima["media_movil_4"] * 0.25
            ),
            "media_movil_12": ultima["media_movil_12"],
            "media_movil_52": ultima["media_movil_52"],
            "std_movil_4": ultima["std_movil_4"],
        }

        features_df = pd.DataFrame([features])
        nivel = modelo.predict(features_df[VARIABLES])[0]

        predicciones.append({
            "borough": borough,
            "semana": proxima,
            "solicitudes_estimadas": int(ultima["total_solicitudes"]),
            "nivel_demanda": nivel,
        })

    return pd.DataFrame(predicciones)


def predecir_por_categoria(sem_cat, umbrales_cat):
    """Genera predicción por categoría y borough (últimas 4 semanas)."""
    resultados = []
    for borough in BOROUGHS:
        for cat in CATEGORIAS_PRINCIPALES:
            datos_bc = sem_cat[
                (sem_cat["borough"] == borough)
                & (sem_cat["categoria"] == cat)
            ].sort_values("semana")

            if datos_bc.empty:
                resultados.append({
                    "borough": borough,
                    "categoria": cat,
                    "nivel": "Media",
                })
                continue

            media_4 = datos_bc.tail(4)["n"].mean()
            key = (borough, cat)
            if key in umbrales_cat:
                nivel = etiquetar(
                    media_4,
                    umbrales_cat[key]["p33"],
                    umbrales_cat[key]["p66"],
                )
            else:
                nivel = "Media"

            resultados.append({
                "borough": borough,
                "categoria": cat,
                "nivel": nivel,
            })

    return pd.DataFrame(resultados)


@st.cache_data
def calcular_umbrales_categoria(sem_cat):
    """Calcula p33/p66 por (borough, categoria)."""
    umbrales = {}
    for borough in BOROUGHS:
        for cat in CATEGORIAS_PRINCIPALES:
            serie = sem_cat[
                (sem_cat["borough"] == borough)
                & (sem_cat["categoria"] == cat)
            ]["n"]
            if len(serie) > 5:
                umbrales[(borough, cat)] = {
                    "p33": serie.quantile(0.33),
                    "p66": serie.quantile(0.66),
                }
    return umbrales


# ---------------------------------------------------------------------------
# Cargar todo
# ---------------------------------------------------------------------------
df_diario = cargar_datos_diarios()
sem = construir_serie_semanal(df_diario)
sem_cat = construir_serie_por_categoria(df_diario)
datos_modelado = cargar_datos_modelado()
umbrales = calcular_umbrales(sem)
umbrales_cat = calcular_umbrales_categoria(sem_cat)
modelo = entrenar_modelo(datos_modelado)

# Etiquetar serie histórica
sem["nivel"] = sem.apply(
    lambda r: etiquetar(
        r["n"], umbrales[r["borough"]]["p33"], umbrales[r["borough"]]["p66"]
    ),
    axis=1,
)

pred = predecir_proxima_semana(modelo, datos_modelado)
pred_cat = predecir_por_categoria(sem_cat, umbrales_cat)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    pagina = st.radio(
        "Navegación",
        ["🏠 Inicio", "📊 Análisis"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("### ℹ️ Modelo")
    st.markdown("""
    **RidgeClassifier** (α=0.1)

    Entrenamiento: 2023–2024

    **Métricas en 2025:**
    - Accuracy: 56.9%
    - F1-macro: 0.54
    - Recall Alta: 75.7%
    """)

    st.divider()
    st.caption(
        "MIAD · Despliegue de Soluciones Analíticas\n\n"
        "Laura Vásquez · Ruby Alvarez · Jorge Lopera"
    )

# =========================================================================
# PÁGINA: INICIO
# =========================================================================
if "Inicio" in pagina:

    # --- Header ---
    st.markdown("""
    <div class="header-bar">
        <h1>🏙️ NYC 311 — Nivel de demanda de solicitudes</h1>
        <div class="subtitle">
            Predicción semanal por borough · Datos 2022–2025
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- KPI principal + selector de semana ---
    col_kpi, col_semana = st.columns([1, 2])

    with col_kpi:
        total_solicitudes = int(
            df_diario[df_diario["borough"] != "Unspecified"]["n"].sum()
        )
        st.markdown(f"""
        <div class="kpi-main">
            <div class="number">{total_solicitudes:,}</div>
            <div class="label">Número total de solicitudes (2022–2025)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_semana:
        proxima_fecha = pred["semana"].iloc[0]
        st.info(
            f"📅 **Predicción para la semana del "
            f"{proxima_fecha.strftime('%d de %B de %Y')}** — "
            f"Modelo: RidgeClassifier α=0.1"
        )

        # Tarjetas de predicción por borough
        cols_pred = st.columns(5)
        for i, borough in enumerate(BOROUGHS):
            row = pred[pred["borough"] == borough].iloc[0]
            nivel = row["nivel_demanda"]
            color = COLOR[nivel]
            with cols_pred[i]:
                st.markdown(f"""
                <div class="pred-card" style="background: {color}15;
                    border-left: 4px solid {color};">
                    <div class="borough-name">{borough}</div>
                    <div class="nivel" style="color: {color};">{nivel}</div>
                    <div class="detalle">
                        ~{row['solicitudes_estimadas']:,} sol.
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # --- Filtro de categoría (fuera de columnas para compatibilidad) ---
    col_titulo1, col_titulo2 = st.columns([1, 1])
    with col_titulo1:
        st.subheader("Nivel de demanda predicho por borough")
    with col_titulo2:
        cat_sel = st.selectbox(
            "Tipo de solicitud",
            list(CATEGORIAS_PRINCIPALES.keys()),
            key="cat_inicio",
        )

    # --- Barras + Serie temporal ---
    col_mapa, col_serie = st.columns([1, 1])

    with col_mapa:

        # Construir datos para el mapa
        mapa_data = []
        for borough in BOROUGHS:
            row = pred[pred["borough"] == borough].iloc[0]
            nivel = row["nivel_demanda"]
            coords = BOROUGH_COORDS[borough]
            mapa_data.append({
                "borough": borough,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "nivel": nivel,
                "solicitudes": row["solicitudes_estimadas"],
            })
        mapa_df = pd.DataFrame(mapa_data)

        # Gráfico de barras horizontales con nivel predicho por borough
        fig_barras = go.Figure()
        for _, row_m in mapa_df.iterrows():
            fig_barras.add_trace(go.Bar(
                y=[row_m["borough"]],
                x=[row_m["solicitudes"]],
                orientation="h",
                marker_color=COLOR.get(row_m["nivel"], "#999"),
                name=row_m["nivel"],
                showlegend=False,
                text=f'{row_m["nivel"]} (~{row_m["solicitudes"]:,.0f})',
                textposition="inside",
                textfont=dict(color="white", size=13),
            ))
        # Leyenda manual (una entrada por nivel)
        for nivel, color in COLOR.items():
            fig_barras.add_trace(go.Bar(
                y=[None], x=[None], orientation="h",
                marker_color=color, name=nivel,
                showlegend=True,
            ))
        fig_barras.update_layout(
            height=350,
            margin=dict(l=0, r=10, t=10, b=0),
            xaxis_title="Solicitudes estimadas (próxima semana)",
            yaxis=dict(autorange="reversed"),
            legend=dict(
                orientation="h", yanchor="top", y=-0.15,
                xanchor="center", x=0.5, title="Nivel"
            ),
            barmode="stack",
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    with col_serie:
        # Serie mensual de la categoría seleccionada
        datos_cat = sem_cat[sem_cat["categoria"] == cat_sel].copy()
        if not datos_cat.empty:
            datos_cat["mes"] = datos_cat["semana"].dt.to_period("M").dt.to_timestamp()
            mensual = (
                datos_cat.groupby(["mes", "borough"], as_index=False)["n"]
                .sum()
            )

            fig_cat = px.line(
                mensual,
                x="mes",
                y="n",
                color="borough",
                labels={
                    "n": "Solicitudes",
                    "mes": "",
                    "borough": "Borough",
                },
            )
            fig_cat.update_layout(
                height=350,
                hovermode="x unified",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1
                ),
                margin=dict(t=10),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    st.divider()

    # --- Tabla de predicción por borough y categoría (como en el mockup) ---
    st.subheader(
        f"Predicción de la próxima semana: "
        f"{proxima_fecha.strftime('%d/%m/%Y')}"
    )

    categorias_cols = list(CATEGORIAS_PRINCIPALES.keys())

    # Construir tabla HTML
    header = "<tr><th>Borough</th>"
    for cat in categorias_cols:
        header += f"<th>{cat}</th>"
    header += "</tr>"

    rows_html = ""
    for borough in BOROUGHS:
        rows_html += f"<tr><td style='text-align:left; font-weight:600;'>{borough}</td>"
        for cat in categorias_cols:
            nivel_row = pred_cat[
                (pred_cat["borough"] == borough)
                & (pred_cat["categoria"] == cat)
            ]
            if not nivel_row.empty:
                nivel = nivel_row.iloc[0]["nivel"]
            else:
                nivel = "Media"
            rows_html += f"<td>{badge_html(nivel)}</td>"
        rows_html += "</tr>"

    st.markdown(
        f'<table class="tabla-pred">{header}{rows_html}</table>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Los niveles por categoría se estiman con el promedio móvil de "
        "las últimas 4 semanas vs. los percentiles 33/66 históricos "
        "de cada combinación borough-categoría."
    )

# =========================================================================
# PÁGINA: ANÁLISIS
# =========================================================================
elif "Análisis" in pagina:

    st.markdown("""
    <div class="header-bar">
        <h1>📊 Análisis histórico</h1>
        <div class="subtitle">
            Exploración de series temporales y distribución de niveles
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Filtros ---
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        boroughs_sel = st.multiselect(
            "Boroughs", BOROUGHS, default=BOROUGHS
        )
    with col_f2:
        anios = sorted(sem["semana"].dt.year.unique())
        rango_anios = st.slider(
            "Rango de años",
            min_value=int(min(anios)),
            max_value=int(max(anios)),
            value=(int(min(anios)), int(max(anios))),
        )

    mask = (
        sem["borough"].isin(boroughs_sel)
        & (sem["semana"].dt.year >= rango_anios[0])
        & (sem["semana"].dt.year <= rango_anios[1])
    )
    datos_filtrados = sem[mask].copy()

    # --- Serie temporal ---
    if not datos_filtrados.empty:
        fig_serie = px.line(
            datos_filtrados,
            x="semana",
            y="n",
            color="borough",
            labels={
                "n": "Solicitudes semanales",
                "semana": "Semana",
                "borough": "Borough",
            },
            title="Solicitudes semanales por borough",
        )
        fig_serie.update_layout(
            hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1
            ),
            height=450,
        )
        st.plotly_chart(fig_serie, use_container_width=True)

    # --- Distribución de niveles + umbrales ---
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
                labels={
                    "semanas": "Número de semanas",
                    "borough": "Borough",
                    "nivel": "Nivel",
                },
            )
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)

    with col_b:
        st.subheader("Umbrales por borough")
        umb_df = pd.DataFrame(umbrales).T.reset_index()
        umb_df.columns = ["Borough", "P33 (Baja/Media)", "P66 (Media/Alta)"]
        umb_df["P33 (Baja/Media)"] = umb_df["P33 (Baja/Media)"].apply(
            lambda x: f"{x:,.0f}"
        )
        umb_df["P66 (Media/Alta)"] = umb_df["P66 (Media/Alta)"].apply(
            lambda x: f"{x:,.0f}"
        )
        st.dataframe(umb_df, use_container_width=True, hide_index=True)

        st.markdown("""
        **Criterio de clasificación:**
        - **Baja:** solicitudes ≤ percentil 33
        - **Media:** entre percentil 33 y 66
        - **Alta:** solicitudes > percentil 66

        *Umbrales calculados sobre semanas completas (2022–2025)
        por borough.*
        """)

    st.divider()

    # --- Consulta individual ---
    st.subheader("🔍 Consultar borough")

    col_q1, col_q2 = st.columns([1, 2])
    with col_q1:
        borough_sel = st.selectbox("Selecciona un borough", BOROUGHS)

    serie_borough = (
        sem[sem["borough"] == borough_sel].sort_values("semana").copy()
    )
    pred_borough = pred[pred["borough"] == borough_sel].iloc[0]

    with col_q2:
        st.metric(
            label=f"Predicción próxima semana — {borough_sel}",
            value=pred_borough["nivel_demanda"],
            delta=(
                f"Última semana: "
                f"~{pred_borough['solicitudes_estimadas']:,} solicitudes"
            ),
        )

    # Serie individual con colores por nivel
    fig_ind = go.Figure()

    for nivel, color in COLOR.items():
        sub = serie_borough[serie_borough["nivel"] == nivel]
        fig_ind.add_trace(go.Scatter(
            x=sub["semana"],
            y=sub["n"],
            mode="markers",
            name=nivel,
            marker=dict(color=color, size=6),
            hovertemplate=(
                "%{x|%d %b %Y}<br>%{y:,.0f} solicitudes<extra></extra>"
            ),
        ))

    fig_ind.add_trace(go.Scatter(
        x=serie_borough["semana"],
        y=serie_borough["n"],
        mode="lines",
        name="Tendencia",
        line=dict(color="#999", width=1),
        hoverinfo="skip",
    ))

    fig_ind.add_hline(
        y=umbrales[borough_sel]["p33"],
        line_dash="dash",
        line_color=COLOR["Baja"],
        annotation_text="P33",
    )
    fig_ind.add_hline(
        y=umbrales[borough_sel]["p66"],
        line_dash="dash",
        line_color=COLOR["Alta"],
        annotation_text="P66",
    )

    fig_ind.update_layout(
        title=f"Serie semanal — {borough_sel}",
        xaxis_title="Semana",
        yaxis_title="Solicitudes",
        height=400,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1
        ),
    )
    st.plotly_chart(fig_ind, use_container_width=True)

    # Estadísticas
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Promedio semanal", f"{serie_borough['n'].mean():,.0f}")
    with col_s2:
        st.metric("Máximo", f"{serie_borough['n'].max():,.0f}")
    with col_s3:
        st.metric("Mínimo", f"{serie_borough['n'].min():,.0f}")
    with col_s4:
        pct_alto = (serie_borough["nivel"] == "Alta").mean() * 100
        st.metric("% semanas altas", f"{pct_alto:.0f}%")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Proyecto MIAD — Despliegue de Soluciones Analíticas · "
    "Laura Vásquez, Ruby Alvarez, Jorge Lopera · "
    "Datos: NYC Open Data 311 Service Requests (2022–2025) · "
    "Modelo: RidgeClassifier α=0.1 registrado en MLflow"
)