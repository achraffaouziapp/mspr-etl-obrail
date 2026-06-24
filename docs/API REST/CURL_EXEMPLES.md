# Exemples de requêtes cURL — API ObRail Europe

Ces commandes peuvent être utilisées dans un terminal pour tester rapidement l'API.

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl "http://127.0.0.1:8000/tables/counts"
```

```bash
curl "http://127.0.0.1:8000/trips?train_type=night&limit=10"
```

```bash
curl "http://127.0.0.1:8000/trips?departure_city=Paris&limit=10"
```

```bash
curl "http://127.0.0.1:8000/trips?arrival_city=Berlin&limit=10"
```

```bash
curl "http://127.0.0.1:8000/trips?departure_city=Paris&arrival_city=Berlin&train_type=night"
```

```bash
curl "http://127.0.0.1:8000/trips/1"
```

```bash
curl "http://127.0.0.1:8000/trips/1/stops"
```

```bash
curl "http://127.0.0.1:8000/stats/train-types"
```

```bash
curl "http://127.0.0.1:8000/stats/quality"
```
