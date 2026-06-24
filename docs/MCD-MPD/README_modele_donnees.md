# README — Modèle conceptuel et physique des données

## 1. Objectif du livrable

Ce livrable présente le modèle de données du projet **ObRail Europe**.  
Il explique la logique de conception du modèle conceptuel, le passage vers le modèle physique PostgreSQL, les relations entre les tables et les choix effectués pour structurer les données ferroviaires.

Le but est de montrer que les données collectées par le pipeline ETL sont organisées dans une base relationnelle cohérente, contrôlable et exploitable par l’API FastAPI et le dashboard Streamlit.

---

## 2. Contenu attendu du dossier

Le dossier du livrable peut être organisé comme ceci :

```text
02_Modele_Conceptuel_Physique/
│
├── schema_relationnel_obrail_europe.png
├── create_tables.sql
├── dictionnaire_donnees.md
└── README_modele_donnees.md
```

### Rôle des fichiers

| Fichier | Description |
|---|---|
| `schema_relationnel_obrail_europe.png` | Schéma visuel des tables, clés primaires, clés étrangères et relations. |
| `create_tables.sql` | Script SQL permettant de créer le modèle physique dans PostgreSQL. |
| `dictionnaire_donnees.md` | Description détaillée des tables, colonnes, types, clés et contraintes. |
| `README_modele_donnees.md` | Explication générale du modèle conceptuel et physique. |

---

## 3. Logique globale du modèle

Le modèle de données ObRail Europe est construit autour de l’entité centrale **trip**, qui représente un trajet ferroviaire.

Un trajet :

- provient d’une source de données ;
- appartient à un type de train : `day` ou `night` ;
- circule sur une route ;
- possède une gare de départ et une gare d’arrivée à travers la route ;
- peut contenir plusieurs arrêts intermédiaires ;
- peut être associé à un contrôle qualité.

La logique générale peut être résumée ainsi :

```text
Source de données
      │
      ▼
Trajet ferroviaire
      │
      ├── Type de train : day / night
      ├── Route : gare de départ → gare d'arrivée
      ├── Arrêts intermédiaires
      └── Contrôle qualité
```

Le modèle est également relié à une structure géographique :

```text
Pays → Ville → Gare
```

Cette structure permet d’analyser les trajets par pays, ville, gare, opérateur ou type de train.

---

## 4. Modèle conceptuel des données

Le modèle conceptuel identifie les principales entités métier du projet et leurs relations.

### Entités principales

| Entité | Description métier |
|---|---|
| Pays | Zone géographique utilisée pour rattacher les villes et opérateurs. |
| Ville | Localisation d’une ou plusieurs gares. |
| Gare | Point ferroviaire utilisé comme départ, arrivée ou arrêt intermédiaire. |
| Opérateur | Entreprise ou organisme exploitant des routes ferroviaires. |
| Type de train | Classification entre train de jour et train de nuit. |
| Source de données | Origine des données intégrées dans l’ETL. |
| Route | Relation entre une gare de départ, une gare d’arrivée et un opérateur. |
| Trajet | Circulation ferroviaire concrète sur une route. |
| Arrêt de trajet | Gare desservie pendant un trajet, avec ordre de passage. |
| Contrôle qualité | Résultat des règles qualité appliquées aux trajets. |

### Relations métier

| Relation | Cardinalité | Explication |
|---|---:|---|
| Un pays contient des villes | 1,N | Une ville appartient à un seul pays. |
| Un pays possède des opérateurs | 1,N | Un opérateur est rattaché à un pays. |
| Une ville contient des gares | 1,N | Une gare appartient à une ville. |
| Un opérateur exploite des routes | 1,N | Une route est associée à un opérateur. |
| Une gare peut être utilisée dans plusieurs routes | 1,N | Une gare peut être départ ou arrivée de plusieurs routes. |
| Une route contient plusieurs trajets | 1,N | Plusieurs trajets peuvent circuler sur la même relation ferroviaire. |
| Un type de train concerne plusieurs trajets | 1,N | Les trajets sont classés en `day` ou `night`. |
| Une source fournit plusieurs trajets | 1,N | Chaque trajet garde la trace de sa source d’origine. |
| Un trajet possède plusieurs arrêts | 1,N | Les arrêts sont ordonnés grâce à `stop_order`. |
| Une gare apparaît dans plusieurs arrêts | 1,N | Une gare peut être desservie par plusieurs trajets. |
| Un trajet peut avoir des contrôles qualité | 1,N | Les contrôles qualité permettent d’identifier les anomalies. |

