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
    load_trips,
    load_route_network,
    create_horizontal_bar_chart,
    create_sunburst_chart,
    create_network_graph,
)


# Configure la page Streamlit avant d'afficher le contenu.
# Le mode wide donne plus d'espace aux graphiques et rend le dashboard plus lisible.
st.set_page_config(
    page_title="ObRail Europe - Dashboard Pro",
    page_icon="🚆",
    layout="wide"
)


# Style CSS du dashboard.
# Ce bloc personnalise l'apparence générale : cartes, titres, onglets, métriques et encadrés explicatifs.
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
            border-bottom: none !important;
            box-shadow: none !important;
        }

        .stTabs [aria-selected="true"] {
            background-color: #E0F2FE !important;
            color: #0369A1 !important;
            border: 1px solid #7DD3FC !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            display: none !important;
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
    """
    Affiche un titre de section avec un sous-titre optionnel.

    Cette fonction évite de répéter le même HTML à chaque nouvelle partie du dashboard.
    """
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart_block(fig):
    """
    Affiche un graphique Plotly dans une carte visuelle.

    La carte ajoute de l'espace, une bordure et une ombre pour donner un rendu plus professionnel.
    """
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


def table_block(df):
    """
    Affiche un tableau dans une carte visuelle.

    Cette fonction est utilisée pour présenter les données détaillées de manière lisible.
    """
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


def explanation_block(text: str):
    """
    Affiche un encadré explicatif sous une visualisation.

    Ces textes permettent à un lecteur non technique de comprendre le sens du graphique.
    """
    st.markdown(f'<div class="explanation-box">{text}</div>', unsafe_allow_html=True)


# En-tête principal du dashboard.
st.markdown(
    '<div class="dashboard-title">🚆 ObRail Europe — Dashboard analytique</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="dashboard-subtitle">Pilotage visuel de la qualité, du réseau et des volumes ferroviaires chargés dans PostgreSQL.</div>',
    unsafe_allow_html=True
)


# Vérifie dès le démarrage que le dashboard peut communiquer avec PostgreSQL.
# Si la connexion échoue, l'application s'arrête pour éviter d'afficher des graphiques vides.
try:
    test_database_connection()
    st.sidebar.success("PostgreSQL connecté")
except Exception as error:
    st.error("Impossible de se connecter à PostgreSQL.")
    st.code(str(error))
    st.stop()


# Barre latérale réservée aux filtres d'exploration des trajets.
# Ces filtres ne changent pas les graphiques globaux, ils s'appliquent uniquement au tableau de la page Réseau.
st.sidebar.title("Filtres exploration trajets")

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

st.sidebar.info(
    "Ces filtres s'appliquent uniquement à la table d'exploration des trajets "
    "dans la page Réseau ferroviaire."
)


# Charge les indicateurs globaux affichés en haut du dashboard.
# Ces métriques donnent une vision rapide du volume total des données.
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


# Organisation du dashboard en trois pages principales.
tab_exec, tab_transport, tab_network = st.tabs([
    "Vue exécutive",
    "Analyse transport",
    "Réseau ferroviaire"
])


with tab_exec:
    section(
        "Vue exécutive",
        "Les graphiques présentent les volumes principaux du projet avec un affichage simple et lisible."
    )

    source_stats_df = load_source_stats()
    stations_country_df = load_stations_by_country()
    train_type_stats_df = load_train_type_stats()

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


with tab_transport:
    section(
        "Analyse transport",
        "Cette page analyse les volumes de trajets selon les opérateurs, les sources de données et les types de train."
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

    explanation_block(
        "Ce graphique présente les opérateurs ferroviaires les plus représentés dans l'entrepôt de données. "
        "Il permet d'identifier rapidement quels opérateurs contribuent le plus au volume total de trajets. "
        "Une forte présence d'un opérateur peut s'expliquer par le périmètre de la source utilisée, par exemple "
        "une source GTFS nationale contenant un grand nombre de services."
    )

    fig_sunburst = create_sunburst_chart(
        counts_df,
        height=720
    )
    chart_block(fig_sunburst)

    explanation_block(
        "Ce diagramme hiérarchique se lit de l'intérieur vers l'extérieur. "
        "Le premier niveau représente les sources de données, par exemple SNCF GTFS, Back-on-Track ou European Sleeper. "
        "Le second niveau représente le type de train associé à chaque source : day ou night. "
        "Chaque couleur correspond à une branche de la hiérarchie, principalement une source de données. "
        "Les sous-segments de même couleur appartiennent à la même source. "
        "La taille de chaque segment est proportionnelle au nombre de trajets chargés dans la base."
    )

    explanation_block(
        "Le bleu correspond à SNCF GTFS, l'orange à Back-on-Track Night Train Data et le vert à European Sleeper Timetable. "
        "Le centre du diagramme représente les sources de données, tandis que l'anneau extérieur indique le type de train associé : day ou night. "
        "La taille de chaque segment est proportionnelle au nombre de trajets chargés dans PostgreSQL."
    )


with tab_network:
    section(
        "Réseau ferroviaire",
        "Visualisation des connexions les plus fréquentes entre villes."
    )

    network_df = load_route_network(limit=25)
    fig_network = create_network_graph(network_df, height=780)
    chart_block(fig_network)

    explanation_block(
        "Ce graphe représente les principales connexions ferroviaires entre villes. "
        "Chaque nœud correspond à une ville et chaque lien représente une relation de trajet entre deux villes. "
        "Les connexions affichées sont limitées aux trajets les plus fréquents afin de garder une visualisation lisible. "
        "Ce graphique permet d'identifier rapidement les villes les plus connectées dans le réseau chargé."
    )

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

        explanation_block(
            "Ce tableau permet d'explorer les trajets ferroviaires présents dans la base. "
            "Les filtres de la barre latérale peuvent être utilisés pour limiter l'affichage "
            "par type de train ou par source de données. Les champs de recherche permettent aussi "
            "de filtrer les trajets selon la ville de départ ou la ville d'arrivée."
        )

        st.download_button(
            label="Télécharger les trajets",
            data=trips_df.to_csv(index=False).encode("utf-8"),
            file_name="trips_filtered.csv",
            mime="text/csv"
        )
