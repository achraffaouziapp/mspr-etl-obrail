# Preuve de base de données alimentée — ObRail Europe

## Objectif

Ce document accompagne le livrable **Base de données relationnelle alimentée**. Il sert à montrer que les données transformées ont bien été chargées dans une base PostgreSQL exploitable.

---

## Base utilisée

| Élément | Valeur |
|---|---|
| SGBD | PostgreSQL |
| Nom de la base | `obrail` |
| Client utilisé pour contrôle | DBeaver |
| Script de création | `sql/create_tables.sql` |
| Données chargées | CSV harmonisés dans `data_processed/` |
| Dump fourni | `obrail_postgres_dump.sql` |

---

## Volumétrie chargée

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

## Contrôles réalisés

Les contrôles suivants ont été réalisés après chargement :

- ouverture de la base dans DBeaver ;
- vérification de la présence des tables ;
- vérification du nombre de lignes par table ;
- consultation de quelques enregistrements ;
- exécution de requêtes SQL de jointure ;
- contrôle de la cohérence entre les tables principales : `route`, `trip`, `trip_stop`, `station` ;
- vérification de la table `quality_check`.

---

## Capture de preuve

La capture `screenshots/DBeaver.PNG` montre l'ouverture de la base et la consultation des tables dans DBeaver.

---

## Utilisation attendue

Une fois chargée, la base est utilisée par :

- l'API FastAPI pour exposer les données ;
- le dashboard Streamlit pour visualiser les indicateurs ;
- les requêtes SQL de contrôle et d'analyse.

La base est donc exploitable immédiatement pour consulter les trajets, les gares, les opérateurs, les sources de données et les contrôles qualité du projet ObRail Europe.
