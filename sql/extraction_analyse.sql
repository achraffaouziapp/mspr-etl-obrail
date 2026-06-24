-- =====================================================================
-- ObRail Europe - Requêtes SQL d'extraction et d'analyse
-- MSPR TPRE612 - Livrable : Requêtes SQL depuis un SGBD
-- =====================================================================
--
-- Objectif :
-- Ce fichier regroupe des requêtes SQL permettant d'extraire et d'analyser
-- les données stockées dans la base PostgreSQL ObRail Europe.
--
-- Ces requêtes montrent l'utilisation :
-- - de jointures entre plusieurs tables ;
-- - d'agrégations ;
-- - de filtres métier ;
-- - de contrôles qualité ;
-- - d'analyses par source, opérateur, type de train et géographie.
--
-- Exécution possible :
-- - dans DBeaver ;
-- - dans pgAdmin ;
-- - avec psql ;
-- - depuis un conteneur PostgreSQL Docker.
--
-- Base attendue : obrail
-- Schéma attendu : public
-- =====================================================================

--Lancement des requêtes SQL (DBeaver):
-- 1.Ouvre DBeaver.
-- 1.Connecte-toi à ta base PostgreSQL obrail.
-- 1.Va dans le menu SQL Editor.
-- 1.Ouvre le fichier requetes_sql_extraction_analyse.sql.
-- 1.Sélectionne une requête.
-- 1.Clique sur Exécuter la sélection ou fais Ctrl + Entrée.


-- =====================================================================
-- 1. Vérifier rapidement le volume de données par table
-- =====================================================================

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


-- =====================================================================
-- 2. Répartition des trajets par type de train
-- Objectif : comparer les volumes entre trains de jour et trains de nuit.
-- =====================================================================

SELECT
    tt.type_name AS type_train,
    COUNT(t.trip_id) AS nombre_trajets
FROM trip t
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
GROUP BY tt.type_name
ORDER BY nombre_trajets DESC;


-- =====================================================================
-- 3. Top 15 des opérateurs par nombre de trajets
-- Objectif : identifier les opérateurs les plus représentés dans la base.
-- =====================================================================

SELECT
    o.operator_name AS operateur,
    COUNT(t.trip_id) AS nombre_trajets
FROM trip t
JOIN route r
    ON t.route_id = r.route_id
JOIN "operator" o
    ON r.operator_id = o.operator_id
GROUP BY o.operator_name
ORDER BY nombre_trajets DESC
LIMIT 15;


-- =====================================================================
-- 4. Volume de données collectées par opérateur
-- Objectif : mesurer le volume total en combinant trajets et arrêts.
-- =====================================================================

SELECT
    COALESCE(NULLIF(o.operator_name, ''), 'Opérateur inconnu') AS operateur,
    COUNT(DISTINCT t.trip_id) AS total_trajets,
    COUNT(ts.trip_stop_id) AS total_arrets,
    COUNT(DISTINCT t.trip_id) + COUNT(ts.trip_stop_id) AS volume_total
FROM trip t
JOIN route r
    ON t.route_id = r.route_id
LEFT JOIN "operator" o
    ON r.operator_id = o.operator_id
LEFT JOIN trip_stop ts
    ON t.trip_id = ts.trip_id
GROUP BY operateur
ORDER BY volume_total DESC
LIMIT 15;


-- =====================================================================
-- 5. Recherche de dessertes ferroviaires par ville et type de train
-- Objectif : extraire les trajets selon des critères métier.
--
-- Exemple ci-dessous :
-- - ville de départ contenant "Paris"
-- - ville d'arrivée contenant "Berlin"
-- - type de train "night"
--
-- Modifier les valeurs dans le WHERE selon le besoin.
-- =====================================================================

SELECT
    t.trip_id,
    t.trip_code,
    dep_city.city_name AS ville_depart,
    dep_station.station_name AS gare_depart,
    arr_city.city_name AS ville_arrivee,
    arr_station.station_name AS gare_arrivee,
    tt.type_name AS type_train,
    ds.source_name AS source_donnees,
    t.service_date,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes
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
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE dep_city.city_name ILIKE '%Paris%'
  AND arr_city.city_name ILIKE '%Berlin%'
  AND tt.type_name = 'night'
ORDER BY t.service_date, t.departure_time
LIMIT 50;


-- =====================================================================
-- 6. Liste des arrêts d'un trajet précis
-- Objectif : vérifier le détail du parcours d'un trip.
--
-- Remplacer la valeur 1 par l'identifiant du trajet à analyser.
-- =====================================================================

SELECT
    t.trip_id,
    t.trip_code,
    ts.stop_order AS ordre_arret,
    s.station_name AS gare,
    c.city_name AS ville,
    co.country_name AS pays,
    ts.arrival_time,
    ts.departure_time,
    ts.arrival_day_offset,
    ts.departure_day_offset
FROM trip t
JOIN trip_stop ts
    ON t.trip_id = ts.trip_id
JOIN station s
    ON ts.station_id = s.station_id
JOIN city c
    ON s.city_id = c.city_id