---

## 5. Modèle physique PostgreSQL

Le modèle physique est implémenté dans PostgreSQL à travers le fichier :

```text
create_tables.sql
```

Ce script :

1. supprime les anciennes tables si elles existent ;
2. recrée les tables dans le bon ordre ;
3. définit les clés primaires ;
4. définit les clés étrangères ;
5. ajoute les contraintes utiles ;
6. crée des index pour accélérer les requêtes.

### Tables créées

```text
country
city
station
operator
train_type
data_source
route
trip
trip_stop
quality_check
```

Le cœur du modèle est composé des tables :

```text
route → trip → trip_stop
```

La table `trip` fait le lien entre le référentiel ferroviaire, le type de train et la source de données.

---

## 6. Description synthétique des tables

### `country`

Stocke les pays présents dans les sources.  
Cette table est utilisée pour rattacher les villes et les opérateurs à une zone géographique.

### `city`

Stocke les villes.  
Chaque ville est reliée à un pays par la clé étrangère `country_id`.

### `station`

Stocke les gares.  
Chaque gare est reliée à une ville par `city_id`. Les coordonnées GPS sont conservées lorsqu’elles sont disponibles.

### `operator`

Stocke les opérateurs ferroviaires.  
Chaque opérateur est rattaché à un pays. Les noms d’origine sont conservés pour garder la traçabilité.

### `train_type`

Stocke les catégories de trains.  
Dans le projet, deux types principaux sont utilisés :

```text
day
night
```

### `data_source`

Stocke les sources utilisées par le pipeline ETL.  
Cette table permet de tracer l’origine des données : source, URL, format, date d’extraction et fichiers bruts.

### `route`

Stocke une relation ferroviaire entre une gare de départ, une gare d’arrivée et un opérateur.

### `trip`

Stocke les trajets ferroviaires.  
Cette table contient le code du trajet, la date de service, les horaires, la durée, le type de train et la source.

### `trip_stop`

Stocke les arrêts d’un trajet.  
Chaque arrêt est lié à un trajet et à une gare. L’ordre de passage est conservé avec `stop_order`.

### `quality_check`

Stocke les résultats des contrôles qualité.  
Elle permet de repérer les valeurs manquantes, les erreurs horaires, les doublons potentiels et le score qualité.

---

## 7. Justification des choix de modélisation

### Séparation entre route et trip

Une route représente une relation stable entre deux gares et un opérateur.  
Un trip représente une circulation concrète sur cette route, avec des horaires et une date de service.

Cette séparation évite de répéter inutilement les informations de départ, d’arrivée et d’opérateur dans chaque trajet.

### Création de tables géographiques

Le modèle utilise trois niveaux géographiques :

```text
country → city → station
```

Ce choix permet d’analyser les données par pays, par ville ou par gare. Il facilite aussi les visualisations du dashboard.

### Traçabilité des sources

La table `data_source` permet de relier les trajets à leur source d’origine.  
Ce choix est important car le projet utilise plusieurs sources de formats différents : CSV, JSON, GTFS et HTML.

### Classification jour / nuit

La table `train_type` permet de distinguer les trains de jour et les trains de nuit.  
Ce choix répond au besoin métier d’analyser la répartition des trajets et d’étudier les trains de nuit européens.

### Contrôle qualité séparé

Les contrôles qualité sont stockés dans une table dédiée `quality_check`.  
Cela permet de garder les anomalies sans mélanger les champs métier du trajet avec les résultats de contrôle.

---

## 8. Clés primaires et clés étrangères

Chaque table possède une clé primaire de type identifiant numérique.

Exemples :

```text
country.country_id
city.city_id
station.station_id
route.route_id
trip.trip_id
```

Les clés étrangères assurent la cohérence entre les tables.

Exemples :

