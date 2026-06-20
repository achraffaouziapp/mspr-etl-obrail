import os
from pathlib import Path
from typing import Optional

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# Configuration PostgreSQL
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "obrail"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query: str, params: tuple = ()) -> pd.DataFrame:
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=params)
    finally:
        connection.close()


# ============================================================
# Formatage
# ============================================================

def format_int(value) -> str:
    if pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(",", " ")


def format_float(value, digits: int = 2) -> str:
    if pd.isna(value):
        return "0.00"
    return f"{float(value):.{digits}f}"


def test_database_connection() -> bool:
    df = run_query("SELECT 1 AS status;")
    return not df.empty


# ============================================================
# Chargement des données
# ============================================================

def load_global_kpis() -> pd.DataFrame:
    query = """
        SELECT
            (SELECT COUNT(*) FROM trip) AS total_trips,
            (SELECT COUNT(*) FROM station) AS total_stations,
            (SELECT COUNT(*) FROM route) AS total_routes,
            (SELECT COUNT(*) FROM trip_stop) AS total_trip_stops,
            (
                SELECT COUNT(*)
                FROM quality_check
                WHERE has_missing_values = TRUE
                   OR has_time_error = TRUE
                   OR is_duplicate = TRUE
            ) AS total_anomalies,
            (
                SELECT ROUND(AVG(quality_score), 2)
                FROM quality_check
            ) AS avg_quality_score,
            (
                SELECT ROUND(
                    100.0 * SUM(
                        CASE
                            WHEN latitude IS NOT NULL
                             AND longitude IS NOT NULL
                            THEN 1 ELSE 0
                        END
                    ) / COUNT(*),
                    2
                )
                FROM station
            ) AS coordinate_completion_rate;
    """
    return run_query(query)


def load_train_type_options() -> pd.DataFrame:
    return run_query("""
        SELECT type_name
        FROM train_type
        ORDER BY type_name;
    """)


def load_source_options() -> pd.DataFrame:
    return run_query("""
        SELECT data_source_id, source_name
        FROM data_source
        ORDER BY data_source_id;
    """)


def load_source_stats() -> pd.DataFrame:
    return run_query("""
        SELECT
            ds.source_name,
            ds.source_format,
            COUNT(t.trip_id) AS total_trips
        FROM trip t
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        GROUP BY ds.source_name, ds.source_format
        ORDER BY total_trips DESC;
    """)


def load_train_type_stats() -> pd.DataFrame:
    return run_query("""
        SELECT
            tt.type_name,
            COUNT(t.trip_id) AS total_trips,
            ROUND(
                100.0 * COUNT(t.trip_id) / SUM(COUNT(t.trip_id)) OVER (),
                2
            ) AS percentage
        FROM trip t
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        GROUP BY tt.type_name
        ORDER BY total_trips DESC;
    """)


def load_stations_by_country() -> pd.DataFrame:
    return run_query("""
        SELECT
            c.country_name,
            c.country_code,
            COUNT(s.station_id) AS total_stations
        FROM station s
        JOIN city ci
            ON s.city_id = ci.city_id
        JOIN country c
            ON ci.country_id = c.country_id
        GROUP BY c.country_name, c.country_code
        ORDER BY total_stations DESC;
    """)


def load_top_operators(limit: int = 15) -> pd.DataFrame:
    return run_query("""
        SELECT
            o.operator_name,
            o.operator_code,
            COUNT(t.trip_id) AS total_trips
        FROM trip t
        JOIN route r
            ON t.route_id = r.route_id
        JOIN "operator" o
            ON r.operator_id = o.operator_id
        GROUP BY o.operator_name, o.operator_code
        ORDER BY total_trips DESC
        LIMIT %s;
    """, (limit,))


def load_source_train_type_counts() -> pd.DataFrame:
    return run_query("""
        SELECT
            ds.source_name,
            tt.type_name,
            COUNT(t.trip_id) AS total_trips
        FROM trip t
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        GROUP BY ds.source_name, tt.type_name
        ORDER BY ds.source_name, tt.type_name;
    """)


def load_quality_stats() -> pd.DataFrame:
    return run_query("""
        SELECT
            COUNT(*) AS total_checks,
            SUM(CASE WHEN has_missing_values THEN 1 ELSE 0 END) AS trips_with_missing_values,
            SUM(CASE WHEN has_time_error THEN 1 ELSE 0 END) AS trips_with_time_error,
            SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) AS duplicated_trips,
            ROUND(AVG(quality_score), 2) AS avg_quality_score,
            MIN(quality_score) AS min_quality_score,
            MAX(quality_score) AS max_quality_score
        FROM quality_check;
    """)