JOIN country co
    ON c.country_id = co.country_id
WHERE t.trip_id = 1
ORDER BY ts.stop_order;


-- =====================================================================
-- 7. Top 15 des pays par nombre de gares
-- Objectif : analyser la couverture géographique du jeu de données.
-- =====================================================================

SELECT
    co.country_name AS pays,
    COUNT(s.station_id) AS nombre_gares
FROM station s
JOIN city c
    ON s.city_id = c.city_id
JOIN country co
    ON c.country_id = co.country_id
GROUP BY co.country_name
ORDER BY nombre_gares DESC
LIMIT 15;


-- =====================================================================
-- 8. Répartition des trajets par source et type de train
-- Objectif : savoir quelles sources alimentent les trains de jour/nuit.
-- =====================================================================

SELECT
    ds.source_name AS source_donnees,
    tt.type_name AS type_train,
    COUNT(t.trip_id) AS nombre_trajets
FROM trip t
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
GROUP BY ds.source_name, tt.type_name
ORDER BY ds.source_name, tt.type_name;


-- =====================================================================
-- 9. Taux d'anomalies qualité par source de données
-- Objectif : comparer la qualité des données selon leur origine.
-- =====================================================================

SELECT
    ds.source_name AS source_donnees,
    COUNT(q.quality_check_id) AS nombre_controles,
    SUM(
        CASE
            WHEN q.has_missing_values OR q.has_time_error OR q.is_duplicate
            THEN 1
            ELSE 0
        END
    ) AS nombre_anomalies,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN q.has_missing_values OR q.has_time_error OR q.is_duplicate
                THEN 1
                ELSE 0
            END
        ) / NULLIF(COUNT(q.quality_check_id), 0),
        2
    ) AS taux_anomalies_pct,
    ROUND(AVG(q.quality_score), 2) AS score_qualite_moyen
FROM quality_check q
JOIN trip t
    ON q.trip_id = t.trip_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
GROUP BY ds.source_name
ORDER BY taux_anomalies_pct DESC, score_qualite_moyen ASC;


-- =====================================================================
-- 10. Champs critiques : taux de valeurs manquantes sur quelques colonnes clés
-- Objectif : produire un contrôle simple de complétude.
-- =====================================================================

SELECT
    'trip.departure_time' AS champ,
    COUNT(*) AS total_lignes,
    SUM(CASE WHEN departure_time IS NULL THEN 1 ELSE 0 END) AS valeurs_manquantes,
    ROUND(
        100.0 * SUM(CASE WHEN departure_time IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    ) AS taux_manquant_pct
FROM trip

UNION ALL

SELECT
    'trip.arrival_time',
    COUNT(*),
    SUM(CASE WHEN arrival_time IS NULL THEN 1 ELSE 0 END),
    ROUND(
        100.0 * SUM(CASE WHEN arrival_time IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    )
FROM trip

UNION ALL

SELECT
    'trip.duration_minutes',
    COUNT(*),
    SUM(CASE WHEN duration_minutes IS NULL THEN 1 ELSE 0 END),
    ROUND(
        100.0 * SUM(CASE WHEN duration_minutes IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    )
FROM trip

UNION ALL

SELECT
    'station.latitude',
    COUNT(*),
    SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END),
    ROUND(
        100.0 * SUM(CASE WHEN latitude IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    )
FROM station

UNION ALL

SELECT
    'station.longitude',
    COUNT(*),
    SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END),
    ROUND(
        100.0 * SUM(CASE WHEN longitude IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        2
    )
FROM station
ORDER BY taux_manquant_pct DESC;


-- =====================================================================
-- 11. Trajets avec erreur horaire ou durée invalide
-- Objectif : inspecter les anomalies qualité les plus importantes.
-- =====================================================================

SELECT
    t.trip_id,
    t.trip_code,
    tt.type_name AS type_train,
    ds.source_name AS source_donnees,
    t.departure_time,
    t.arrival_time,
    t.duration_minutes,
    q.has_missing_values,
    q.has_time_error,
    q.is_duplicate,
    q.quality_score,
    q.error_message
FROM quality_check q
JOIN trip t
    ON q.trip_id = t.trip_id
JOIN train_type tt
    ON t.train_type_id = tt.train_type_id
JOIN data_source ds
    ON t.data_source_id = ds.data_source_id
WHERE q.has_time_error = TRUE
   OR q.has_missing_values = TRUE
   OR q.is_duplicate = TRUE
ORDER BY q.quality_score ASC, t.trip_id
LIMIT 100;


-- =====================================================================
-- 12. Connexions ferroviaires les plus fréquentes entre villes
-- Objectif : alimenter une analyse réseau ou une visualisation de connexions.
-- =====================================================================

SELECT
    dep_city.city_name AS ville_depart,
    arr_city.city_name AS ville_arrivee,
    COUNT(t.trip_id) AS nombre_trajets
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
ORDER BY nombre_trajets DESC
LIMIT 50;


-- =====================================================================
-- Fin du fichier
-- =====================================================================
