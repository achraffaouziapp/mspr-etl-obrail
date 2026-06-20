# ObRail Europe — Projet ETL ferroviaire

## 1. Présentation du projet

**ObRail Europe** est un projet ETL autour de données ferroviaires européennes.  
L’objectif est de collecter plusieurs sources de données, de les transformer dans un modèle relationnel commun, de les charger dans PostgreSQL, puis de les exploiter à travers une API FastAPI et un dashboard Streamlit.

Le projet permet notamment de :

- centraliser des données provenant de plusieurs sources ferroviaires ;
- distinguer les trains de jour et les trains de nuit ;
- structurer les données dans un schéma relationnel PostgreSQL ;
- contrôler la qualité des trajets transformés ;
- exposer les données via une API REST ;
- visualiser les volumes, les opérateurs, les sources et le réseau ferroviaire dans un dashboard.

---

## 2. Sources de données utilisées

Le projet intègre plusieurs sources :

| Source | Format | Utilisation principale |
|---|---:|---|
| Back-on-Track Night Train Data | JSON | Trains de nuit européens |
| SNCF GTFS | GTFS ZIP | Horaires théoriques SNCF : TGV, Intercités, TER |
| Gares de voyageurs SNCF | CSV | Référentiel des gares françaises avec coordonnées |
| Wikipedia — Busiest railway stations in Europe | HTML scraping | Enrichissement des gares européennes |
| European Sleeper Timetable | HTML + CSV structuré | Trains de nuit European Sleeper |

Chaque extraction génère des fichiers bruts dans `data/raw/` ainsi qu’un fichier `metadata.json` permettant de tracer l’origine et la date d’extraction.

---

## 3. Architecture générale

Le projet suit une architecture ETL classique :

```text
Sources externes
      │
      ▼
Extraction
      │
      ▼
data/raw/
      │
      ▼
Transformation
      │
      ▼
data/processed/
      │
      ▼
Chargement PostgreSQL
      │
      ├── API FastAPI
      │
      └── Dashboard Streamlit
```

---

## 4. Structure du projet

```text
obrail-europe/
│
├── api/
│   ├── database.py
│   └── main.py
│
├── dashboard/
│   ├── app.py
│   └── visualisation.py
│
├── data/
│   ├── raw/
│   │   ├── back_on_track/
│   │   ├── sncf_gtfs/
│   │   ├── gares_voyageurs/
│   │   ├── wikipedia_busiest_stations_europe/
│   │   └── european_sleeper/
│   │
│   └── processed/
│       ├── country.csv
│       ├── city.csv
│       ├── station.csv
│       ├── operator.csv
│       ├── train_type.csv
│       ├── data_source.csv
│       ├── route.csv
│       ├── trip.csv
│       ├── trip_stop.csv
│       └── quality_check.csv
│
├── scripts/
│   ├── extraction/
│   │   ├── extract_back_on_track.py
│   │   ├── extract_gtfs.py
│   │   ├── extract_gares_voyageurs.py
│   │   ├── extract_wikipedia_busiest_stations.py
│   │   └── extract_european_sleeper.py
│   │
│   ├── transformation/
│   │   ├── transform_all_sources.py
│   │   └── check_processed_data.py
│   │
│   └── loading/
│       └── load_to_postgres.py
│
├── sql/
│   ├── create_tables.sql
│   └── test_queries.sql
│
├── docker-compose.yml
├── .env
└── README.md
```

---

## 5. Prérequis

Avant de lancer le projet, il faut avoir installé :

- Python 3.10 ou une version supérieure ;
- Docker et Docker Compose ;
- PostgreSQL, si vous ne souhaitez pas utiliser Docker ;
- Git, optionnel mais recommandé.

Le projet utilise notamment :

- `pandas` pour la manipulation des données ;
- `requests` pour télécharger les sources ;
- `beautifulsoup4` pour le scraping HTML ;
- `psycopg2` pour PostgreSQL ;
- `fastapi` et `uvicorn` pour l’API ;
- `streamlit` pour le dashboard ;
- `plotly` et `networkx` pour les visualisations ;
- `python-dotenv` pour charger la configuration ;
- `reverse_geocoder` et `pycountry` pour certains enrichissements géographiques.

---

