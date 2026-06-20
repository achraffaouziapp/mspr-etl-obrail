/* ============================================================
   ObRail Europe - Création du schéma PostgreSQL
   Fichier : sql/create_tables.sql

   Ce script prépare une base propre pour charger les données transformées.
   Il supprime d'abord les anciennes tables, puis recrée toutes les tables
   du modèle relationnel avec leurs clés primaires, clés étrangères et index.
   ============================================================ */


/* ------------------------------------------------------------
   1. Nettoyage de l'ancien schéma

   Les tables sont supprimées dans l'ordre inverse des dépendances.
   CASCADE permet de supprimer automatiquement les contraintes liées.
   Cette étape garantit que le chargement repart toujours d'une base vide.
   ------------------------------------------------------------ */

DROP TABLE IF EXISTS quality_check CASCADE;
DROP TABLE IF EXISTS trip_stop CASCADE;
DROP TABLE IF EXISTS trip CASCADE;
DROP TABLE IF EXISTS route CASCADE;
DROP TABLE IF EXISTS "operator" CASCADE;
DROP TABLE IF EXISTS station CASCADE;
DROP TABLE IF EXISTS city CASCADE;
DROP TABLE IF EXISTS country CASCADE;
DROP TABLE IF EXISTS train_type CASCADE;
DROP TABLE IF EXISTS data_source CASCADE;


/* ------------------------------------------------------------
   2. Table country

   Cette table contient les pays utilisés pour rattacher les villes,
   les gares et les opérateurs à une zone géographique.
   ------------------------------------------------------------ */

CREATE TABLE country (
    country_id INTEGER PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    CONSTRAINT uq_country_name_code UNIQUE (country_name, country_code)
);


/* ------------------------------------------------------------
   3. Table city

   Cette table contient les villes.
   Chaque ville est rattachée à un pays avec country_id.
   ------------------------------------------------------------ */

CREATE TABLE city (
    city_id INTEGER PRIMARY KEY,
    city_name VARCHAR(150) NOT NULL,
    country_id INTEGER NOT NULL,
    CONSTRAINT fk_city_country
        FOREIGN KEY (country_id)
        REFERENCES country(country_id)
);


/* ------------------------------------------------------------
   4. Table station

   Cette table contient les gares.
   Certaines informations comme le code gare, les coordonnées GPS ou le fuseau
   horaire peuvent être absentes selon la qualité de la source d'origine.
   ------------------------------------------------------------ */

CREATE TABLE station (
    station_id INTEGER PRIMARY KEY,
    station_name VARCHAR(255) NOT NULL,
    station_code VARCHAR(100),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    timezone VARCHAR(100),
    city_id INTEGER NOT NULL,
    CONSTRAINT fk_station_city
        FOREIGN KEY (city_id)
        REFERENCES city(city_id)
);


/* ------------------------------------------------------------
   5. Table operator

   Cette table contient les opérateurs ferroviaires.
   Le nom "operator" étant un mot sensible en SQL, il est entouré de guillemets.
   ------------------------------------------------------------ */

CREATE TABLE "operator" (
    operator_id INTEGER PRIMARY KEY,
    operator_name VARCHAR(255) NOT NULL,
    operator_code VARCHAR(100),
    country_id INTEGER NOT NULL,
    CONSTRAINT fk_operator_country
        FOREIGN KEY (country_id)
        REFERENCES country(country_id)
);


/* ------------------------------------------------------------
   6. Table train_type

   Cette petite table de référence distingue les trains de jour et les trains
   de nuit. Le champ type_name est unique pour éviter les doublons.
   ------------------------------------------------------------ */

CREATE TABLE train_type (
    train_type_id INTEGER PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE
);


/* ------------------------------------------------------------
   7. Table data_source

   Cette table trace les sources utilisées dans l'ETL.
   Elle permet de savoir d'où vient chaque trajet chargé dans la base.
   ------------------------------------------------------------ */

CREATE TABLE data_source (
    data_source_id INTEGER PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT,
    source_format VARCHAR(100),
    extraction_date TIMESTAMP,
    licence VARCHAR(255),
    raw_file_name TEXT,
    import_status VARCHAR(50)
);


/* ------------------------------------------------------------
   8. Table route

   Une route représente une relation entre une gare de départ,
   une gare d'arrivée et un opérateur.
   La distance est prévue dans le modèle, mais elle peut rester vide en V1.
   ------------------------------------------------------------ */

