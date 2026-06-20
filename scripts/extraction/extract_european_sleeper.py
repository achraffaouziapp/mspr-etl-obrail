"""
Extrait et structure les données European Sleeper utilisées dans le projet.

La page officielle du timetable est téléchargée pour garder la preuve de la source.
Les gares, routes et horaires nécessaires à l'ETL sont ensuite écrits dans des CSV bruts.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw" / "european_sleeper"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Données structurées utilisées pour produire une source night reproductible.
SOURCE_URL = "https://www.europeansleeper.eu/timetable"


STATIONS = [
    {
        "station_code": "ES_BRUXELLES_MIDI",
        "station_name": "Bruxelles-Midi",
        "city_name": "Brussels",
        "country_name": "Belgium",
        "country_code": "BE",
        "latitude": 50.8359,
        "longitude": 4.3365,
        "timezone": "Europe/Brussels",
    },
    {
        "station_code": "ES_ANTWERPEN_CENTRAAL",
        "station_name": "Antwerpen-Centraal",
        "city_name": "Antwerp",
        "country_name": "Belgium",
        "country_code": "BE",
        "latitude": 51.2172,
        "longitude": 4.4211,
        "timezone": "Europe/Brussels",
    },
    {
        "station_code": "ES_ROOSENDAAL",
        "station_name": "Roosendaal",
        "city_name": "Roosendaal",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 51.5406,
        "longitude": 4.4580,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_ROTTERDAM_CENTRAAL",
        "station_name": "Rotterdam Centraal",
        "city_name": "Rotterdam",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 51.9244,
        "longitude": 4.4697,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_DEN_HAAG_HS",
        "station_name": "Den Haag HS",
        "city_name": "The Hague",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 52.0699,
        "longitude": 4.3229,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_AMSTERDAM_CENTRAAL",
        "station_name": "Amsterdam Centraal",
        "city_name": "Amsterdam",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 52.3791,
        "longitude": 4.9003,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_UTRECHT_CENTRAAL",
        "station_name": "Utrecht Centraal",
        "city_name": "Utrecht",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 52.0894,
        "longitude": 5.1103,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_ARNHEM_CENTRAAL",
        "station_name": "Arnhem Centraal",
        "city_name": "Arnhem",
        "country_name": "Netherlands",
        "country_code": "NL",
        "latitude": 51.9851,
        "longitude": 5.8987,
        "timezone": "Europe/Amsterdam",
    },
    {
        "station_code": "ES_BERLIN_GESUNDBRUNNEN",
        "station_name": "Berlin Gesundbrunnen",
        "city_name": "Berlin",
        "country_name": "Germany",
        "country_code": "DE",
        "latitude": 52.5486,
        "longitude": 13.3893,
        "timezone": "Europe/Berlin",
    },
    {
        "station_code": "ES_BERLIN_SPANDAU",
        "station_name": "Berlin-Spandau",
        "city_name": "Berlin",
        "country_name": "Germany",
        "country_code": "DE",
        "latitude": 52.5349,
        "longitude": 13.1974,
        "timezone": "Europe/Berlin",
    },
    {
        "station_code": "ES_DRESDEN_HBF",
        "station_name": "Dresden Hbf",
        "city_name": "Dresden",
        "country_name": "Germany",
        "country_code": "DE",
        "latitude": 51.0409,
        "longitude": 13.7326,
        "timezone": "Europe/Berlin",
    },
    {
        "station_code": "ES_BAD_SCHANDAU",
        "station_name": "Bad Schandau",
        "city_name": "Bad Schandau",
        "country_name": "Germany",
        "country_code": "DE",
        "latitude": 50.9189,
        "longitude": 14.1394,
        "timezone": "Europe/Berlin",
    },
    {
        "station_code": "ES_DECIN_HLN",
        "station_name": "Decin hl.n.",
        "city_name": "Decin",
        "country_name": "Czechia",
        "country_code": "CZ",
        "latitude": 50.7730,
        "longitude": 14.2010,
        "timezone": "Europe/Prague",
    },
    {
        "station_code": "ES_USTI_NAD_LABEM_HLN",
        "station_name": "Usti nad Labem hl.n.",
        "city_name": "Usti nad Labem",
        "country_name": "Czechia",
        "country_code": "CZ",
        "latitude": 50.6605,
        "longitude": 14.0430,
        "timezone": "Europe/Prague",
    },
    {
        "station_code": "ES_PRAGUE_HLN",
        "station_name": "Prague hl.n. (main station)",
        "city_name": "Prague",
        "country_name": "Czechia",
        "country_code": "CZ",
        "latitude": 50.0830,
        "longitude": 14.4350,
        "timezone": "Europe/Prague",
    },
    {
        "station_code": "ES_LIEGE_GUILLEMINS",
        "station_name": "Liège-Guillemins",
        "city_name": "Liège",
        "country_name": "Belgium",
        "country_code": "BE",
        "latitude": 50.6242,
        "longitude": 5.5668,
        "timezone": "Europe/Brussels",
    },
    {
        "station_code": "ES_MONS",
        "station_name": "Mons",
        "city_name": "Mons",
        "country_name": "Belgium",
        "country_code": "BE",
        "latitude": 50.4542,
        "longitude": 3.9420,
        "timezone": "Europe/Brussels",
    },
    {
        "station_code": "ES_AULNOYE_AYMERIES",
        "station_name": "Aulnoye-Aymeries",
        "city_name": "Aulnoye-Aymeries",
        "country_name": "France",
        "country_code": "FR",
        "latitude": 50.2010,
        "longitude": 3.8380,
        "timezone": "Europe/Paris",
    },
    {
        "station_code": "ES_PARIS_NORD",
        "station_name": "Paris Nord",
        "city_name": "Paris",
        "country_name": "France",
        "country_code": "FR",
        "latitude": 48.8809,
        "longitude": 2.3553,
        "timezone": "Europe/Paris",
    },
]


ROUTE_PATTERNS = [
    {
        "train_code": "ES 453",
        "route_name": "Brussels - Prague",
        "direction": "Bruxelles-Midi -> Prague hl.n.",
        "operator_name": "European Sleeper",
        "operator_code": "ES",
        "operator_country_name": "Netherlands",
        "operator_country_code": "NL",
        "origin_station_code": "ES_BRUXELLES_MIDI",
        "destination_station_code": "ES_PRAGUE_HLN",
        "operating_days": "mon,wed,fri",
    },
    {
        "train_code": "ES 452",
        "route_name": "Prague - Brussels",
        "direction": "Prague hl.n. -> Bruxelles-Midi",
        "operator_name": "European Sleeper",
        "operator_code": "ES",
        "operator_country_name": "Netherlands",
        "operator_country_code": "NL",
        "origin_station_code": "ES_PRAGUE_HLN",
        "destination_station_code": "ES_BRUXELLES_MIDI",
        "operating_days": "tue,thu,sun",
    },
    {
        "train_code": "ES 474",
        "route_name": "Berlin - Paris",
        "direction": "Berlin-Spandau -> Paris Nord",
        "operator_name": "European Sleeper",
        "operator_code": "ES",
        "operator_country_name": "Netherlands",
        "operator_country_code": "NL",
        "origin_station_code": "ES_BERLIN_SPANDAU",
        "destination_station_code": "ES_PARIS_NORD",
        "operating_days": "mon,wed,fri",
    },
    {
        "train_code": "ES 475",
        "route_name": "Paris - Berlin",
        "direction": "Paris Nord -> Berlin-Spandau",
        "operator_name": "European Sleeper",
        "operator_code": "ES",
        "operator_country_name": "Netherlands",
        "operator_country_code": "NL",
        "origin_station_code": "ES_PARIS_NORD",
        "destination_station_code": "ES_BERLIN_SPANDAU",
        "operating_days": "tue,thu,sun",
    },
]


STOP_TIMES = [

    ["ES 453", 1, "ES_BRUXELLES_MIDI", "", "19:22:00", "", 0],
    ["ES 453", 2, "ES_ANTWERPEN_CENTRAAL", "19:58:00", "20:02:00", 0, 0],
    ["ES 453", 3, "ES_ROOSENDAAL", "20:41:00", "20:44:00", 0, 0],
    ["ES 453", 4, "ES_ROTTERDAM_CENTRAAL", "21:18:00", "21:20:00", 0, 0],
    ["ES 453", 5, "ES_DEN_HAAG_HS", "21:37:00", "21:39:00", 0, 0],
    ["ES 453", 6, "ES_AMSTERDAM_CENTRAAL", "22:18:00", "22:30:00", 0, 0],
    ["ES 453", 7, "ES_UTRECHT_CENTRAAL", "22:55:00", "22:58:00", 0, 0],
    ["ES 453", 8, "ES_ARNHEM_CENTRAAL", "23:34:00", "23:43:00", 0, 0],
    ["ES 453", 9, "ES_BERLIN_GESUNDBRUNNEN", "06:00:00", "06:00:00", 1, 1],
    ["ES 453", 10, "ES_DRESDEN_HBF", "09:31:00", "09:33:00", 1, 1],
    ["ES 453", 11, "ES_BAD_SCHANDAU", "09:57:00", "09:59:00", 1, 1],
    ["ES 453", 12, "ES_DECIN_HLN", "10:14:00", "10:15:00", 1, 1],
    ["ES 453", 13, "ES_USTI_NAD_LABEM_HLN", "10:45:00", "10:45:00", 1, 1],
    ["ES 453", 14, "ES_PRAGUE_HLN", "11:45:00", "", 1, ""],


    ["ES 452", 1, "ES_PRAGUE_HLN", "", "18:04:00", "", 0],
    ["ES 452", 2, "ES_USTI_NAD_LABEM_HLN", "19:04:00", "19:05:00", 0, 0],
    ["ES 452", 3, "ES_DECIN_HLN", "19:35:00", "19:36:00", 0, 0],
    ["ES 452", 4, "ES_BAD_SCHANDAU", "19:51:00", "19:53:00", 0, 0],
    ["ES 452", 5, "ES_DRESDEN_HBF", "20:17:00", "20:19:00", 0, 0],
    ["ES 452", 6, "ES_BERLIN_GESUNDBRUNNEN", "23:00:00", "23:08:00", 0, 0],
    ["ES 452", 7, "ES_ARNHEM_CENTRAAL", "06:25:00", "06:33:00", 1, 1],
    ["ES 452", 8, "ES_UTRECHT_CENTRAAL", "07:17:00", "07:20:00", 1, 1],
    ["ES 452", 9, "ES_AMSTERDAM_CENTRAAL", "07:50:00", "08:02:00", 1, 1],
    ["ES 452", 10, "ES_DEN_HAAG_HS", "08:38:00", "08:40:00", 1, 1],
    ["ES 452", 11, "ES_ROTTERDAM_CENTRAAL", "08:58:00", "09:00:00", 1, 1],
    ["ES 452", 12, "ES_ROOSENDAAL", "09:34:00", "09:37:00", 1, 1],
    ["ES 452", 13, "ES_ANTWERPEN_CENTRAAL", "10:16:00", "10:20:00", 1, 1],
    ["ES 452", 14, "ES_BRUXELLES_MIDI", "11:00:00", "", 1, ""],


    ["ES 474", 1, "ES_BERLIN_SPANDAU", "", "19:48:00", "", 0],
    ["ES 474", 2, "ES_LIEGE_GUILLEMINS", "05:45:00", "05:47:00", 1, 1],
    ["ES 474", 3, "ES_BRUXELLES_MIDI", "07:08:00", "07:21:00", 1, 1],
    ["ES 474", 4, "ES_MONS", "07:59:00", "08:03:00", 1, 1],
    ["ES 474", 5, "ES_AULNOYE_AYMERIES", "08:35:00", "08:56:00", 1, 1],
    ["ES 474", 6, "ES_PARIS_NORD", "11:28:00", "", 1, ""],


    ["ES 475", 1, "ES_PARIS_NORD", "", "19:12:00", "", 0],
    ["ES 475", 2, "ES_AULNOYE_AYMERIES", "21:25:00", "21:45:00", 0, 0],
    ["ES 475", 3, "ES_MONS", "22:18:00", "22:22:00", 0, 0],
    ["ES 475", 4, "ES_BRUXELLES_MIDI", "23:02:00", "23:16:00", 0, 0],
    ["ES 475", 5, "ES_LIEGE_GUILLEMINS", "00:41:00", "00:43:00", 1, 1],
    ["ES 475", 6, "ES_BERLIN_SPANDAU", "10:14:00", "", 1, ""],
]


def download_source_page() -> dict:
    """
    Télécharge la page officielle European Sleeper et la sauvegarde en HTML.

    Cette copie brute sert de preuve de source et complète les fichiers structurés utilisés ensuite.
    """
    response = requests.get(
        SOURCE_URL,
        timeout=30,
        headers={"User-Agent": "ObRail MSPR ETL educational project"}
    )
    response.raise_for_status()

    html_path = RAW_DIR / "timetable.html"
    html_path.write_text(response.text, encoding="utf-8")

    return {
        "status_code": response.status_code,
        "content_length": len(response.text),
        "html_file": str(html_path),
    }


def main():
    """
    Point d'entrée du script.

    Cette fonction organise les étapes dans le bon ordre et affiche des messages de suivi dans le terminal.
    """
    print("Extraction European Sleeper...")

    download_info = download_source_page()

    stations_df = pd.DataFrame(STATIONS)
    routes_df = pd.DataFrame(ROUTE_PATTERNS)
    stop_times_df = pd.DataFrame(
        STOP_TIMES,
        columns=[
            "train_code",
            "stop_order",
            "station_code",
            "arrival_time",
            "departure_time",
            "arrival_day_offset",
            "departure_day_offset",
        ]
    )

    stations_df.to_csv(RAW_DIR / "european_sleeper_stations.csv", index=False, encoding="utf-8")
    routes_df.to_csv(RAW_DIR / "european_sleeper_routes.csv", index=False, encoding="utf-8")
    stop_times_df.to_csv(RAW_DIR / "european_sleeper_stop_times.csv", index=False, encoding="utf-8")

    metadata = {
        "source_name": "European Sleeper Timetable",
        "source_url": SOURCE_URL,
        "source_format": "HTML + structured CSV",
        "extraction_date": datetime.now(timezone.utc).isoformat(),
        "licence": "Public timetable page",
        "raw_files": [
            "timetable.html",
            "european_sleeper_stations.csv",
            "european_sleeper_routes.csv",
            "european_sleeper_stop_times.csv",
        ],
        "download_info": download_info,
        "import_status": "OK",
    }

    with open(RAW_DIR / "metadata.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print("[OK] Extraction European Sleeper terminée")
    print(f"Dossier : {RAW_DIR}")


if __name__ == "__main__":
    main()
