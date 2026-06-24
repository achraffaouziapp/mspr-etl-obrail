# Documentation technique — Endpoints API ObRail Europe

Base URL en local :

```text
http://127.0.0.1:8000
```

Documentation interactive FastAPI :

```text
http://127.0.0.1:8000/docs
```

---

## 1. Vérification de l'API

### `GET /`

Vérifie que l'API est lancée.

Exemple :

```text
GET http://127.0.0.1:8000/
```

Réponse attendue :

```json
{
  "message": "Bienvenue sur l'API ObRail Europe",
  "documentation": "/docs",
  "status": "running"
}
```

---

### `GET /health`

Vérifie que l'API arrive à communiquer avec PostgreSQL.

Exemple :

```text
GET http://127.0.0.1:8000/health
```

Réponse attendue :

```json
{
  "api_status": "ok",
  "database_status": "ok"
}
```

---

## 2. Volumétrie de la base

### `GET /tables/counts`

Retourne le nombre de lignes par table.

Exemple :

```text
GET http://127.0.0.1:8000/tables/counts
```

Utilisation : vérifier que la base PostgreSQL est bien alimentée.

---

## 3. Référentiels

### `GET /train-types`

Retourne les types de trains disponibles.

Exemple :

```text
GET http://127.0.0.1:8000/train-types
```

Réponse attendue : types `day` et `night`.

---

### `GET /sources`

Retourne les sources de données intégrées par l'ETL.

Exemple :

```text
GET http://127.0.0.1:8000/sources
```

Utilisation : vérifier l'origine des données exploitées.

---

### `GET /countries`

Retourne la liste des pays présents dans la base.

Exemple :

```text
GET http://127.0.0.1:8000/countries
```

---

### `GET /operators`

Retourne les opérateurs ferroviaires.

Exemple :

```text
GET http://127.0.0.1:8000/operators
```

---

## 4. Consultation des gares

### `GET /stations`

Retourne les gares avec filtres optionnels.

Paramètres disponibles :

| Paramètre | Type | Description |
|---|---:|---|
| `country_code` | string | Filtre par code pays, par exemple `FR` |
| `city` | string | Filtre par ville |
| `limit` | integer | Nombre maximum de résultats, entre 1 et 1000 |
| `offset` | integer | Décalage pour la pagination |

Exemples :

```text
GET http://127.0.0.1:8000/stations
GET http://127.0.0.1:8000/stations?country_code=FR
GET http://127.0.0.1:8000/stations?city=Paris
GET http://127.0.0.1:8000/stations?city=Lyon&limit=20
```

---

## 5. Consultation des trajets

### `GET /trips`

Retourne les trajets ferroviaires avec filtres optionnels.

Paramètres disponibles :

| Paramètre | Type | Description |
|---|---:|---|
| `train_type` | string | `day` ou `night` |
| `departure_city` | string | Ville de départ |
| `arrival_city` | string | Ville d'arrivée |
| `source_id` | integer | Identifiant de la source de données |
| `limit` | integer | Nombre maximum de résultats, entre 1 et 1000 |
| `offset` | integer | Décalage pour la pagination |

Exemples :

```text
GET http://127.0.0.1:8000/trips
GET http://127.0.0.1:8000/trips?train_type=night
GET http://127.0.0.1:8000/trips?train_type=day
GET http://127.0.0.1:8000/trips?departure_city=Paris
GET http://127.0.0.1:8000/trips?arrival_city=Berlin
GET http://127.0.0.1:8000/trips?departure_city=Paris&arrival_city=Berlin&train_type=night
GET http://127.0.0.1:8000/trips?source_id=5&limit=50
```

Cette route répond directement au besoin de consultation des dessertes ferroviaires selon différents critères.

---

### `GET /trips/{trip_id}`

Retourne le détail d'un trajet.

Exemple :

```text
GET http://127.0.0.1:8000/trips/1
```

Réponse : informations du trajet, type de train, source, villes de départ et d'arrivée, opérateur, horaires, durée et score qualité.

---

### `GET /trips/{trip_id}/stops`

Retourne les arrêts d'un trajet.

Exemple :

```text
GET http://127.0.0.1:8000/trips/1/stops
```

Réponse : liste ordonnée des arrêts avec gare, ville, pays, horaires et décalages de jour.

---

## 6. Contrôle qualité

### `GET /quality`

Retourne les contrôles qualité des trajets.

Paramètres disponibles :

| Paramètre | Type | Description |
|---|---:|---|
| `only_errors` | boolean | Par défaut `true`, retourne uniquement les anomalies |
| `limit` | integer | Nombre maximum de résultats |
| `offset` | integer | Décalage pour la pagination |

Exemples :

```text
GET http://127.0.0.1:8000/quality
GET http://127.0.0.1:8000/quality?only_errors=false
GET http://127.0.0.1:8000/quality?limit=50
```

---

## 7. Statistiques

### `GET /stats/train-types`

Nombre de trajets par type de train.

```text
GET http://127.0.0.1:8000/stats/train-types
```

---

### `GET /stats/sources`

Nombre de trajets par source de données.

```text
GET http://127.0.0.1:8000/stats/sources
```

---

### `GET /stats/quality`

Statistiques globales de qualité : nombre de contrôles, anomalies et score moyen.

```text
GET http://127.0.0.1:8000/stats/quality
```

---

### `GET /stats/stations-by-country`

Nombre de gares par pays.

```text
GET http://127.0.0.1:8000/stats/stations-by-country
```

---

## 8. Codes de réponse attendus

| Code | Signification |
|---:|---|
| 200 | Requête réussie |
| 404 | Ressource introuvable, par exemple trajet absent |
| 422 | Paramètre invalide, par exemple `limit` hors plage |
| 500 | Erreur serveur ou problème de connexion à la base |

---

## 9. Remarque sur la sécurité

L'API est prévue pour un usage projet / démonstration. Elle ne contient pas d'authentification dans cette version. Si elle devait être exposée publiquement, il faudrait ajouter un mécanisme d'authentification, une gestion des droits et éventuellement une limitation du nombre de requêtes.
