# Dictionnaire des données — ObRail Europe

## 1. Objectif du document

Ce dictionnaire des données décrit les tables utilisées dans la base PostgreSQL du projet **ObRail Europe**.  
Il sert à expliquer le rôle de chaque table, les colonnes principales, les clés primaires, les clés étrangères et les règles de cohérence mises en place dans le modèle physique.

Le modèle relationnel a été conçu pour centraliser des données ferroviaires provenant de plusieurs sources hétérogènes : fichiers GTFS, fichiers CSV, fichiers JSON et scraping HTML. Les données sont transformées dans un format commun avant d’être chargées dans PostgreSQL.

---

## 2. Vue d’ensemble des tables

| Table | Rôle principal |
|---|---|
| `country` | Stocke les pays utilisés dans le référentiel géographique. |
| `city` | Stocke les villes rattachées à un pays. |
| `station` | Stocke les gares ferroviaires rattachées à une ville. |
| `operator` | Stocke les opérateurs ferroviaires. |
| `train_type` | Stocke les types de trains : jour ou nuit. |
| `data_source` | Stocke les sources de données utilisées dans l’ETL. |
| `route` | Stocke les relations entre une gare de départ, une gare d’arrivée et un opérateur. |
| `trip` | Stocke les trajets ferroviaires. |
| `trip_stop` | Stocke les arrêts intermédiaires d’un trajet. |
| `quality_check` | Stocke les contrôles qualité appliqués aux trajets. |

---

## 3. Table `country`

### Rôle

La table `country` contient les pays utilisés dans le projet. Elle permet de rattacher les villes et les opérateurs ferroviaires à une zone géographique.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `country_id` | `INTEGER` | PK | Oui | Identifiant unique du pays. |
| `country_name` | `VARCHAR(100)` |  | Oui | Nom du pays. Exemple : France, Germany, Belgium. |
| `country_code` | `VARCHAR(10)` |  | Oui | Code du pays. Exemple : FR, DE, BE. |

### Contraintes

| Contrainte | Description |
|---|---|
| `PRIMARY KEY (country_id)` | Garantit l’unicité de chaque pays. |
| `UNIQUE (country_name, country_code)` | Évite d’insérer deux fois le même pays avec le même code. |

---

## 4. Table `city`

### Rôle

La table `city` contient les villes identifiées dans les différentes sources. Chaque ville est rattachée à un pays.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `city_id` | `INTEGER` | PK | Oui | Identifiant unique de la ville. |
| `city_name` | `VARCHAR(150)` |  | Oui | Nom de la ville. |
| `country_id` | `INTEGER` | FK | Oui | Référence vers le pays de la ville. |

### Relations

| Relation | Description |
|---|---|
| `city.country_id` → `country.country_id` | Une ville appartient à un pays. |

---

## 5. Table `station`

### Rôle

La table `station` contient les gares ferroviaires. Les gares proviennent de plusieurs sources : SNCF GTFS, référentiel des gares voyageurs, Wikipedia, Back-on-Track et European Sleeper.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `station_id` | `INTEGER` | PK | Oui | Identifiant unique de la gare. |
| `station_name` | `VARCHAR(255)` |  | Oui | Nom de la gare. |
| `station_code` | `VARCHAR(100)` |  | Non | Code ou identifiant de la gare dans la source d’origine. |
| `latitude` | `NUMERIC(10,7)` |  | Non | Latitude GPS de la gare. |
| `longitude` | `NUMERIC(10,7)` |  | Non | Longitude GPS de la gare. |
| `timezone` | `VARCHAR(100)` |  | Non | Fuseau horaire de la gare. |
| `city_id` | `INTEGER` | FK | Oui | Référence vers la ville de la gare. |

### Relations

| Relation | Description |
|---|---|
| `station.city_id` → `city.city_id` | Une gare appartient à une ville. |

### Remarque

Certaines gares peuvent ne pas avoir de coordonnées GPS ou de code gare selon la source d’origine. Le modèle accepte donc ces champs en valeur nulle.

