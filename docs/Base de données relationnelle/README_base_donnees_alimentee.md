# Livrable 3 — Base de données relationnelle alimentée

## Objectif du livrable

Ce livrable fournit une base de données relationnelle PostgreSQL opérationnelle pour le projet **ObRail Europe**.
Elle contient un jeu de données harmonisé issu du pipeline ETL : extraction des sources, transformation vers un modèle commun, contrôle qualité, puis chargement dans PostgreSQL.

La base peut être reconstruite de deux manières :

1. avec le script SQL `sql/create_tables.sql` puis les CSV présents dans `data_processed/` ;
2. directement avec le dump `obrail_postgres_dump.sql`, qui contient le schéma et les données.

---

## Contenu du dossier

```text
03_Base_Donnees_Relationnelle_Alimentee/
├── sql/
│   ├── create_tables.sql
│   └── test_queries.sql
├── data_processed/
│   ├── country.csv
│   ├── city.csv
│   ├── station.csv
│   ├── operator.csv
│   ├── train_type.csv
│   ├── data_source.csv
│   ├── route.csv
│   ├── trip.csv
│   ├── trip_stop.csv
│   └── quality_check.csv
├── scripts/
│   └── load_to_postgres.py
├── screenshots/
│   └── DBeaver.PNG
├── docker-compose.yml
├── .env.example
├── table_row_counts.csv
├── obrail_postgres_dump.sql
├── README_base_donnees_alimentee.md
└── PREUVE_BASE_ALIMENTEE.md
```

---

## Tables alimentées

| Table | Nombre de lignes | Nombre de colonnes |
|---|---:|---:|
| `country` | 16 | 3 |
| `city` | 32 993 | 3 |
| `station` | 40 496 | 7 |
| `operator` | 37 | 4 |
| `train_type` | 2 | 2 |
| `data_source` | 4 | 8 |
| `route` | 4 099 | 5 |
| `trip` | 50 983 | 12 |
| `trip_stop` | 440 227 | 8 |
| `quality_check` | 50 983 | 9 |

---

## Méthode 1 — Reconstruction avec le dump PostgreSQL

Créer une base vide :

```bash
createdb -U postgres obrail
```

Restaurer le schéma et les données :

```bash
psql -U postgres -d obrail -f obrail_postgres_dump.sql
```

Cette méthode est la plus directe pour fournir une base préremplie.

---

## Méthode 2 — Reconstruction avec l'ETL

Lancer PostgreSQL avec Docker :

```bash
docker compose up -d
```

Créer les tables et charger les CSV transformés :

```bash
python scripts/load_to_postgres.py
```

Le script charge les tables dans l'ordre des dépendances afin de respecter les clés étrangères :

```text
country → city → station → operator → train_type → data_source → route → trip → trip_stop → quality_check
```

---

## Vérification dans DBeaver

La base a été consultée avec **DBeaver** afin de vérifier :

- la présence des tables ;
- les colonnes et les types de données ;
- l'insertion effective des lignes ;
- la cohérence générale des relations ;
- la possibilité d'exécuter des requêtes SQL sur les données chargées.

Une capture est fournie dans `screenshots/DBeaver.PNG`.

---

## Requêtes de contrôle

Le fichier `sql/test_queries.sql` contient des requêtes permettant de vérifier la base.

Exemples de contrôles :

```sql
SELECT COUNT(*) FROM country;
SELECT COUNT(*) FROM city;
SELECT COUNT(*) FROM station;
SELECT COUNT(*) FROM trip;
SELECT COUNT(*) FROM trip_stop;
SELECT COUNT(*) FROM quality_check;
```

Contrôle par type de train :

```sql
SELECT tt.type_name, COUNT(*) AS total_trips
FROM trip t
JOIN train_type tt ON t.train_type_id = tt.train_type_id
GROUP BY tt.type_name
ORDER BY total_trips DESC;
```

Contrôle par source de données :

```sql
SELECT ds.source_name, COUNT(*) AS total_trips
FROM trip t
JOIN data_source ds ON t.data_source_id = ds.data_source_id
GROUP BY ds.source_name
ORDER BY total_trips DESC;
```

---

## Exploitation par ObRail Europe

La base est directement exploitable par :

- l'API REST FastAPI ;
- le dashboard Streamlit ;
- un client SQL comme DBeaver ;
- des requêtes d'analyse sur les trajets, gares, opérateurs, sources et contrôles qualité.

Le modèle relationnel garantit la cohérence des données grâce aux clés primaires, clés étrangères et index définis dans `create_tables.sql`.
