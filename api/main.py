from fastapi import FastAPI, Query, HTTPException

from api.database import execute_query


# Création de l'application FastAPI.
# Les informations ci-dessous apparaissent dans la documentation interactive /docs.
app = FastAPI(
    title="ObRail Europe API",
    description="API REST permettant de consulter les données ferroviaires transformées et chargées dans PostgreSQL.",
    version="1.0.0",
)


@app.get("/")
def root():
    """
    Point d'entrée simple de l'API.

    Il permet de vérifier rapidement que le serveur FastAPI est bien lancé et
    indique où trouver la documentation interactive.
    """
    return {
        "message": "Bienvenue sur l'API ObRail Europe",
        "documentation": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    Vérifie l'état de l'API et de la connexion PostgreSQL.

    Cet endpoint est utile pour les tests Postman ou pour vérifier rapidement que
    le backend communique correctement avec la base de données.
    """
    result = execute_query("SELECT 1 AS database_status;", fetch_one=True)

    return {
        "api_status": "ok",
        "database_status": "ok" if result else "error"
    }


@app.get("/tables/counts")
def get_table_counts():
    """
    Retourne le nombre de lignes présentes dans chaque table principale.

    Cette route sert à contrôler que le chargement ETL a bien alimenté toutes les
    tables attendues : dimensions, trajets, arrêts et contrôles qualité.
    """
    query = """
        SELECT 'country' AS table_name, COUNT(*) AS total_rows FROM country
        UNION ALL
        SELECT 'city', COUNT(*) FROM city
        UNION ALL
        SELECT 'station', COUNT(*) FROM station
        UNION ALL
        SELECT 'operator', COUNT(*) FROM "operator"
        UNION ALL
        SELECT 'train_type', COUNT(*) FROM train_type
        UNION ALL
        SELECT 'data_source', COUNT(*) FROM data_source
        UNION ALL
        SELECT 'route', COUNT(*) FROM route
        UNION ALL
        SELECT 'trip', COUNT(*) FROM trip
        UNION ALL
        SELECT 'trip_stop', COUNT(*) FROM trip_stop
        UNION ALL
        SELECT 'quality_check', COUNT(*) FROM quality_check
        ORDER BY table_name;
    """

    return execute_query(query)


@app.get("/train-types")
def get_train_types():
    """
    Liste les types de train disponibles dans la base.

    Dans ce projet, les trajets sont principalement classés en deux catégories :
    trains de jour et trains de nuit.
    """
    query = """
        SELECT
            train_type_id,
            type_name
        FROM train_type
        ORDER BY train_type_id;
    """

    return execute_query(query)


@app.get("/sources")
def get_data_sources():
    """
    Liste les sources de données intégrées dans le processus ETL.

    Cette route permet de voir d'où viennent les données : GTFS SNCF,
    Back-on-Track, European Sleeper ou autres sources utilisées dans le projet.
    """
    query = """
        SELECT
            data_source_id,
            source_name,
            source_format,
            source_url,
            extraction_date,
            import_status
        FROM data_source
        ORDER BY data_source_id;
    """

    return execute_query(query)


@app.get("/countries")
def get_countries():
    """
    Liste les pays présents dans l'entrepôt de données.

    Cette route est utile pour alimenter des filtres géographiques ou pour
    explorer la couverture européenne des gares.
    """
    query = """
        SELECT
            country_id,
            country_name,
            country_code
        FROM country
        ORDER BY country_name;
    """

    return execute_query(query)


@app.get("/stations")
def get_stations(
    country_code: str | None = Query(default=None, description="Filtrer par code pays, ex: FR"),
    city: str | None = Query(default=None, description="Filtrer par ville"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Retourne les gares avec des filtres optionnels.

    On peut filtrer par pays, par ville, et limiter le nombre de résultats pour
    éviter de retourner trop de lignes à la fois. Le paramètre offset permet de
    parcourir les résultats page par page.
    """
    conditions = []
    params = []

    if country_code:
        conditions.append("LOWER(c.country_code) = LOWER(%s)")
        params.append(country_code)

    if city:
        conditions.append("LOWER(ci.city_name) LIKE LOWER(%s)")
        params.append(f"%{city}%")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            s.station_id,
            s.station_name,
            s.station_code,
            s.latitude,
            s.longitude,
            s.timezone,
            ci.city_name,
            c.country_name,
            c.country_code
        FROM station s
        JOIN city ci
            ON s.city_id = ci.city_id
        JOIN country c
            ON ci.country_id = c.country_id
        {where_clause}
        ORDER BY s.station_name
        LIMIT %s OFFSET %s;
    """

    params.extend([limit, offset])

    return execute_query(query, tuple(params))


@app.get("/operators")
def get_operators():
    """
    Liste les opérateurs ferroviaires enregistrés dans la base.

    Chaque opérateur est rattaché à un pays. Les libellés sont conservés tels
    qu'ils proviennent des sources afin de garder la traçabilité des données.
    """
    query = """
        SELECT
            o.operator_id,
            o.operator_name,
            o.operator_code,
            c.country_name,
            c.country_code
        FROM "operator" o
        JOIN country c
            ON o.country_id = c.country_id
        ORDER BY o.operator_name;
    """

    return execute_query(query)


@app.get("/trips")
def get_trips(
    train_type: str | None = Query(default=None, description="day ou night"),
    departure_city: str | None = Query(default=None, description="Ville de départ"),
    arrival_city: str | None = Query(default=None, description="Ville d'arrivée"),
    source_id: int | None = Query(default=None, description="Identifiant de la source"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Retourne une liste de trajets ferroviaires avec filtres optionnels.

    Cette route est l'une des plus importantes de l'API. Elle regroupe les
    informations du trajet, des gares de départ et d'arrivée, de la source,
    de l'opérateur et du contrôle qualité.
    """
    conditions = []
    params = []

    if train_type:
        conditions.append("LOWER(tt.type_name) = LOWER(%s)")
        params.append(train_type)

    if departure_city:
        conditions.append("LOWER(dep_city.city_name) LIKE LOWER(%s)")
        params.append(f"%{departure_city}%")

    if arrival_city:
        conditions.append("LOWER(arr_city.city_name) LIKE LOWER(%s)")
        params.append(f"%{arrival_city}%")

    if source_id:
        conditions.append("t.data_source_id = %s")
        params.append(source_id)

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
            dep_country.country_name AS departure_country,
            arr_station.station_name AS arrival_station,
            arr_city.city_name AS arrival_city,
            arr_country.country_name AS arrival_country,
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
        JOIN country dep_country
            ON dep_city.country_id = dep_country.country_id
        JOIN station arr_station
            ON r.arrival_station_id = arr_station.station_id
        JOIN city arr_city
            ON arr_station.city_id = arr_city.city_id
        JOIN country arr_country
            ON arr_city.country_id = arr_country.country_id
        LEFT JOIN quality_check q
            ON t.trip_id = q.trip_id
        {where_clause}
        ORDER BY t.trip_id
        LIMIT %s OFFSET %s;
    """

    params.extend([limit, offset])

    return execute_query(query, tuple(params))


@app.get("/trips/{trip_id}")
def get_trip_by_id(trip_id: int):
    """
    Retourne le détail complet d'un trajet à partir de son identifiant.

    Si aucun trajet ne correspond à l'identifiant demandé, l'API renvoie une
    erreur 404 afin d'indiquer clairement que la ressource n'existe pas.
    """
    query = """
        SELECT
            t.trip_id,
            t.trip_code,
            tt.type_name AS train_type,
            ds.source_name,
            dep_station.station_name AS departure_station,
            dep_city.city_name AS departure_city,
            dep_country.country_name AS departure_country,
            arr_station.station_name AS arrival_station,
            arr_city.city_name AS arrival_city,
            arr_country.country_name AS arrival_country,
            o.operator_name,
            t.service_date,
            t.departure_time,
            t.arrival_time,
            t.duration_minutes,
            t.co2_estimated_kg,
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
        JOIN country dep_country
            ON dep_city.country_id = dep_country.country_id
        JOIN station arr_station
            ON r.arrival_station_id = arr_station.station_id
        JOIN city arr_city
            ON arr_station.city_id = arr_city.city_id
        JOIN country arr_country
            ON arr_city.country_id = arr_country.country_id
        LEFT JOIN quality_check q
            ON t.trip_id = q.trip_id
        WHERE t.trip_id = %s;
    """

    result = execute_query(query, (trip_id,), fetch_one=True)

    if result is None:
        raise HTTPException(status_code=404, detail="Trajet introuvable")

    return result


@app.get("/trips/{trip_id}/stops")
def get_trip_stops(trip_id: int):
    """
    Retourne les arrêts associés à un trajet.

    Les arrêts sont classés dans l'ordre du parcours grâce à stop_order. Cette
    route permet donc de reconstituer l'itinéraire complet d'un train.
    """
    query = """
        SELECT
            ts.trip_stop_id,
            ts.trip_id,
            ts.stop_order,
            s.station_name,
            s.station_code,
            ci.city_name,
            c.country_name,
            ts.arrival_time,
            ts.departure_time,
            ts.arrival_day_offset,
            ts.departure_day_offset
        FROM trip_stop ts
        JOIN station s
            ON ts.station_id = s.station_id
        JOIN city ci
            ON s.city_id = ci.city_id
        JOIN country c
            ON ci.country_id = c.country_id
        WHERE ts.trip_id = %s
        ORDER BY ts.stop_order;
    """

    rows = execute_query(query, (trip_id,))

    if not rows:
        raise HTTPException(status_code=404, detail="Aucun arrêt trouvé pour ce trajet")

    return rows


@app.get("/quality")
def get_quality_checks(
    only_errors: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Retourne les résultats des contrôles qualité.

    Par défaut, l'API affiche uniquement les lignes qui contiennent une anomalie.
    Il est possible de désactiver ce filtre avec only_errors=false pour consulter
    l'ensemble des contrôles.
    """
    where_clause = ""

    if only_errors:
        where_clause = """
            WHERE
                q.has_missing_values = TRUE
                OR q.has_time_error = TRUE
                OR q.is_duplicate = TRUE
        """

    query = f"""
        SELECT
            q.quality_check_id,
            q.trip_id,
            t.trip_code,
            tt.type_name AS train_type,
            q.has_missing_values,
            q.has_time_error,
            q.is_duplicate,
            q.quality_score,
            q.rule_name,
            q.error_message,
            q.check_date
        FROM quality_check q
        JOIN trip t
            ON q.trip_id = t.trip_id
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        {where_clause}
        ORDER BY q.quality_score ASC, q.trip_id
        LIMIT %s OFFSET %s;
    """

    return execute_query(query, (limit, offset))


@app.get("/stats/train-types")
def get_stats_by_train_type():
    """
    Calcule le nombre de trajets par type de train.

    Cette statistique est utilisée pour comparer le volume des trains de jour et
    des trains de nuit dans l'entrepôt de données.
    """
    query = """
        SELECT
            tt.type_name,
            COUNT(*) AS total_trips
        FROM trip t
        JOIN train_type tt
            ON t.train_type_id = tt.train_type_id
        GROUP BY tt.type_name
        ORDER BY total_trips DESC;
    """

    return execute_query(query)


@app.get("/stats/sources")
def get_stats_by_source():
    """
    Calcule le nombre de trajets par source de données.

    Cette statistique permet de comprendre quelle source contribue le plus au
    volume global des trajets.
    """
    query = """
        SELECT
            ds.source_name,
            ds.source_format,
            COUNT(*) AS total_trips
        FROM trip t
        JOIN data_source ds
            ON t.data_source_id = ds.data_source_id
        GROUP BY ds.source_name, ds.source_format
        ORDER BY total_trips DESC;
    """

    return execute_query(query)


@app.get("/stats/quality")
def get_quality_stats():
    """
    Retourne les indicateurs globaux de qualité.

    Cette route résume le nombre de contrôles effectués, les anomalies détectées
    et le score qualité moyen calculé pendant la transformation.
    """
    query = """
        SELECT
            COUNT(*) AS total_checks,
            SUM(CASE WHEN has_missing_values THEN 1 ELSE 0 END) AS trips_with_missing_values,
            SUM(CASE WHEN has_time_error THEN 1 ELSE 0 END) AS trips_with_time_error,
            SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) AS duplicated_trips,
            ROUND(AVG(quality_score), 2) AS avg_quality_score,
            MIN(quality_score) AS min_quality_score,
            MAX(quality_score) AS max_quality_score
        FROM quality_check;
    """

    return execute_query(query, fetch_one=True)


@app.get("/stats/stations-by-country")
def get_stations_by_country():
    """
    Calcule le nombre de gares par pays.

    Cette statistique permet d'évaluer la couverture géographique des données et
    d'identifier les pays les plus représentés dans la base.
    """
    query = """
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
    """

    return execute_query(query)
