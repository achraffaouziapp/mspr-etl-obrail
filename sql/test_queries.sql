/* ============================================================
   ObRail Europe - Requêtes SQL d'analyse
   Fichier : sql/test_queries.sql
   Objectif : vérifier et analyser les données chargées
   ============================================================ */


/* ============================================================
   1. Vérification du volume de données par table
   ============================================================ */

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


/* ============================================================
   2. Répartition des trajets par type de train : jour / nuit
   ============================================================ */

SELECT
    tt.type_name,
    COUNT(*) AS total_trips
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
GROUP BY tt.type_name
ORDER BY total_trips DESC;


/* ============================================================
   3. Répartition des trajets par source de données
   ============================================================ */

SELECT
    ds.source_name,
    ds.source_format,
    COUNT(*) AS total_trips
FROM trip t
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
GROUP BY ds.source_name, ds.source_format
ORDER BY total_trips DESC;


/* ============================================================
   4. Répartition croisée source / type de train
   ============================================================ */

SELECT
    ds.source_name,
    tt.type_name,
    COUNT(*) AS total_trips
FROM trip t
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
GROUP BY ds.source_name, tt.type_name
ORDER BY ds.source_name, tt.type_name;


/* ============================================================
   5. Nombre de gares par pays
   ============================================================ */

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


/* ============================================================
   6. Nombre de villes par pays
   ============================================================ */

SELECT
    c.country_name,
    c.country_code,
    COUNT(ci.city_id) AS total_cities
FROM city ci
JOIN country c
    ON ci.country_id = c.country_id
GROUP BY c.country_name, c.country_code
ORDER BY total_cities DESC;


/* ============================================================
   7. Nombre de routes par opérateur
   ============================================================ */

SELECT
    o.operator_name,
    o.operator_code,
    COUNT(r.route_id) AS total_routes
FROM route r
JOIN "operator" o
    ON r.operator_id = o.operator_id
GROUP BY o.operator_name, o.operator_code
ORDER BY total_routes DESC;


/* ============================================================
   8. Nombre de trajets par opérateur
   ============================================================ */

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
ORDER BY total_trips DESC;


/* ============================================================
   9. Durée moyenne des trajets par type de train
   ============================================================ */

SELECT
    tt.type_name,
    COUNT(t.trip_id) AS total_trips,
    ROUND(AVG(t.duration_minutes), 2) AS avg_duration_minutes,
    ROUND(MIN(t.duration_minutes), 2) AS min_duration_minutes,
    ROUND(MAX(t.duration_minutes), 2) AS max_duration_minutes
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
WHERE t.duration_minutes IS NOT NULL
GROUP BY tt.type_name
ORDER BY avg_duration_minutes DESC;


/* ============================================================
   10. Top 20 des trajets les plus longs
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    tt.type_name,
    dep.station_name AS departure_station,
    arr.station_name AS arrival_station,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes,
    ds.source_name
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN route r
    ON t.route_id = r.route_id
JOIN station dep
    ON r.departure_station_id = dep.station_id
JOIN station arr
    ON r.arrival_station_id = arr.station_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE t.duration_minutes IS NOT NULL
ORDER BY t.duration_minutes DESC
LIMIT 20;


/* ============================================================
   11. Exemples de trajets de nuit
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    dep.station_name AS departure_station,
    arr.station_name AS arrival_station,
    t.service_date,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes,
    ds.source_name
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN route r
    ON t.route_id = r.route_id
JOIN station dep
    ON r.departure_station_id = dep.station_id
JOIN station arr
    ON r.arrival_station_id = arr.station_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE tt.type_name = 'night'
ORDER BY t.trip_id
LIMIT 20;


/* ============================================================
   12. Exemples de trajets de jour
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    dep.station_name AS departure_station,
    arr.station_name AS arrival_station,
    t.service_date,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes,
    ds.source_name
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN route r
    ON t.route_id = r.route_id
JOIN station dep
    ON r.departure_station_id = dep.station_id
JOIN station arr
    ON r.arrival_station_id = arr.station_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE tt.type_name = 'day'
ORDER BY t.trip_id
LIMIT 20;


/* ============================================================
   13. Routes transfrontalières
   Une route est transfrontalière si le pays de départ
   est différent du pays d'arrivée.
   ============================================================ */