---

## 6. Table `operator`

### Rôle

La table `operator` contient les opérateurs ferroviaires associés aux routes. Le nom de la table est encadré par des guillemets dans PostgreSQL (`"operator"`) car `operator` peut être un terme sensible en SQL.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `operator_id` | `INTEGER` | PK | Oui | Identifiant unique de l’opérateur. |
| `operator_name` | `VARCHAR(255)` |  | Oui | Nom de l’opérateur ferroviaire. |
| `operator_code` | `VARCHAR(100)` |  | Non | Code de l’opérateur dans la source d’origine. |
| `country_id` | `INTEGER` | FK | Oui | Pays associé à l’opérateur. |

### Relations

| Relation | Description |
|---|---|
| `operator.country_id` → `country.country_id` | Un opérateur est rattaché à un pays. |

### Remarque

Les libellés d’opérateurs sont conservés tels qu’ils apparaissent dans les sources pour garder la traçabilité des données. Cela peut entraîner plusieurs variantes pour un même groupe ferroviaire.

---

## 7. Table `train_type`

### Rôle

La table `train_type` distingue les types de trains utilisés dans le projet. Elle permet notamment de différencier les trains de jour et les trains de nuit.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `train_type_id` | `INTEGER` | PK | Oui | Identifiant unique du type de train. |
| `type_name` | `VARCHAR(50)` |  | Oui | Nom du type de train. Exemple : `day`, `night`. |

### Contraintes

| Contrainte | Description |
|---|---|
| `PRIMARY KEY (train_type_id)` | Garantit l’unicité du type de train. |
| `UNIQUE (type_name)` | Évite d’avoir deux fois le même type de train. |

---

## 8. Table `data_source`

### Rôle

La table `data_source` trace les sources utilisées dans le pipeline ETL. Elle permet de savoir d’où proviennent les trajets chargés dans la base.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `data_source_id` | `INTEGER` | PK | Oui | Identifiant unique de la source. |
| `source_name` | `VARCHAR(255)` |  | Oui | Nom de la source. |
| `source_url` | `TEXT` |  | Non | URL de la source de données. |
| `source_format` | `VARCHAR(100)` |  | Non | Format de la source : CSV, JSON, GTFS ZIP, HTML scraping. |
| `extraction_date` | `TIMESTAMP` |  | Non | Date et heure d’extraction. |
| `licence` | `VARCHAR(255)` |  | Non | Licence ou information d’usage si disponible. |
| `raw_file_name` | `TEXT` |  | Non | Nom des fichiers bruts extraits. |
| `import_status` | `VARCHAR(50)` |  | Non | Statut d’import de la source. Exemple : success. |

### Remarque

Cette table est importante pour la traçabilité. Elle permet de relier chaque trajet à la source qui a permis de le produire.

---

## 9. Table `route`

### Rôle

La table `route` représente une relation ferroviaire entre une gare de départ, une gare d’arrivée et un opérateur.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `route_id` | `INTEGER` | PK | Oui | Identifiant unique de la route. |
| `departure_station_id` | `INTEGER` | FK | Oui | Gare de départ de la route. |
| `arrival_station_id` | `INTEGER` | FK | Oui | Gare d’arrivée de la route. |
| `operator_id` | `INTEGER` | FK | Oui | Opérateur associé à la route. |
| `distance_km` | `NUMERIC(10,2)` |  | Non | Distance estimée entre les deux gares, en kilomètres. |

### Relations

| Relation | Description |
|---|---|
| `route.departure_station_id` → `station.station_id` | Une route part d’une gare. |
| `route.arrival_station_id` → `station.station_id` | Une route arrive dans une gare. |
| `route.operator_id` → `operator.operator_id` | Une route est exploitée par un opérateur. |

### Remarque

La colonne `distance_km` est prévue pour l’évolution du projet. Dans la première version, elle peut rester vide si le calcul de distance n’est pas encore appliqué à toutes les routes.

