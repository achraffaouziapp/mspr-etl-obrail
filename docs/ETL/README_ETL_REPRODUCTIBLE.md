# Runbook ETL — ObRail Europe

Ce document explique comment rejouer les scripts ETL de manière propre et reproductible.

## Objectif

Le pipeline ETL sert à mettre à jour l'entrepôt PostgreSQL à partir des sources ferroviaires.
Il suit toujours le même ordre : extraction, transformation, contrôle, chargement.

## Préparation

1. Installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Démarrer PostgreSQL :

```bash
docker compose up -d postgres
```

3. Créer le fichier `.env` à partir de `.env.example`.

## Ordre d'exécution

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

## Sorties attendues

- `data/raw/` : fichiers bruts et métadonnées par source.
- `data/processed/` : CSV relationnels prêts pour PostgreSQL.
- PostgreSQL : tables créées et alimentées.

## Pourquoi le pipeline est reproductible ?

- Les entrées et sorties sont rangées dans des dossiers fixes.
- Les sources sont documentées par des fichiers `metadata.json`.
- La transformation réécrit les CSV finaux à chaque exécution.
- Le chargement PostgreSQL recrée les tables à partir de `create_tables.sql`.
- Les paramètres de connexion sont placés dans `.env`.

## Mise à jour régulière

Pour rafraîchir l'entrepôt, il suffit de relancer les scripts dans le même ordre.
Les scripts `run_etl.sh` et `run_etl.ps1` reprennent cette séquence automatiquement.
