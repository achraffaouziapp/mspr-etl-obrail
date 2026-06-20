# Dockerisation complète — ObRail Europe

Ce dossier contient les fichiers nécessaires pour lancer le projet avec Docker.

## Conteneurs lancés

Le fichier `docker-compose.yml` lance trois services :

| Service | Rôle | Port |
|---|---|---:|
| `postgres` | Base de données PostgreSQL | 5432 |
| `api` | API FastAPI | 8000 |
| `dashboard` | Dashboard Streamlit | 8501 |

## Fichiers fournis

```text
docker-compose.yml
Dockerfile.api
Dockerfile.dashboard
requirements.txt
.dockerignore
README_DOCKER.md
```

Tous les fichiers Docker sont commentés pour expliquer le rôle de chaque bloc.

## Où placer les fichiers ?

Place-les à la racine du projet, au même niveau que :

```text
api/
dashboard/
scripts/
sql/
data/
.env
```

## Lancer tout le projet

```bash
docker compose up --build
```

Lancer en arrière-plan :

```bash
docker compose up --build -d
```

## Accès aux services

API FastAPI :

```text
http://localhost:8000
```

Documentation API :

```text
http://localhost:8000/docs
```

Dashboard Streamlit :

```text
http://localhost:8501
```

PostgreSQL :

```text
localhost:5432
```

## Point important : chargement des données

Docker lance PostgreSQL, l'API et le dashboard.  
Mais la base doit encore être alimentée avec les données ETL.

La première fois, il faut lancer PostgreSQL :

```bash
docker compose up -d postgres
```

Puis exécuter le pipeline ETL depuis la machine locale :

```bash
python scripts/extraction/extract_back_on_track.py
python scripts/extraction/extract_gtfs.py
python scripts/extraction/extract_gares_voyageurs.py
python scripts/extraction/extract_wikipedia_busiest_stations.py
python scripts/extraction/extract_european_sleeper.py

python scripts/transformation/transform_all_sources.py
python scripts/transformation/check_processed_data.py
python scripts/loading/load_to_postgres.py
```

Ensuite, lancer toute l'application :

```bash
docker compose up --build
```

## Pourquoi DB_HOST=postgres dans Docker ?

En local, une application Python utilise souvent :

```env
DB_HOST=localhost
```

Dans Docker, chaque service est dans un conteneur différent.  
Pour que l'API ou le dashboard contacte PostgreSQL, il faut utiliser le nom du service Docker :

```env
DB_HOST=postgres
```

C'est pour cela que cette variable est définie dans `docker-compose.yml`.

## Commandes utiles

Voir les conteneurs actifs :

```bash
docker ps
```

Voir les logs de l'API :

```bash
docker compose logs api
```

Voir les logs du dashboard :

```bash
docker compose logs dashboard
```

Voir les logs PostgreSQL :

```bash
docker compose logs postgres
```

Arrêter les conteneurs :

```bash
docker compose down
```

Supprimer aussi les données PostgreSQL :

```bash
docker compose down -v
```

Attention : `docker compose down -v` supprime le volume PostgreSQL.  
Il faudra donc recharger la base avec `load_to_postgres.py`.
