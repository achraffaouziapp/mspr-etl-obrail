# mspr-etl-obrail



## Sources de données extraites

1. Back-on-Track Night Train Data
   - Format : JSON
   - Objectif : données sur les trains de nuit européens
   - Script : scripts/extraction/extract_back_on_track.py

2. SNCF GTFS
   - Format : GTFS ZIP
   - Objectif : horaires théoriques des trains SNCF
   - Script : scripts/extraction/extract_sncf_gtfs.py

3. Gares de voyageurs SNCF
   - Format : CSV
   - Objectif : référentiel des gares
   - Script : scripts/extraction/extract_gares_voyageurs.py

4. Wikipedia - Busiest railway stations in Europe
   - Format : scraping HTML
   - Objectif : enrichissement gares, villes, pays et démonstration scraping
   - Script : scripts/extraction/scrape_wikipedia_busiest_stations.py