SELECT
    dep_country.country_name AS departure_country,
    arr_country.country_name AS arrival_country,
    COUNT(r.route_id) AS total_routes
FROM route r
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
WHERE dep_country.country_id <> arr_country.country_id
GROUP BY dep_country.country_name, arr_country.country_name
ORDER BY total_routes DESC;


/* ============================================================
   14. Nombre de trajets transfrontaliers par type de train
   ============================================================ */

SELECT
    tt.type_name,
    COUNT(t.trip_id) AS total_cross_border_trips
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN route r
    ON t.route_id = r.route_id
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
WHERE dep_country.country_id <> arr_country.country_id
GROUP BY tt.type_name
ORDER BY total_cross_border_trips DESC;


/* ============================================================
   15. Analyse globale de la qualité des données
   ============================================================ */

SELECT
    COUNT(*) AS total_checks,
    SUM(CASE WHEN has_missing_values THEN 1 ELSE 0 END) AS trips_with_missing_values,
    SUM(CASE WHEN has_time_error THEN 1 ELSE 0 END) AS trips_with_time_error,
    SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) AS duplicated_trips,
    ROUND(AVG(quality_score), 2) AS avg_quality_score,
    MIN(quality_score) AS min_quality_score,
    MAX(quality_score) AS max_quality_score
FROM quality_check;


/* ============================================================
   16. Détail des trajets avec anomalie qualité
   ============================================================ */

SELECT
    q.quality_check_id,
    t.trip_id,
    t.trip_code,
    tt.type_name,
    q.has_missing_values,
    q.has_time_error,
    q.is_duplicate,
    q.quality_score,
    q.error_message,
    ds.source_name
FROM quality_check q
JOIN trip t
    ON q.trip_id = t.trip_id
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE
    q.has_missing_values = TRUE
    OR q.has_time_error = TRUE
    OR q.is_duplicate = TRUE
ORDER BY q.quality_score ASC, t.trip_id
LIMIT 100;


/* ============================================================
   17. Les 4 trajets de nuit incomplets identifiés
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    tt.type_name,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes,
    q.has_missing_values,
    q.has_time_error,
    q.quality_score,
    q.error_message
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN quality_check q
    ON t.trip_id = q.trip_id
WHERE t.trip_code IN ('ES 454', 'ES 455', 'MÁV IC 1204', 'MÁV IC 1205')
ORDER BY t.trip_code;


/* ============================================================
   18. Complétude des coordonnées des gares
   ============================================================ */