## 6. Installation

### 6.1 Cloner ou ouvrir le projet

```bash
cd obrail-europe
```

### 6.2 Créer un environnement virtuel

Sous Windows :

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Sous macOS ou Linux :

```bash
python -m venv .venv
source .venv/bin/activate
```

### 6.3 Installer les dépendances

```bash
pip install pandas requests beautifulsoup4 psycopg2-binary fastapi uvicorn streamlit plotly networkx python-dotenv reverse_geocoder pycountry
```

Si le projet contient un fichier `requirements.txt`, il est préférable d’utiliser :

```bash
pip install -r requirements.txt
```

---

## 7. Configuration

La configuration de la base de données est placée dans le fichier `.env`.

Exemple :

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=obrail
DB_USER=postgres
DB_PASSWORD=postgres
```

Ces variables sont utilisées par :

- l’API FastAPI ;
- le dashboard Streamlit ;
- les scripts de connexion à PostgreSQL.

---

## 8. Lancement de PostgreSQL avec Docker

Le projet peut utiliser PostgreSQL via Docker Compose.

```bash
docker compose up -d
```

Pour vérifier que le conteneur est lancé :

```bash
docker ps
```

Pour arrêter PostgreSQL :

```bash
docker compose down
```

---

## 9. Pipeline ETL complet

### 9.1 Extraction des données brutes

Les scripts d’extraction téléchargent ou construisent les fichiers bruts dans `data/raw/`.

```bash
python scripts/extraction/extract_back_on_track.py
python scripts/extraction/extract_gtfs.py
python scripts/extraction/extract_gares_voyageurs.py
python scripts/extraction/extract_wikipedia_busiest_stations.py
python scripts/extraction/extract_european_sleeper.py
```

Chaque script d’extraction produit un dossier dédié à sa source et un fichier `metadata.json`.

---

### 9.2 Transformation des données

La transformation globale fusionne les sources et génère les fichiers normalisés dans `data/processed/`.

```bash
python scripts/transformation/transform_all_sources.py
```

Cette étape produit les fichiers CSV suivants :

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

Ces fichiers correspondent aux tables relationnelles qui seront ensuite chargées dans PostgreSQL.

---

### 9.3 Vérification des fichiers transformés

Avant de charger PostgreSQL, il est recommandé de vérifier les fichiers générés :

```bash
python scripts/transformation/check_processed_data.py
```

Ce script contrôle notamment :

- la présence des fichiers attendus ;
- le nombre de lignes et de colonnes ;
- les valeurs manquantes ;
- l’unicité des clés primaires ;
- la validité des clés étrangères ;
- la répartition des types de train ;
- les scores qualité.

---

### 9.4 Chargement dans PostgreSQL

Une fois les fichiers transformés vérifiés, il faut créer les tables et charger les CSV :

```bash
python scripts/loading/load_to_postgres.py
```

Le script exécute d’abord `sql/create_tables.sql`, puis charge les fichiers dans l’ordre nécessaire pour respecter les relations entre les tables.

---

## 10. Modèle relationnel

Le modèle relationnel est organisé autour des principales entités ferroviaires :

| Table | Rôle |
|---|---|
| `country` | Pays |
| `city` | Villes rattachées aux pays |
| `station` | Gares rattachées aux villes |
| `operator` | Opérateurs ferroviaires |
| `train_type` | Type de train : `day` ou `night` |
| `data_source` | Sources de données intégrées |
| `route` | Relation entre une gare de départ et une gare d’arrivée |
| `trip` | Trajet ferroviaire |
| `trip_stop` | Arrêts intermédiaires d’un trajet |
| `quality_check` | Contrôles qualité appliqués aux trajets |

Les tables `route`, `trip` et `trip_stop` constituent le cœur métier du projet.

---

## 11. Contrôle qualité

La table `quality_check` est générée pendant la transformation.  
Elle permet d’identifier les problèmes simples sur les trajets.

Les contrôles principaux sont :

- valeurs manquantes sur des champs essentiels ;
- durée invalide ou erreur horaire ;
- doublon potentiel sur le code du trajet.

Un score qualité est calculé sur 100 :

- départ à 100 ;
- retrait de points en cas d’anomalie ;
- score minimum limité à 0.

Ce score permet d’avoir une lecture rapide de la fiabilité des trajets chargés.

---

## 12. API FastAPI

L’API permet d’interroger les données transformées et chargées dans PostgreSQL.

### 12.1 Lancer l’API

```bash
python -m uvicorn api.main:app --reload
```

L’API est ensuite disponible à l’adresse :

```text
http://127.0.0.1:8000
```

La documentation interactive est disponible ici :

```text
http://127.0.0.1:8000/docs
```

---

### 12.2 Principaux endpoints

| Endpoint | Description |
|---|---|
| `/` | Vérifie que l’API est lancée |
| `/health` | Vérifie la connexion entre l’API et PostgreSQL |
| `/tables/counts` | Retourne le nombre de lignes par table |
| `/train-types` | Liste les types de train |
| `/sources` | Liste les sources de données |
| `/countries` | Liste les pays |
| `/stations` | Liste les gares avec filtres |
| `/operators` | Liste les opérateurs |
| `/trips` | Liste les trajets avec filtres |
| `/trips/{trip_id}` | Retourne le détail d’un trajet |
| `/trips/{trip_id}/stops` | Retourne les arrêts d’un trajet |
| `/quality` | Retourne les contrôles qualité |
| `/stats/train-types` | Statistiques par type de train |
| `/stats/sources` | Statistiques par source |
| `/stats/quality` | Statistiques qualité globales |
| `/stats/stations-by-country` | Nombre de gares par pays |

---

### 12.3 Exemples d’appels API

Liste des trajets :

```text
http://127.0.0.1:8000/trips
```

Trajets de nuit :

```text
http://127.0.0.1:8000/trips?train_type=night
```

Trajets au départ de Paris :

```text
http://127.0.0.1:8000/trips?departure_city=Paris
```

Détail du trajet 1 :

```text
http://127.0.0.1:8000/trips/1
```

Arrêts du trajet 1 :

```text
http://127.0.0.1:8000/trips/1/stops
```

---

## 13. Dashboard Streamlit

Le dashboard permet de visualiser les données de manière interactive.

### 13.1 Lancer le dashboard

```bash
python -m streamlit run dashboard/app.py
```

Le dashboard s’ouvre ensuite dans le navigateur.

---

### 13.2 Pages du dashboard

Le dashboard est organisé en trois onglets.

#### Vue exécutive

Cette page donne une vision globale du projet :

- nombre total de trajets ;
- nombre de gares ;
- nombre de routes ;
- nombre d’arrêts ;
- nombre d’anomalies ;
- score qualité moyen ;
- complétude des coordonnées GPS.

Elle affiche aussi :

- le volume de trajets par source ;
- le volume de trajets par type de train ;
- le top des pays par nombre de gares.

#### Analyse transport

Cette page analyse les données selon une logique métier :

- top des opérateurs par nombre de trajets ;
- répartition hiérarchique source → type de train.

Le diagramme Sunburst permet de voir quelle source contient quels types de trains.

#### Réseau ferroviaire

Cette page permet d’explorer les connexions entre villes.

Elle contient :

- un graphe des connexions ferroviaires les plus fréquentes ;
- une table d’exploration des trajets ;
- des filtres par type de train, source, ville de départ et ville d’arrivée ;
- un bouton de téléchargement des trajets filtrés.

---

## 14. Ordre recommandé d’exécution

Pour exécuter tout le projet depuis zéro :

```bash
docker compose up -d