CREATE TABLE route (
    route_id INTEGER PRIMARY KEY,
    departure_station_id INTEGER NOT NULL,
    arrival_station_id INTEGER NOT NULL,
    operator_id INTEGER NOT NULL,
    distance_km NUMERIC(10, 2),
    CONSTRAINT fk_route_departure_station
        FOREIGN KEY (departure_station_id)
        REFERENCES station(station_id),
    CONSTRAINT fk_route_arrival_station
        FOREIGN KEY (arrival_station_id)
        REFERENCES station(station_id),
    CONSTRAINT fk_route_operator
        FOREIGN KEY (operator_id)
        REFERENCES "operator"(operator_id)
);


/* ------------------------------------------------------------
   9. Table trip

   Cette table contient les trajets ferroviaires.
   Elle fait le lien entre une route, un type de train et une source de données.
   Les offsets permettent de gérer les trajets qui arrivent le lendemain.
   ------------------------------------------------------------ */

CREATE TABLE trip (
    trip_id INTEGER PRIMARY KEY,
    route_id INTEGER NOT NULL,
    train_type_id INTEGER NOT NULL,
    data_source_id INTEGER NOT NULL,
    trip_code VARCHAR(255) NOT NULL,
    service_date DATE,
    departure_time TIME,
    arrival_time TIME,
    departure_day_offset INTEGER,
    arrival_day_offset INTEGER,
    duration_minutes NUMERIC(10, 2),
    co2_estimated_kg NUMERIC(10, 2),
    CONSTRAINT fk_trip_route
        FOREIGN KEY (route_id)
        REFERENCES route(route_id),
    CONSTRAINT fk_trip_train_type
        FOREIGN KEY (train_type_id)
        REFERENCES train_type(train_type_id),
    CONSTRAINT fk_trip_data_source
        FOREIGN KEY (data_source_id)
        REFERENCES data_source(data_source_id)
);


/* ------------------------------------------------------------
   10. Table trip_stop

   Cette table détaille les arrêts d'un trajet.
   stop_order indique l'ordre de passage des gares dans l'itinéraire.
   ------------------------------------------------------------ */

CREATE TABLE trip_stop (
    trip_stop_id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    stop_order INTEGER NOT NULL,
    arrival_time TIME,
    departure_time TIME,
    arrival_day_offset INTEGER,
    departure_day_offset INTEGER,
    CONSTRAINT fk_trip_stop_trip
        FOREIGN KEY (trip_id)
        REFERENCES trip(trip_id),
    CONSTRAINT fk_trip_stop_station
        FOREIGN KEY (station_id)
        REFERENCES station(station_id)
);


/* ------------------------------------------------------------
   11. Table quality_check

   Cette table stocke les contrôles qualité appliqués aux trajets.
   Elle permet d'identifier les valeurs manquantes, les incohérences horaires
   et les doublons potentiels.
   ------------------------------------------------------------ */

CREATE TABLE quality_check (
    quality_check_id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    has_missing_values BOOLEAN NOT NULL,
    has_time_error BOOLEAN NOT NULL,
    is_duplicate BOOLEAN NOT NULL,
    quality_score INTEGER NOT NULL,
    rule_name VARCHAR(255),
    error_message TEXT,
    check_date DATE,
    CONSTRAINT fk_quality_check_trip
        FOREIGN KEY (trip_id)
        REFERENCES trip(trip_id)
);


/* ------------------------------------------------------------
   12. Index de performance

   Ces index accélèrent les jointures entre tables.
   Ils sont surtout utiles pour l'API REST et le dashboard Streamlit.
   ------------------------------------------------------------ */

CREATE INDEX idx_city_country_id ON city(country_id);
CREATE INDEX idx_station_city_id ON station(city_id);
CREATE INDEX idx_route_departure_station_id ON route(departure_station_id);
CREATE INDEX idx_route_arrival_station_id ON route(arrival_station_id);
CREATE INDEX idx_route_operator_id ON route(operator_id);
CREATE INDEX idx_trip_route_id ON trip(route_id);
CREATE INDEX idx_trip_train_type_id ON trip(train_type_id);
CREATE INDEX idx_trip_data_source_id ON trip(data_source_id);
CREATE INDEX idx_trip_stop_trip_id ON trip_stop(trip_id);
CREATE INDEX idx_trip_stop_station_id ON trip_stop(station_id);
CREATE INDEX idx_quality_check_trip_id ON quality_check(trip_id);