---

## 10. Table `trip`

### Rôle

La table `trip` est la table centrale du modèle. Elle contient les trajets ferroviaires produits par la transformation ETL.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `trip_id` | `INTEGER` | PK | Oui | Identifiant unique du trajet. |
| `route_id` | `INTEGER` | FK | Oui | Route empruntée par le trajet. |
| `train_type_id` | `INTEGER` | FK | Oui | Type de train : jour ou nuit. |
| `data_source_id` | `INTEGER` | FK | Oui | Source d’origine du trajet. |
| `trip_code` | `VARCHAR(255)` |  | Oui | Code du trajet dans la source d’origine. |
| `service_date` | `DATE` |  | Non | Date de circulation du trajet. |
| `departure_time` | `TIME` |  | Non | Heure de départ. |
| `arrival_time` | `TIME` |  | Non | Heure d’arrivée. |
| `departure_day_offset` | `INTEGER` |  | Non | Décalage de jour au départ. Généralement 0. |
| `arrival_day_offset` | `INTEGER` |  | Non | Décalage de jour à l’arrivée. Utile pour les trains de nuit. |
| `duration_minutes` | `NUMERIC(10,2)` |  | Non | Durée du trajet en minutes. |
| `co2_estimated_kg` | `NUMERIC(10,2)` |  | Non | Estimation éventuelle des émissions CO₂ du trajet. |

### Relations

| Relation | Description |
|---|---|
| `trip.route_id` → `route.route_id` | Un trajet circule sur une route. |
| `trip.train_type_id` → `train_type.train_type_id` | Un trajet appartient à un type de train. |
| `trip.data_source_id` → `data_source.data_source_id` | Un trajet provient d’une source de données. |

### Remarque

Les colonnes `departure_day_offset` et `arrival_day_offset` permettent de gérer correctement les trajets qui dépassent minuit, par exemple les trains de nuit.

---

## 11. Table `trip_stop`

### Rôle

La table `trip_stop` détaille les arrêts d’un trajet. Elle permet de reconstruire l’itinéraire d’un train dans l’ordre de passage des gares.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `trip_stop_id` | `INTEGER` | PK | Oui | Identifiant unique de l’arrêt. |
| `trip_id` | `INTEGER` | FK | Oui | Trajet concerné par l’arrêt. |
| `station_id` | `INTEGER` | FK | Oui | Gare de l’arrêt. |
| `stop_order` | `INTEGER` |  | Oui | Ordre de passage de la gare dans le trajet. |
| `arrival_time` | `TIME` |  | Non | Heure d’arrivée à l’arrêt. |
| `departure_time` | `TIME` |  | Non | Heure de départ depuis l’arrêt. |
| `arrival_day_offset` | `INTEGER` |  | Non | Décalage de jour à l’arrivée. |
| `departure_day_offset` | `INTEGER` |  | Non | Décalage de jour au départ. |

### Relations

| Relation | Description |
|---|---|
| `trip_stop.trip_id` → `trip.trip_id` | Un arrêt appartient à un trajet. |
| `trip_stop.station_id` → `station.station_id` | Un arrêt se situe dans une gare. |

---

## 12. Table `quality_check`

### Rôle

La table `quality_check` stocke les contrôles qualité appliqués aux trajets. Elle permet d’identifier rapidement les trajets incomplets, incohérents ou potentiellement dupliqués.

### Colonnes

| Colonne | Type PostgreSQL | Clé | Obligatoire | Description |
|---|---:|---|---|---|
| `quality_check_id` | `INTEGER` | PK | Oui | Identifiant unique du contrôle qualité. |
| `trip_id` | `INTEGER` | FK | Oui | Trajet contrôlé. |
| `has_missing_values` | `BOOLEAN` |  | Oui | Indique si le trajet contient des valeurs manquantes importantes. |
| `has_time_error` | `BOOLEAN` |  | Oui | Indique si une incohérence horaire ou une durée invalide a été détectée. |
| `is_duplicate` | `BOOLEAN` |  | Oui | Indique si le trajet est potentiellement dupliqué. |
| `quality_score` | `INTEGER` |  | Oui | Score qualité calculé entre 0 et 100. |
| `rule_name` | `VARCHAR(255)` |  | Non | Nom de la règle qualité appliquée. |
| `error_message` | `TEXT` |  | Non | Message décrivant les anomalies détectées. |
| `check_date` | `DATE` |  | Non | Date d’exécution du contrôle qualité. |