```text
city.country_id → country.country_id
station.city_id → city.city_id
route.departure_station_id → station.station_id
route.arrival_station_id → station.station_id
trip.route_id → route.route_id
trip.train_type_id → train_type.train_type_id
trip.data_source_id → data_source.data_source_id
trip_stop.trip_id → trip.trip_id
quality_check.trip_id → trip.trip_id
```

Ces relations empêchent par exemple de charger un trajet qui référence une route inexistante ou un arrêt qui référence une gare absente.

---

## 9. Ordre de chargement des tables

Le chargement PostgreSQL doit respecter les dépendances entre tables. Les tables parentes sont chargées avant les tables enfants.

Ordre utilisé :

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

Cet ordre est utilisé dans le script de chargement `load_to_postgres.py`.

---

## 10. Index de performance

Des index sont créés sur les principales clés étrangères afin d’améliorer les performances des requêtes utilisées par l’API et le dashboard.

Les index concernent notamment :

```text
city.country_id
station.city_id
route.departure_station_id
route.arrival_station_id
route.operator_id
trip.route_id
trip.train_type_id
trip.data_source_id
trip_stop.trip_id
trip_stop.station_id
quality_check.trip_id
```

Ces index accélèrent les jointures entre tables, notamment pour afficher les trajets, les arrêts, les statistiques par source ou les visualisations du réseau ferroviaire.

---

## 11. Utilisation du modèle dans le projet

Le modèle est utilisé par trois parties du projet.

### Pipeline ETL

Les scripts de transformation produisent les fichiers CSV correspondant aux tables du modèle :

```text
country.csv
city.csv
station.csv
operator.csv
train_type.csv
data_source.csv
route.csv
trip.csv
trip_stop.csv
quality_check.csv
```

Ces fichiers sont ensuite chargés dans PostgreSQL.

### API FastAPI

L’API interroge PostgreSQL pour exposer les données sous forme d’endpoints REST :

```text
/trips
/stations
/operators
/sources
/train-types
/quality
/stats/quality
/stats/sources
```

### Dashboard Streamlit

Le dashboard utilise le modèle pour produire les indicateurs et visualisations :

- nombre de trajets ;
- répartition jour / nuit ;
- volume par source ;
- top opérateurs ;
- taux de valeurs manquantes ;
- réseau ferroviaire ;
- contrôles qualité.

---

## 12. Limites du modèle actuel

Le modèle répond au besoin du projet, mais certaines limites ont été identifiées.

### Normalisation des opérateurs

Les noms d’opérateurs sont conservés tels qu’ils apparaissent dans les sources. Certaines variantes d’un même opérateur peuvent donc apparaître séparément.

### Distance kilométrique

La colonne `distance_km` existe dans le modèle, mais elle n’est pas encore systématiquement alimentée.

### Estimation CO₂

La colonne `co2_estimated_kg` est prévue pour stocker une estimation CO₂, mais son calcul peut être amélioré avec une règle métier plus complète.

### Historisation

Le modèle ne stocke pas encore plusieurs versions d’une même extraction. Une évolution possible serait d’ajouter une table d’historique des imports.

---

## 13. Axes d’amélioration du modèle

Plusieurs améliorations peuvent être envisagées :

- créer une table de correspondance pour harmoniser les noms d’opérateurs ;
- calculer automatiquement `distance_km` à partir des coordonnées GPS ;
- alimenter `co2_estimated_kg` à partir de la distance et d’un facteur d’émission ;
- ajouter une table d’historisation des extractions ;
- enrichir les règles de contrôle qualité ;
- ajouter des contraintes supplémentaires selon les règles métier ;
- suivre les dates de mise à jour de chaque ligne chargée.

---

## 14. Conclusion

Le modèle conceptuel et physique du projet ObRail Europe permet de structurer des données ferroviaires issues de sources hétérogènes dans une base PostgreSQL cohérente.

La séparation entre les tables de référence, les tables métier et les tables de contrôle qualité rend le modèle lisible, maintenable et adapté à l’exploitation par une API REST et un dashboard.

Ce modèle constitue la base de l’entrepôt de données du projet. Il permet de transformer des fichiers bruts en données relationnelles exploitables pour l’analyse des trajets ferroviaires européens.
