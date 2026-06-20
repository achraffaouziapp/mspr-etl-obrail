import streamlit as st

from visualisation import (
    test_database_connection,
    format_int,
    format_float,
    load_global_kpis,
    load_train_type_options,
    load_source_options,
    load_source_stats,
    load_train_type_stats,
    load_stations_by_country,
    load_top_operators,
    load_source_train_type_counts,
    load_quality_stats,
    load_quality_by_source,
    load_quality_by_source_and_type,
    load_anomalies,
    load_trips,
    load_route_network,
    create_horizontal_bar_chart,
    create_sunburst_chart,
    create_heatmap_counts,
    create_quality_heatmap,
    create_radar_chart,
    create_network_graph,
)


# ============================================================
# Configuration Streamlit
# ============================================================

st.set_page_config(
    page_title="ObRail Europe - Dashboard Pro",
    page_icon="🚆",
    layout="wide"
)


# ============================================================
# Style professionnel
# ============================================================

st.markdown(
    """
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1450px;
        }

        .dashboard-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.2rem;
        }

        .dashboard-subtitle {
            font-size: 1rem;
            color: #64748B;
            margin-bottom: 2rem;
        }

        .section-title {
            font-size: 1.55rem;
            font-weight: 750;
            color: #0F172A;
            margin-top: 1.2rem;
            margin-bottom: 0.2rem;
        }

        .section-subtitle {
            font-size: 0.95rem;
            color: #64748B;
            margin-bottom: 1.2rem;
        }

        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            padding: 18px 20px;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        }

        .chart-card {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            padding: 22px 22px 10px 22px;
            margin-top: 24px;
            margin-bottom: 34px;
            box-shadow: 0 8px 26px rgba(15, 23, 42, 0.07);
        }

        .table-card {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            padding: 22px;
            margin-top: 24px;
            margin-bottom: 34px;
            box-shadow: 0 8px 26px rgba(15, 23, 42, 0.07);
        }

        .explanation-box {
            background-color: #F8FAFC;
            border-left: 5px solid #0284C7;
            border-radius: 14px;
            padding: 18px 22px;
            margin-top: 8px;
            margin-bottom: 34px;
            color: #334155;
            font-size: 0.96rem;
            line-height: 1.55;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            margin-top: 22px;
            margin-bottom: 18px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 10px 18px;
            background-color: #F8FAFC;
            border: 1px solid #E5E7EB;
        }

        .stTabs [aria-selected="true"] {
            background-color: #E0F2FE !important;
            color: #0369A1 !important;
            border: 1px solid #7DD3FC !important;
        }

        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


def section(title: str, subtitle: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart_block(fig):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


def table_block(df):
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


def explanation_block(text: str):
    st.markdown(f'<div class="explanation-box">{text}</div>', unsafe_allow_html=True)


st.markdown(
    '<div class="dashboard-title">🚆 ObRail Europe — Dashboard analytique</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="dashboard-subtitle">Pilotage visuel de la qualité, du réseau et des volumes ferroviaires chargés dans PostgreSQL.</div>',
    unsafe_allow_html=True
)


# ============================================================
# Connexion DB
# ============================================================

try:
    test_database_connection()
    st.sidebar.success("PostgreSQL connecté")
except Exception as error:
    st.error("Impossible de se connecter à PostgreSQL.")
    st.code(str(error))
    st.stop()


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("Filtres")

train_types_df = load_train_type_options()
train_type_options = ["Tous"] + train_types_df["type_name"].tolist()
selected_train_type = st.sidebar.selectbox("Type de train", train_type_options)

sources_df = load_source_options()
source_options = ["Toutes"] + sources_df["source_name"].tolist()
selected_source_name = st.sidebar.selectbox("Source de données", source_options)

selected_source_id = None
if selected_source_name != "Toutes":
    selected_source_id = int(
        sources_df.loc[
            sources_df["source_name"] == selected_source_name,
            "data_source_id"
        ].iloc[0]
    )

anomaly_limit = st.sidebar.slider(
    "Nombre d'anomalies affichées",
    min_value=10,
    max_value=300,
    value=100,
    step=10
)


# ============================================================
# KPI
# ============================================================

kpi_df = load_global_kpis()
kpi = kpi_df.iloc[0]

section(
    "Indicateurs globaux",
    "Vue synthétique des volumes chargés et du niveau de qualité global."
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Trajets", format_int(kpi["total_trips"]))
with col2:
    st.metric("Gares", format_int(kpi["total_stations"]))
with col3:
    st.metric("Routes", format_int(kpi["total_routes"]))
with col4:
    st.metric("Arrêts", format_int(kpi["total_trip_stops"]))

st.markdown("<br>", unsafe_allow_html=True)

col5, col6, col7 = st.columns(3)
with col5:
    st.metric("Anomalies", format_int(kpi["total_anomalies"]))
with col6:
    st.metric("Score qualité moyen", format_float(kpi["avg_quality_score"]))
with col7:
    st.metric("Complétude coordonnées", f"{format_float(kpi['coordinate_completion_rate'])} %")


# ============================================================
# Onglets
# ============================================================

tab_exec, tab_transport, tab_quality, tab_network = st.tabs([
    "Vue exécutive",
    "Analyse transport",
    "Analyse qualité",
    "Réseau ferroviaire"
])


# ============================================================
# 1. Vue exécutive
# ============================================================

with tab_exec:
    section(
        "Vue exécutive",
        "Les graphiques présentent les volumes principaux du projet avec un affichage simple et lisible."
    )

    source_stats_df = load_source_stats()
    stations_country_df = load_stations_by_country()
    train_type_stats_df = load_train_type_stats()

    # Diagramme simple, non logarithmique : volume de trajets par source.
    fig_sources = create_horizontal_bar_chart(
        source_stats_df,
        x_col="total_trips",
        y_col="source_name",
        title="Volume de trajets par source de données",
        height=560
    )
    chart_block(fig_sources)

    explanation_block(
        "Ce graphique compare les volumes réellement chargés par source. "
        "La source SNCF GTFS contient un volume beaucoup plus important car elle couvre "
        "un périmètre opérationnel large, tandis que Back-on-Track est une source spécialisée "
        "sur les trains de nuit. Cette différence est conservée car elle reflète les données réelles."
    )

    # Graphique séparé jour / nuit.
    fig_train_types = create_horizontal_bar_chart(
        train_type_stats_df,
        x_col="total_trips",
        y_col="type_name",
        title="Volume de trajets par type de train",
        height=460
    )
    chart_block(fig_train_types)

    explanation_block(
        "Le graphique jour / nuit est séparé du graphique des sources afin de ne pas confondre "
        "le volume d'une source de données avec la catégorie métier du trajet."
    )

    fig_countries = create_horizontal_bar_chart(
        stations_country_df.head(15),
        x_col="total_stations",
        y_col="country_name",
        title="Top 15 pays par nombre de gares",
        height=680
    )
    chart_block(fig_countries)


# ============================================================
# 2. Analyse transport
# ============================================================

with tab_transport:
    section(
        "Analyse transport",
        "Lecture des volumes par opérateur, par source et par type de train."
    )

    operators_df = load_top_operators(limit=15)
    counts_df = load_source_train_type_counts()

    fig_operators = create_horizontal_bar_chart(
        operators_df,
        x_col="total_trips",
        y_col="operator_name",
        title="Top opérateurs par nombre de trajets",
        height=700
    )
    chart_block(fig_operators)

    fig_sunburst = create_sunburst_chart(counts_df, height=720)
    chart_block(fig_sunburst)

    fig_heatmap_counts = create_heatmap_counts(counts_df, height=580)
    chart_block(fig_heatmap_counts)


# ============================================================
# 3. Analyse qualité
# ============================================================

with tab_quality:
    section(
        "Analyse qualité",
        "Contrôle visuel du score qualité, des valeurs manquantes, des erreurs horaires et des doublons."
    )

    quality_stats_df = load_quality_stats()
    table_block(quality_stats_df)

    quality_source_df = load_quality_by_source()
    quality_source_type_df = load_quality_by_source_and_type()

    fig_radar = create_radar_chart(quality_source_df, height=740)
    chart_block(fig_radar)

    fig_quality_heatmap = create_quality_heatmap(quality_source_type_df, height=580)
    chart_block(fig_quality_heatmap)

    st.subheader("Détail des anomalies")

    anomalies_df = load_anomalies(
        selected_train_type=selected_train_type,
        selected_source_id=selected_source_id,
        limit=anomaly_limit
    )

    if anomalies_df.empty:
        st.success("Aucune anomalie trouvée avec les filtres sélectionnés.")
    else:
        table_block(anomalies_df)
        st.download_button(
            label="Télécharger les anomalies",
            data=anomalies_df.to_csv(index=False).encode("utf-8"),
            file_name="quality_anomalies.csv",
            mime="text/csv"
        )


# ============================================================
# 4. Réseau ferroviaire
# ============================================================

with tab_network:
    section(
        "Réseau ferroviaire",
        "Visualisation des connexions les plus fréquentes entre villes."
    )

    network_df = load_route_network(limit=25)
    fig_network = create_network_graph(network_df, height=780)
    chart_block(fig_network)

    st.subheader("Exploration des trajets")

    col_filter_1, col_filter_2 = st.columns(2)

    with col_filter_1:
        departure_city = st.text_input("Ville de départ contient", value="")

    with col_filter_2:
        arrival_city = st.text_input("Ville d'arrivée contient", value="")

    trip_limit = st.slider(
        "Nombre de trajets affichés",
        min_value=10,
        max_value=300,
        value=100,
        step=10
    )

    trips_df = load_trips(
        selected_train_type=selected_train_type,
        selected_source_id=selected_source_id,
        departure_city=departure_city,
        arrival_city=arrival_city,
        limit=trip_limit
    )

    if trips_df.empty:
        st.warning("Aucun trajet trouvé avec les filtres sélectionnés.")
    else:
        table_block(trips_df)
        st.download_button(
            label="Télécharger les trajets",
            data=trips_df.to_csv(index=False).encode("utf-8"),
            file_name="trips_filtered.csv",
            mime="text/csv"
        )