### Relations

| Relation | Description |
|---|---|
| `quality_check.trip_id` → `trip.trip_id` | Un contrôle qualité est rattaché à un trajet. |

### Remarque

Le score qualité commence à 100 puis diminue en fonction des anomalies détectées : valeurs manquantes, erreur horaire ou doublon potentiel.

---

## 13. Relations principales du modèle

| Relation | Cardinalité | Description |
|---|---:|---|
| `country` → `city` | 1,N | Un pays contient plusieurs villes. |
| `country` → `operator` | 1,N | Un pays peut être associé à plusieurs opérateurs. |
| `city` → `station` | 1,N | Une ville peut contenir plusieurs gares. |
| `station` → `route` | 1,N | Une gare peut être utilisée comme gare de départ ou d’arrivée dans plusieurs routes. |
| `operator` → `route` | 1,N | Un opérateur peut exploiter plusieurs routes. |
| `route` → `trip` | 1,N | Une route peut être utilisée par plusieurs trajets. |
| `train_type` → `trip` | 1,N | Un type de train peut concerner plusieurs trajets. |
| `data_source` → `trip` | 1,N | Une source peut fournir plusieurs trajets. |
| `trip` → `trip_stop` | 1,N | Un trajet contient plusieurs arrêts. |
| `station` → `trip_stop` | 1,N | Une gare peut apparaître dans plusieurs arrêts. |
| `trip` → `quality_check` | 1,N | Un trajet peut être associé à un ou plusieurs contrôles qualité. |

---

## 14. Index créés dans PostgreSQL

Des index sont ajoutés sur les principales clés étrangères afin d’améliorer les performances des jointures utilisées par l’API FastAPI et le dashboard Streamlit.

| Index | Colonne concernée |
|---|---|
| `idx_city_country_id` | `city.country_id` |
| `idx_station_city_id` | `station.city_id` |
| `idx_route_departure_station_id` | `route.departure_station_id` |
| `idx_route_arrival_station_id` | `route.arrival_station_id` |
| `idx_route_operator_id` | `route.operator_id` |
| `idx_trip_route_id` | `trip.route_id` |
| `idx_trip_train_type_id` | `trip.train_type_id` |
| `idx_trip_data_source_id` | `trip.data_source_id` |
| `idx_trip_stop_trip_id` | `trip_stop.trip_id` |
| `idx_trip_stop_station_id` | `trip_stop.station_id` |
| `idx_quality_check_trip_id` | `quality_check.trip_id` |

---

## 15. Ordre de chargement des tables

L’ordre de chargement respecte les dépendances entre clés primaires et clés étrangères.

```text
1. country
2. city
3. station
4. operator
5. train_type
6. data_source
7. route
8. trip
9. trip_stop
10. quality_check
```

Les tables de référence sont chargées en premier. Les tables métier dépendantes sont chargées ensuite.

---

## 16. Synthèse

Le dictionnaire des données montre que le modèle ObRail Europe est organisé autour des trajets ferroviaires.  
Les entités géographiques (`country`, `city`, `station`) servent de base au référentiel. Les entités métier (`route`, `trip`, `trip_stop`) permettent de représenter les itinéraires et les horaires. Les tables `data_source`, `train_type` et `quality_check` ajoutent la traçabilité, la classification jour/nuit et le contrôle qualité.

Ce modèle est adapté au besoin du projet : collecter, structurer, stocker et analyser des données ferroviaires issues de plusieurs sources hétérogènes.
