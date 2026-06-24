# Tests Postman — API ObRail Europe

## 1. Objectif

Les tests Postman servent à vérifier que l'API REST est fonctionnelle et que les endpoints retournent bien les données attendues depuis PostgreSQL.

Les captures `Postman 1.PNG` et `Postman 2.PNG` montrent des appels réalisés sur l'API pendant la validation du projet.

---

## 2. Préparation

Avant de tester l'API dans Postman :

1. lancer PostgreSQL ;
2. vérifier que la base `obrail` est alimentée ;
3. lancer l'API FastAPI :

```bash
python -m uvicorn api.main:app --reload
```

4. ouvrir Postman ;
5. utiliser la base URL suivante :

```text
http://127.0.0.1:8000
```

---

## 3. Tests de disponibilité

### Test 1 — API démarrée

```text
GET http://127.0.0.1:8000/
```

Résultat attendu :

```json
{
  "message": "Bienvenue sur l'API ObRail Europe",
  "documentation": "/docs",
  "status": "running"
}
```

---

### Test 2 — Connexion PostgreSQL

```text
GET http://127.0.0.1:8000/health
```

Résultat attendu :

```json
{
  "api_status": "ok",
  "database_status": "ok"
}
```

Ce test valide que FastAPI communique correctement avec PostgreSQL.

---

## 4. Tests métier principaux

### Test 3 — Consultation des trajets

```text
GET http://127.0.0.1:8000/trips
```

Objectif : vérifier que l'API retourne des trajets ferroviaires.

---

### Test 4 — Filtre par type de train

```text
GET http://127.0.0.1:8000/trips?train_type=night
```

Objectif : vérifier que l'API peut filtrer les trains de nuit.

---

### Test 5 — Filtre par ville de départ

```text
GET http://127.0.0.1:8000/trips?departure_city=Paris
```

Objectif : vérifier que l'API permet d'interroger les dessertes par ville de départ.

---

### Test 6 — Filtre par ville d'arrivée

```text
GET http://127.0.0.1:8000/trips?arrival_city=Berlin
```

Objectif : vérifier que l'API permet d'interroger les dessertes par ville d'arrivée.

---

### Test 7 — Filtre combiné

```text
GET http://127.0.0.1:8000/trips?departure_city=Paris&arrival_city=Berlin&train_type=night
```

Objectif : tester une recherche plus proche du besoin métier : trouver une desserte selon une origine, une destination et un type de train.

---

### Test 8 — Détail d'un trajet

```text
GET http://127.0.0.1:8000/trips/1
```

Objectif : vérifier que l'API retourne les détails d'un trajet précis.

---

### Test 9 — Arrêts d'un trajet

```text
GET http://127.0.0.1:8000/trips/1/stops
```

Objectif : vérifier la restitution des arrêts d'un trajet dans l'ordre.

---

## 5. Tests de référentiels et statistiques

```text
GET http://127.0.0.1:8000/stations?city=Paris
GET http://127.0.0.1:8000/sources
GET http://127.0.0.1:8000/train-types
GET http://127.0.0.1:8000/stats/train-types
GET http://127.0.0.1:8000/stats/sources
GET http://127.0.0.1:8000/stats/quality
```

Ces tests permettent de vérifier que les données de référence, les sources et les statistiques globales sont bien exposées.

---

## 6. Résultat attendu global

L'API est considérée comme fonctionnelle si :

- le endpoint `/health` retourne `database_status = ok` ;
- les endpoints de consultation retournent du JSON ;
- les filtres `departure_city`, `arrival_city` et `train_type` fonctionnent ;
- les endpoints de statistiques retournent des résultats cohérents ;
- les erreurs sont gérées, par exemple `404` si un trajet n'existe pas.

---

## 7. Preuves fournies

Le dossier `screenshots/` contient les captures de tests Postman :

```text
Postman 1.PNG
Postman 2.PNG
```

Ces captures servent de preuve visuelle que l'API a été testée en dehors du navigateur, avec un outil dédié aux tests d'API.