SELECT
    COUNT(*) AS total_stations,
    SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END) AS missing_latitude,
    SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END) AS missing_longitude,
    ROUND(
        100.0 * SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS coordinate_completion_rate_percent
FROM station;


/* ============================================================
   19. Complétude des coordonnées par pays
   ============================================================ */

SELECT
    c.country_name,
    c.country_code,
    COUNT(s.station_id) AS total_stations,
    SUM(CASE WHEN s.latitude IS NULL OR s.longitude IS NULL THEN 1 ELSE 0 END) AS stations_without_coordinates,
    ROUND(
        100.0 * SUM(CASE WHEN s.latitude IS NOT NULL AND s.longitude IS NOT NULL THEN 1 ELSE 0 END)
        / COUNT(s.station_id),
        2
    ) AS coordinate_completion_rate_percent
FROM station s
JOIN city ci
    ON s.city_id = ci.city_id
JOIN country c
    ON ci.country_id = c.country_id
GROUP BY c.country_name, c.country_code
ORDER BY coordinate_completion_rate_percent ASC;


/* ============================================================
   20. Vérification des doublons de trip_code
   ============================================================ */

SELECT
    trip_code,
    COUNT(*) AS duplicate_count
FROM trip
GROUP BY trip_code
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


/* ============================================================
   21. Nombre d'arrêts moyen par trajet
   ============================================================ */

SELECT
    tt.type_name,
    COUNT(DISTINCT t.trip_id) AS total_trips,
    ROUND(AVG(stop_counts.total_stops), 2) AS avg_stops_per_trip,
    MIN(stop_counts.total_stops) AS min_stops,
    MAX(stop_counts.total_stops) AS max_stops
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN (
    SELECT
        trip_id,
        COUNT(*) AS total_stops
    FROM trip_stop
    GROUP BY trip_id
) stop_counts
    ON t.trip_id = stop_counts.trip_id
GROUP BY tt.type_name
ORDER BY avg_stops_per_trip DESC;


/* ============================================================
   22. Top 20 des trajets avec le plus d'arrêts
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    tt.type_name,
    dep.station_name AS departure_station,
    arr.station_name AS arrival_station,
    COUNT(ts.trip_stop_id) AS total_stops
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN route r
    ON t.route_id = r.route_id
JOIN station dep
    ON r.departure_station_id = dep.station_id
JOIN station arr
    ON r.arrival_station_id = arr.station_id
JOIN trip_stop ts
    ON t.trip_id = ts.trip_id
GROUP BY
    t.trip_id,
    t.trip_code,
    tt.type_name,
    dep.station_name,
    arr.station_name
ORDER BY total_stops DESC
LIMIT 20;


/* ============================================================
   23. Top villes de départ
   ============================================================ */

SELECT
    dep_city.city_name AS departure_city,
    dep_country.country_name AS departure_country,
    COUNT(t.trip_id) AS total_departures
FROM trip t
JOIN route r
    ON t.route_id = r.route_id
JOIN station dep_station
    ON r.departure_station_id = dep_station.station_id
JOIN city dep_city
    ON dep_station.city_id = dep_city.city_id
JOIN country dep_country
    ON dep_city.country_id = dep_country.country_id
GROUP BY dep_city.city_name, dep_country.country_name
ORDER BY total_departures DESC
LIMIT 20;


/* ============================================================
   24. Top villes d'arrivée
   ============================================================ */

SELECT
    arr_city.city_name AS arrival_city,
    arr_country.country_name AS arrival_country,
    COUNT(t.trip_id) AS total_arrivals
FROM trip t
JOIN route r
    ON t.route_id = r.route_id
JOIN station arr_station
    ON r.arrival_station_id = arr_station.station_id
JOIN city arr_city
    ON arr_station.city_id = arr_city.city_id
JOIN country arr_country
    ON arr_city.country_id = arr_country.country_id
GROUP BY arr_city.city_name, arr_country.country_name
ORDER BY total_arrivals DESC
LIMIT 20;


/* ============================================================
   25. Exemple de recherche API future :
   rechercher des trajets entre deux villes
   Ici : départ contenant 'paris' et arrivée contenant 'lyon'
   ============================================================ */

SELECT
    t.trip_id,
    t.trip_code,
    tt.type_name,
    dep_city.city_name AS departure_city,
    dep_station.station_name AS departure_station,
    arr_city.city_name AS arrival_city,
    arr_station.station_name AS arrival_station,
    t.service_date,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
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
WHERE LOWER(dep_city.city_name) LIKE '%paris%'
  AND LOWER(arr_city.city_name) LIKE '%lyon%'
ORDER BY t.service_date, t.departure_time
LIMIT 50;


/* ============================================================
   26. Vue utile pour l'API : trajets enrichis
   Cette vue facilite les futurs endpoints FastAPI.
   ============================================================ */

CREATE OR REPLACE VIEW vw_trip_details AS
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
    ON t.trip_id = q.trip_id;


/* ============================================================
   27. Test de la vue vw_trip_details
   ============================================================ */

SELECT *
FROM vw_trip_details
ORDER BY trip_id
LIMIT 50;


/* ============================================================
   28. Vue utile pour le dashboard qualité
   ============================================================ */

CREATE OR REPLACE VIEW vw_quality_dashboard AS
SELECT
    tt.type_name AS train_type,
    ds.source_name,
    COUNT(t.trip_id) AS total_trips,
    SUM(CASE WHEN q.has_missing_values THEN 1 ELSE 0 END) AS trips_with_missing_values,
    SUM(CASE WHEN q.has_time_error THEN 1 ELSE 0 END) AS trips_with_time_error,
    SUM(CASE WHEN q.is_duplicate THEN 1 ELSE 0 END) AS duplicated_trips,
    ROUND(AVG(q.quality_score), 2) AS avg_quality_score
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
JOIN quality_check q
    ON t.trip_id = q.trip_id
GROUP BY tt.type_name, ds.source_name;


/* ============================================================
   29. Test de la vue qualité
   ============================================================ */

SELECT *
FROM vw_quality_dashboard
ORDER BY train_type, source_name;