python scripts/extraction/extract_back_on_track.py
python scripts/extraction/extract_gtfs.py
python scripts/extraction/extract_gares_voyageurs.py
python scripts/extraction/extract_wikipedia_busiest_stations.py
python scripts/extraction/extract_european_sleeper.py

python scripts/transformation/transform_all_sources.py
python scripts/transformation/check_processed_data.py
python scripts/loading/load_to_postgres.py

python -m uvicorn api.main:app --reload
python -m streamlit run dashboard/app.py
```

Il est conseillé de lancer l’API et le dashboard dans deux terminaux séparés.

---

## 15. Tests SQL

Le fichier `sql/test_queries.sql` contient des requêtes utiles pour vérifier le contenu de la base.

Exemples de contrôles possibles :

- compter les lignes par table ;
- vérifier les trajets de nuit ;
- inspecter les trajets European Sleeper ;
- contrôler les anomalies qualité ;
- vérifier les relations entre les trajets, les routes et les gares.

Ces requêtes peuvent être exécutées dans un client PostgreSQL ou directement depuis pgAdmin.

---

## 16. Problèmes fréquents

### PostgreSQL n’est pas connecté

Vérifier que le conteneur Docker est lancé :

```bash
docker ps
```

Puis relancer si nécessaire :

```bash
docker compose up -d
```

---

### Erreur de connexion à la base

Vérifier les variables du fichier `.env` :

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=obrail
DB_USER=postgres
DB_PASSWORD=postgres
```