def load_quality_by_source() -> pd.DataFrame:
    return run_query("""
        SELECT
            ds.source_name,
            COUNT(t.trip_id) AS total_trips,
            ROUND(AVG(q.quality_score), 2) AS avg_quality_score,
            ROUND(100.0 * SUM(CASE WHEN q.has_missing_values THEN 1 ELSE 0 END) / COUNT(*), 2) AS missing_rate,
            ROUND(100.0 * SUM(CASE WHEN q.has_time_error THEN 1 ELSE 0 END) / COUNT(*), 2) AS time_error_rate,
            ROUND(100.0 * SUM(CASE WHEN q.is_duplicate THEN 1 ELSE 0 END) / COUNT(*), 2) AS duplicate_rate
        FROM trip t
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        JOIN quality_check q
            ON t.trip_id = q.trip_id
        GROUP BY ds.source_name
        ORDER BY ds.source_name;
    """)


def load_quality_by_source_and_type() -> pd.DataFrame:
    return run_query("""
        SELECT
            ds.source_name,
            tt.type_name,
            ROUND(AVG(q.quality_score), 2) AS avg_quality_score
        FROM trip t
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        JOIN quality_check q
            ON t.trip_id = q.trip_id
        GROUP BY ds.source_name, tt.type_name
        ORDER BY ds.source_name, tt.type_name;
    """)


def load_anomalies(selected_train_type: str = "Tous", selected_source_id: Optional[int] = None, limit: int = 100) -> pd.DataFrame:
    conditions = [
        """
        (
            q.has_missing_values = TRUE
            OR q.has_time_error = TRUE
            OR q.is_duplicate = TRUE
        )
        """
    ]
    params = []

    if selected_train_type != "Tous":
        conditions.append("LOWER(tt.type_name) = LOWER(%s)")
        params.append(selected_train_type)

    if selected_source_id is not None:
        conditions.append("ds.data_source_id = %s")
        params.append(selected_source_id)

    where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            q.quality_check_id,
            t.trip_id,
            t.trip_code,
            tt.type_name AS train_type,
            ds.source_name,
            q.has_missing_values,
            q.has_time_error,
            q.is_duplicate,
            q.quality_score,
            q.error_message,
            q.check_date
        FROM quality_check q
        JOIN trip t
            ON q.trip_id = t.trip_id
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        {where_clause}
        ORDER BY q.quality_score ASC, t.trip_id
        LIMIT %s;
    """

    params.append(limit)
    return run_query(query, tuple(params))


def load_trips(selected_train_type: str = "Tous", selected_source_id: Optional[int] = None, departure_city: str = "", arrival_city: str = "", limit: int = 100) -> pd.DataFrame:
    conditions = []
    params = []

    if selected_train_type != "Tous":
        conditions.append("LOWER(tt.type_name) = LOWER(%s)")
        params.append(selected_train_type)

    if selected_source_id is not None:
        conditions.append("ds.data_source_id = %s")
        params.append(selected_source_id)

    if departure_city.strip():
        conditions.append("LOWER(dep_city.city_name) LIKE LOWER(%s)")
        params.append(f"%{departure_city.strip()}%")

    if arrival_city.strip():
        conditions.append("LOWER(arr_city.city_name) LIKE LOWER(%s)")
        params.append(f"%{arrival_city.strip()}%")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            t.trip_id,
            t.trip_code,
            tt.type_name AS train_type,
            ds.source_name,
            dep_station.station_name AS departure_station,
            dep_city.city_name AS departure_city,
            arr_station.station_name AS arrival_station,
            arr_city.city_name AS arrival_city,
            o.operator_name,
            t.service_date,
            t.departure_time,
            t.arrival_time,
            t.duration_minutes,
            q.quality_score,
            q.error_message
        FROM trip t
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        JOIN route r
            ON t.route_id = r.route_id
        JOIN "operator" o
            ON r.operator_id = o.operator_id
        JOIN station dep_station
            ON r.departure_station_id = dep_station.station_id
        JOIN city dep_city
            ON dep_station.city_id = dep_city.city_id
        JOIN station arr_station
            ON r.arrival_station_id = arr_station.station_id
        JOIN city arr_city
            ON arr_station.city_id = arr_city.city_id
        LEFT JOIN quality_check q
            ON t.trip_id = q.trip_id
        {where_clause}
        ORDER BY t.trip_id
        LIMIT %s;
    """
    params.append(limit)
    return run_query(query, tuple(params))


def load_route_network(limit: int = 25) -> pd.DataFrame:
    return run_query("""
        SELECT
            dep_city.city_name AS source_city,
            arr_city.city_name AS target_city,
            COUNT(t.trip_id) AS total_trips
        FROM trip t
        JOIN route r
            ON t.route_id = r.route_id
        JOIN station dep_station
            ON r.departure_station_id = dep_station.station_id
        JOIN city dep_city
            ON dep_station.city_id = dep_city.city_id
        JOIN station arr_station
            ON r.arrival_station_id = arr_station.station_id
        JOIN city arr_city
            ON arr_station.city_id = arr_city.city_id
        GROUP BY dep_city.city_name, arr_city.city_name
        ORDER BY total_trips DESC
        LIMIT %s;
    """, (limit,))


# ============================================================
# Préparation + layout
# ============================================================

def prepare_numeric_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    df = df.copy()
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    return df


def apply_pro_layout(fig, height: int = 620):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=40, r=40, t=85, b=55),
        title=dict(x=0.02, xanchor="left", font=dict(size=22)),
        font=dict(size=13),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(font_size=13),
    )
    return fig


