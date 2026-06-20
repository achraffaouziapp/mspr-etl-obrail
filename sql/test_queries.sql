/* ============================================================
   ObRail Europe - Requêtes SQL de contrôle et d'analyse
   Fichier : sql/test_queries.sql

   Ce fichier regroupe des requêtes utiles pour vérifier le chargement,
   comprendre les volumes de données, analyser les trajets et contrôler
   la qualité des informations présentes dans PostgreSQL.
   ============================================================ */

/* ------------------------------------------------------------
   1. Contrôle du nombre de lignes par table

   Cette requête vérifie rapidement que toutes les tables principales ont été alimentées après le chargement PostgreSQL.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   2. Volume de trajets par type de train

   Cette analyse compare le nombre de trajets de jour et de nuit présents dans la table trip.
   ------------------------------------------------------------ */

SELECT
    tt.type_name,
    COUNT(*) AS total_trips
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
GROUP BY tt.type_name
ORDER BY total_trips DESC;


/* ------------------------------------------------------------
   3. Volume de trajets par source

   Cette requête montre quelles sources contribuent le plus au volume total des trajets.
   ------------------------------------------------------------ */

SELECT
    ds.source_name,
    ds.source_format,
    COUNT(*) AS total_trips
FROM trip t
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
GROUP BY ds.source_name, ds.source_format
ORDER BY total_trips DESC;


/* ------------------------------------------------------------
   4. Croisement entre source et type de train

   Cette analyse permet de voir quelle source alimente quel type de train : day ou night.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   5. Nombre de gares par pays

   Cette requête mesure la couverture géographique des gares dans l'entrepôt.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   6. Nombre de villes par pays

   Cette analyse complète la précédente en comptant les villes rattachées à chaque pays.
   ------------------------------------------------------------ */

SELECT
    c.country_name,
    c.country_code,
    COUNT(ci.city_id) AS total_cities
FROM city ci
JOIN country c
    ON ci.country_id = c.country_id
GROUP BY c.country_name, c.country_code
ORDER BY total_cities DESC;


/* ------------------------------------------------------------
   7. Nombre de routes par opérateur

   Cette requête indique combien de relations départ-arrivée sont associées à chaque opérateur.
   ------------------------------------------------------------ */

SELECT
    o.operator_name,
    o.operator_code,
    COUNT(r.route_id) AS total_routes
FROM route r
JOIN "operator" o
    ON r.operator_id = o.operator_id
GROUP BY o.operator_name, o.operator_code
ORDER BY total_routes DESC;


/* ------------------------------------------------------------
   8. Nombre de trajets par opérateur

   Cette analyse classe les opérateurs selon le volume de trajets réellement chargés.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   9. Durée des trajets par type de train

   Cette requête calcule la durée moyenne, minimale et maximale pour les trains de jour et de nuit.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   10. Trajets les plus longs

   Cette requête affiche les 20 trajets dont la durée calculée est la plus élevée.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   11. Exemples de trajets de nuit

   Cette requête affiche quelques trajets night pour vérifier que les sources de trains de nuit sont bien intégrées.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   12. Exemples de trajets de jour

   Cette requête affiche quelques trajets day pour contrôler les données issues de la source SNCF GTFS.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   13. Routes transfrontalières

   Une route est considérée comme transfrontalière lorsque le pays de départ est différent du pays d'arrivée.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   14. Trajets transfrontaliers par type de train

   Cette analyse compte les trajets transfrontaliers séparément pour les trains de jour et de nuit.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   15. Synthèse globale de la qualité

   Cette requête donne une vue d'ensemble des contrôles qualité : anomalies, score moyen, score minimum et maximum.
   ------------------------------------------------------------ */

SELECT
    COUNT(*) AS total_checks,
    SUM(CASE WHEN has_missing_values THEN 1 ELSE 0 END) AS trips_with_missing_values,
    SUM(CASE WHEN has_time_error THEN 1 ELSE 0 END) AS trips_with_time_error,
    SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) AS duplicated_trips,
    ROUND(AVG(quality_score), 2) AS avg_quality_score,
    MIN(quality_score) AS min_quality_score,
    MAX(quality_score) AS max_quality_score
FROM quality_check;


/* ------------------------------------------------------------
   16. Détail des trajets avec anomalie

   Cette requête liste les trajets qui présentent au moins une anomalie qualité détectée par l'ETL.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   17. Trajets de nuit incomplets connus

   Cette requête vérifie spécifiquement les quelques trajets de nuit identifiés avec des horaires manquants ou invalides.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   18. Complétude globale des coordonnées GPS

   Cette analyse mesure la part des gares qui possèdent une latitude et une longitude.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   19. Complétude des coordonnées GPS par pays

   Cette requête permet d'identifier les pays où les informations de géolocalisation sont les moins complètes.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   20. Recherche de doublons sur trip_code

   Cette requête vérifie si un même code trajet apparaît plusieurs fois dans la table trip.
   ------------------------------------------------------------ */

SELECT
    trip_code,
    COUNT(*) AS duplicate_count
FROM trip
GROUP BY trip_code
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


/* ------------------------------------------------------------
   21. Nombre moyen d'arrêts par trajet

   Cette analyse calcule le nombre moyen, minimum et maximum d'arrêts pour chaque type de train.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   22. Trajets avec le plus d'arrêts

   Cette requête affiche les 20 trajets qui possèdent le plus grand nombre d'arrêts.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   23. Villes avec le plus de départs

   Cette analyse identifie les villes qui apparaissent le plus souvent comme point de départ.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   24. Villes avec le plus d'arrivées

   Cette analyse identifie les villes qui apparaissent le plus souvent comme point d'arrivée.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   25. Exemple de recherche de trajet entre deux villes

   Cette requête simule un besoin API : rechercher des trajets dont le départ contient Paris et l'arrivée contient Lyon.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   26. Création de la vue vw_trip_details

   Cette vue prépare une table enrichie et plus simple à interroger pour l'API REST ou le dashboard.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   27. Test de la vue vw_trip_details

   Cette requête affiche les premières lignes de la vue enrichie pour vérifier qu'elle fonctionne correctement.
   ------------------------------------------------------------ */

SELECT *
FROM vw_trip_details
ORDER BY trip_id
LIMIT 50;


/* ------------------------------------------------------------
   28. Création de la vue vw_quality_dashboard

   Cette vue agrège les indicateurs qualité par source et par type de train pour faciliter les analyses futures.
   ------------------------------------------------------------ */

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


/* ------------------------------------------------------------
   29. Test de la vue qualité

   Cette requête affiche le contenu de la vue qualité afin de vérifier le résultat de l'agrégation.
   ------------------------------------------------------------ */

SELECT *
FROM vw_quality_dashboard
ORDER BY train_type, source_name;