---

### Les tables sont vides

Relancer le chargement :

```bash
python scripts/loading/load_to_postgres.py
```

---

### Les fichiers `data/processed/` sont absents

Relancer la transformation :

```bash
python scripts/transformation/transform_all_sources.py
```

---

### Une extraction échoue

Certaines sources sont en ligne et peuvent être temporairement indisponibles.  
Il faut vérifier la connexion Internet, puis relancer le script concerné.

---

## 17. Limites connues

Certaines limites sont identifiées dans la version actuelle :

- les noms d’opérateurs sont conservés tels qu’ils apparaissent dans les sources ;
- certaines variantes d’un même opérateur peuvent apparaître séparément ;
- les distances kilométriques ne sont pas encore calculées ;
- les émissions CO₂ sont prévues dans le modèle mais pas encore estimées ;
- certaines sources peuvent changer de structure dans le temps ;
- le scraping Wikipedia dépend de la structure HTML de la page source.

---

## 18. Axes d’amélioration

Plusieurs améliorations peuvent être envisagées :

### Normalisation avancée des opérateurs

Certaines sources utilisent plusieurs libellés pour une même entité métier.  
Par exemple, des variantes de SNCF Voyageurs peuvent apparaître séparément.

Une amélioration possible serait de créer une table de correspondance permettant de regrouper ces variantes sous un nom harmonisé, tout en conservant le libellé d’origine pour la traçabilité.

### Calcul des distances

La colonne `distance_km` pourrait être alimentée en calculant la distance entre les gares de départ et d’arrivée à partir des coordonnées GPS.

### Estimation CO₂

La colonne `co2_estimated_kg` pourrait être remplie à partir d’une règle métier basée sur la distance et un facteur moyen d’émission ferroviaire.

### Historisation des extractions

Il serait possible de conserver plusieurs versions des extractions afin de suivre l’évolution des sources dans le temps.

### Amélioration du contrôle qualité

Les règles qualité pourraient être enrichies avec :

- contrôle des coordonnées ;
- contrôle des pays et villes inconnus ;
- détection plus fine des doublons ;
- cohérence entre arrêts et durée du trajet ;
- contrôle des trajets anormalement longs ou courts.

### Industrialisation

Le pipeline pourrait être automatisé avec :

- Airflow ;
- Prefect ;
- cron ;
- GitHub Actions ;
- Dockerisation complète de l’API et du dashboard.

---

## 19. Technologies utilisées

| Technologie | Rôle |
|---|---|
| Python | Langage principal |
| pandas | Transformation et nettoyage des données |
| requests | Téléchargement des sources |
| BeautifulSoup | Scraping HTML |
| PostgreSQL | Base relationnelle |
| psycopg2 | Connexion Python/PostgreSQL |
| FastAPI | API REST |
| Uvicorn | Serveur de développement API |
| Streamlit | Dashboard interactif |
| Plotly | Graphiques |
| NetworkX | Graphe de réseau |
| Docker Compose | Lancement de PostgreSQL |
| python-dotenv | Lecture du fichier `.env` |

---

## 20. Conclusion

ObRail Europe met en place une chaîne complète de traitement de données ferroviaires :

1. extraction de sources hétérogènes ;
2. transformation vers un modèle commun ;
3. contrôle qualité ;
4. chargement PostgreSQL ;
5. exposition API ;
6. visualisation dans un dashboard.

Le projet montre comment passer de données brutes issues de plusieurs sources à une base relationnelle exploitable et à des outils de consultation adaptés à l’analyse métier.