# ============================================================
# Visualisations Plotly
# ============================================================

def create_horizontal_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, height: int = 620):
    df = prepare_numeric_column(df, x_col)
    df = df.sort_values(x_col, ascending=True)

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        orientation="h",
        text=x_col,
        title=title,
        labels={x_col: "Volume", y_col: ""}
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", marker_line_width=0)
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F7")
    fig.update_yaxes(showgrid=False)
    return apply_pro_layout(fig, height=height)


def create_log_source_bar_chart(df: pd.DataFrame, height: int = 560):
    """
    Histogramme horizontal avec échelle logarithmique.
    Utile quand une source a un volume beaucoup plus élevé qu'une autre.
    """
    df = prepare_numeric_column(df, "total_trips")
    df = df.sort_values("total_trips", ascending=True)

    fig = px.bar(
        df,
        x="total_trips",
        y="source_name",
        orientation="h",
        text="total_trips",
        title="Histogramme horizontal logarithmique — trajets par source",
        labels={
            "total_trips": "Volume de trajets, échelle logarithmique",
            "source_name": "Source de données"
        },
        hover_data=["source_format"]
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", marker_line_width=0)
    fig.update_xaxes(type="log", showgrid=True, gridcolor="#EEF2F7")
    fig.update_yaxes(showgrid=False)
    return apply_pro_layout(fig, height=height)


def create_train_type_share_chart(df: pd.DataFrame, height: int = 560):
    """
    Graphique séparé jour / nuit avec volume et pourcentage.
    """
    df = prepare_numeric_column(df, "total_trips")
    df = prepare_numeric_column(df, "percentage")
    df = df.sort_values("total_trips", ascending=True)
    df["label"] = df.apply(
        lambda row: f"{int(row['total_trips']):,} trajets · {row['percentage']:.2f} %".replace(",", " "),
        axis=1
    )

    fig = px.bar(
        df,
        x="total_trips",
        y="type_name",
        orientation="h",
        text="label",
        title="Répartition séparée — trains de jour vs trains de nuit",
        labels={
            "total_trips": "Nombre de trajets",
            "type_name": "Type de train"
        }
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F7")
    fig.update_yaxes(showgrid=False)
    return apply_pro_layout(fig, height=height)


def create_sunburst_chart(df: pd.DataFrame, height: int = 680):
    df = prepare_numeric_column(df, "total_trips")
    fig = px.sunburst(
        df,
        path=["source_name", "type_name"],
        values="total_trips",
        title="Répartition hiérarchique : Source → Type de train"
    )
    return apply_pro_layout(fig, height=height)


def create_heatmap_counts(df: pd.DataFrame, height: int = 560):
    pivot_df = df.pivot(index="source_name", columns="type_name", values="total_trips").fillna(0)
    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        title="Heatmap du volume de trajets : Source × Type de train",
        labels=dict(x="Type de train", y="Source", color="Trajets")
    )
    return apply_pro_layout(fig, height=height)


def create_quality_heatmap(df: pd.DataFrame, height: int = 560):
    pivot_df = df.pivot(index="source_name", columns="type_name", values="avg_quality_score").fillna(0)
    fig = px.imshow(
        pivot_df,
        text_auto=True,
        aspect="auto",
        title="Heatmap du score qualité moyen : Source × Type de train",
        labels=dict(x="Type de train", y="Source", color="Score qualité")
    )
    return apply_pro_layout(fig, height=height)


def create_radar_chart(df: pd.DataFrame, height: int = 680):
    fig = go.Figure()

    for _, row in df.iterrows():
        categories = ["Score qualité", "Taux valeurs manquantes", "Taux erreurs horaires", "Taux doublons"]
        values = [row["avg_quality_score"], row["missing_rate"], row["time_error_rate"], row["duplicate_rate"]]
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            name=row["source_name"]
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#E5E7EB")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        title="Diagramme de Kiviat : comparaison qualité par source"
    )
    return apply_pro_layout(fig, height=height)


def create_network_graph(df: pd.DataFrame, height: int = 760):
    df = prepare_numeric_column(df, "total_trips")
    G = nx.Graph()

    for _, row in df.iterrows():
        if row["source_city"] != row["target_city"]:
            G.add_edge(row["source_city"], row["target_city"], weight=row["total_trips"])

    pos = nx.spring_layout(G, seed=42, k=0.9)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1.2, color="#94A3B8"), hoverinfo="none", mode="lines")

    node_x = []
    node_y = []
    node_text = []
    node_size = []
    for node in G.nodes():
        x, y = pos[node]
        degree = G.degree(node)
        node_x.append(x)
        node_y.append(y)
        node_size.append(14 + degree * 4)
        node_text.append(f"{node}<br>Connexions : {degree}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=list(G.nodes()),
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker=dict(size=node_size, line=dict(width=1, color="#0F172A"))
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Graphe de réseau ferroviaire : connexions entre villes",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
    )
    return apply_pro_layout(fig, height=height)
