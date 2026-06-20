from pathlib import Path
from datetime import datetime, date
import json
import re

import pandas as pd


# ============================================================
# Chemins du projet
# ============================================================

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

BACK_ON_TRACK_DIR = RAW_DIR / "back_on_track"
SNCF_GTFS_DIR = RAW_DIR / "sncf_gtfs"
GARES_DIR = RAW_DIR / "gares_voyageurs"
WIKI_DIR = RAW_DIR / "wikipedia_busiest_stations_europe"


# ============================================================
# Fonctions utilitaires
# ============================================================

def ensure_output_dir():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def normalize_column_name(column_name: str) -> str:
    """
    Transforme un nom de colonne en snake_case.
    Exemple : "Stop Name" -> "stop_name"
    """
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name)
    column_name = column_name.strip("_")
    return column_name


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def clean_string(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none", "null"]:
        return None

    return value


def get_column(df: pd.DataFrame, possible_names: list[str]):
    """
    Retourne le vrai nom d'une colonne en cherchant dans plusieurs noms possibles.
    """
    normalized = [normalize_column_name(name) for name in possible_names]

    for col in normalized:
        if col in df.columns:
            return col

    return None


def get_series(df: pd.DataFrame, possible_names: list[str], default_value=None) -> pd.Series:
    col = get_column(df, possible_names)

    if col is None:
        return pd.Series([default_value] * len(df))

    return df[col]


def save_csv(df: pd.DataFrame, file_name: str):
    output_path = PROCESSED_DIR / file_name
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[OK] {file_name} généré : {len(df)} lignes")

def convert_nullable_integer_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Convertit des colonnes en entiers nullable.
    Exemple :
    0.0 -> 0
    1.0 -> 1
    NaN -> valeur vide dans le CSV
    """
    df = df.copy()

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    return df

def read_csv_auto(path: Path) -> pd.DataFrame:
    """
    Lit un CSV avec détection automatique du séparateur.
    """
    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, sep=None, engine="python", dtype=str)
    except Exception:
        df = pd.read_csv(path, dtype=str)

    return normalize_columns(df)



def read_json_auto(path: Path) -> pd.DataFrame:
    """
    Lit un JSON pouvant être :
    - une liste de dictionnaires
    - un dictionnaire simple
    - un dictionnaire contenant une liste de dictionnaires
    - un dictionnaire de dictionnaires, très fréquent avec Back-on-Track
    """
    if not path.exists():
        return pd.DataFrame()

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Cas 1 : liste JSON
    if isinstance(data, list):
        if len(data) == 0:
            return pd.DataFrame()

        if all(isinstance(item, dict) for item in data):
            return normalize_columns(pd.json_normalize(data))

        return normalize_columns(pd.DataFrame({"value": data}))

    # Cas 2 : dictionnaire JSON
    if isinstance(data, dict):

        # Cas 2A : dictionnaire de dictionnaires
        # Exemple :
        # {
        #   "stop_1": {"name": "..."},
        #   "stop_2": {"name": "..."}
        # }
        if len(data) > 0 and all(isinstance(value, dict) for value in data.values()):
            rows = []

            for key, value in data.items():
                row = value.copy()
                row["_source_key"] = key
                rows.append(row)

            return normalize_columns(pd.json_normalize(rows))

        # Cas 2B : dictionnaire contenant une liste de dictionnaires
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                if all(isinstance(item, dict) for item in value):
                    return normalize_columns(pd.json_normalize(value))

        # Cas 2C : dictionnaire simple, comme metadata.json
        return normalize_columns(pd.DataFrame([data]))

    return pd.DataFrame()




def gtfs_time_to_minutes(value):
    """
    Convertit une heure en minutes.

    Formats acceptés :
    - GTFS classique : 23:30:00
    - GTFS avec dépassement de 24h : 25:10:00
    - Back-on-Track datetime : 1899-12-30T05:36:00.000Z
    """
    value = clean_string(value)

    if value is None:
        return None

    value = str(value).strip()

    # Cas 1 : format GTFS HH:MM:SS ou HH:MM
    gtfs_match = re.match(r"^(\d{1,3}):(\d{2})(?::(\d{2}))?$", value)

    if gtfs_match:
        hours = int(gtfs_match.group(1))
        minutes = int(gtfs_match.group(2))
        seconds = int(gtfs_match.group(3)) if gtfs_match.group(3) else 0

        return hours * 60 + minutes + round(seconds / 60)

    # Cas 2 : format datetime Back-on-Track
    try:
        parsed = pd.to_datetime(value, errors="coerce", utc=True)

        if pd.isna(parsed):
            return None

        # Back-on-Track encode souvent les heures avec la date 1899-12-30.
        # Si la date est 1899-12-31, on considère que c'est le lendemain.
        base_date = pd.Timestamp("1899-12-30", tz="UTC").date()

        if parsed.year == 1899:
            day_offset = (parsed.date() - base_date).days
        else:
            day_offset = 0

        if day_offset < 0:
            day_offset = 0

        return (
            day_offset * 1440
            + parsed.hour * 60
            + parsed.minute
            + round(parsed.second / 60)
        )

    except Exception:
        return None


def gtfs_time_to_sql_time_and_offset(value):
    """
    Convertit une heure en heure SQL + offset de jour.

    Exemples :
    - 25:10:00 -> 01:10:00, offset 1
    - 1899-12-30T22:48:00.000Z -> 22:48:00, offset 0
    - 1899-12-31T01:10:00.000Z -> 01:10:00, offset 1
    """
    total_minutes = gtfs_time_to_minutes(value)

    if total_minutes is None:
        return None, None

    day_offset = total_minutes // 1440
    minutes_in_day = total_minutes % 1440

    hours = minutes_in_day // 60
    minutes = minutes_in_day % 60

    return f"{hours:02d}:{minutes:02d}:00", int(day_offset)

def build_key(*values):
    cleaned = [str(v).strip().lower() for v in values if v is not None and str(v).strip() != ""]
    return "|".join(cleaned)

# ============================================================
# Correction des codes pays
# ============================================================

COUNTRY_CODE_BY_NAME = {
    "Austria": "AT",
    "Belgium": "BE",
    "Czechia": "CZ",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Netherlands": "NL",
    "Norway": "NO",
    "Russia": "RU",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "United Kingdom": "GB",
    "UK": "GB",
    "Great Britain": "GB",
    "Hungary": "HU",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Croatia": "HR",
    "Slovenia": "SI",
    "Slovakia": "SK",
    "Serbia": "RS",
    "Luxembourg": "LU",
    "Ireland": "IE",
    "Unknown": "UNK",
}


def fix_country_code(country_name, country_code):
    """
    Corrige le code pays quand il est manquant ou égal à UNK.
    Exemple : Austria + UNK devient Austria + AT.
    """
    country_name = clean_string(country_name)
    country_code = clean_string(country_code)

    if country_code and country_code != "UNK":
        return country_code.upper()

    if country_name in COUNTRY_CODE_BY_NAME:
        return COUNTRY_CODE_BY_NAME[country_name]

    return "UNK"


# ============================================================
# Chargement des sources brutes
# ============================================================

def load_raw_sources():
    print("Chargement des sources brutes...")

    raw = {}

    # Source 1 : Back-on-Track
    raw["bot_agencies"] = read_json_auto(BACK_ON_TRACK_DIR / "agencies.json")
    raw["bot_stops"] = read_json_auto(BACK_ON_TRACK_DIR / "stops.json")
    raw["bot_routes"] = read_json_auto(BACK_ON_TRACK_DIR / "routes.json")
    raw["bot_trips"] = read_json_auto(BACK_ON_TRACK_DIR / "trips.json")
    raw["bot_trip_stop"] = read_json_auto(BACK_ON_TRACK_DIR / "trip_stop.json")
    raw["bot_calendar_dates"] = read_json_auto(BACK_ON_TRACK_DIR / "calendar_dates.json")
    raw["bot_metadata"] = read_json_auto(BACK_ON_TRACK_DIR / "metadata.json")

    # Source 2 : SNCF GTFS
    raw["sncf_agency"] = read_csv_auto(SNCF_GTFS_DIR / "agency.txt")
    raw["sncf_stops"] = read_csv_auto(SNCF_GTFS_DIR / "stops.txt")
    raw["sncf_routes"] = read_csv_auto(SNCF_GTFS_DIR / "routes.txt")
    raw["sncf_trips"] = read_csv_auto(SNCF_GTFS_DIR / "trips.txt")
    raw["sncf_stop_times"] = read_csv_auto(SNCF_GTFS_DIR / "stop_times.txt")
    raw["sncf_calendar_dates"] = read_csv_auto(SNCF_GTFS_DIR / "calendar_dates.txt")

    # Source 3 : Gares de voyageurs
    raw["gares"] = read_csv_auto(GARES_DIR / "gares-de-voyageurs.csv")

    # Source 4 : Wikipedia scraping
    raw["wiki"] = read_csv_auto(WIKI_DIR / "busiest_railway_stations_europe.csv")

    for name, df in raw.items():
        print(f"- {name}: {len(df)} lignes, {len(df.columns)} colonnes")

    return raw


# ============================================================
# DATA_SOURCE
# ============================================================

def transform_data_source():
    data_sources = [
        {
            "data_source_id": 1,
            "source_name": "Back-on-Track Night Train Data",
            "source_url": "https://github.com/Back-on-Track-eu/night-train-data",
            "source_format": "JSON",
            "extraction_date": date.today().isoformat(),
            "licence": None,
            "raw_file_name": "agencies.json; stops.json; routes.json; trips.json; trip_stop.json",
            "import_status": "success"
        },
        {
            "data_source_id": 2,
            "source_name": "SNCF GTFS",
            "source_url": "https://eu.ftp.opendatasoft.com/sncf/plandata/Export_OpenData_SNCF_GTFS_NewTripId.zip",
            "source_format": "GTFS ZIP",
            "extraction_date": date.today().isoformat(),
            "licence": None,
            "raw_file_name": "agency.txt; stops.txt; routes.txt; trips.txt; stop_times.txt; calendar_dates.txt",
            "import_status": "success"
        },
        {
            "data_source_id": 3,
            "source_name": "Gares de voyageurs SNCF",
            "source_url": "https://ressources.data.sncf.com",
            "source_format": "CSV",
            "extraction_date": date.today().isoformat(),
            "licence": None,
            "raw_file_name": "gares-de-voyageurs.csv",
            "import_status": "success"
        },
        {
            "data_source_id": 4,
            "source_name": "Wikipedia - Busiest railway stations in Europe",
            "source_url": "https://en.wikipedia.org/wiki/List_of_busiest_railway_stations_in_Europe",
            "source_format": "HTML scraping",
            "extraction_date": date.today().isoformat(),
            "licence": None,
            "raw_file_name": "busiest_railway_stations_europe.csv",
            "import_status": "success"
        }
    ]

    return pd.DataFrame(data_sources)


# ============================================================
# TRAIN_TYPE
# ============================================================

def transform_train_type():
    return pd.DataFrame([
        {
            "train_type_id": 1,
            "type_name": "night"
        },
        {
            "train_type_id": 2,
            "type_name": "day"
        }
    ])


# ============================================================
# COUNTRY, CITY, STATION
# ============================================================

def extract_stations_from_sncf_gtfs(sncf_stops: pd.DataFrame):
    """
    Source GTFS SNCF.
    On considère les gares comme françaises.
    Si la ville n'est pas fournie, on utilise le nom de la gare comme ville provisoire.
    """
    if sncf_stops.empty:
        return pd.DataFrame()

    stop_id = get_series(sncf_stops, ["stop_id"], None).apply(clean_string)
    stop_name = get_series(sncf_stops, ["stop_name"], None).apply(clean_string)
    lat = pd.to_numeric(get_series(sncf_stops, ["stop_lat"], None), errors="coerce")
    lon = pd.to_numeric(get_series(sncf_stops, ["stop_lon"], None), errors="coerce")
    timezone = get_series(sncf_stops, ["stop_timezone", "timezone"], "Europe/Paris").apply(clean_string)

    df = pd.DataFrame({
        "station_name": stop_name,
        "station_code": stop_id,
        "latitude": lat,
        "longitude": lon,
        "timezone": timezone,
        "city_name": stop_name,
        "country_name": "France",
        "country_code": "FR",
        "source_name": "SNCF GTFS"
    })

    df = df.dropna(subset=["station_name"])
    df = df.drop_duplicates(subset=["station_code", "station_name"])

    return df


def extract_stations_from_gares(gares: pd.DataFrame):
    """
    Source gares-de-voyageurs.
    Les noms de colonnes peuvent varier selon l'export,
    donc on cherche plusieurs noms possibles.
    """
    if gares.empty:
        return pd.DataFrame()

    name_col = get_column(gares, [
        "nom",
        "nom_gare",
        "gare",
        "libelle",
        "libelle_gare",
        "intitule_gare",
        "gare_alias_libelle_noncontraint"
    ])

    code_col = get_column(gares, [
        "code_uic",
        "uic",
        "code_gare",
        "trigramme",
        "code"
    ])

    city_col = get_column(gares, [
        "commune",
        "libelle_commune",
        "city",
        "ville"
    ])

    lat_col = get_column(gares, [
        "latitude",
        "lat"
    ])

    lon_col = get_column(gares, [
        "longitude",
        "lon",
        "lng"
    ])

    # Certains exports ont une colonne géographique du type "geo_point_2d"
    geo_col = get_column(gares, [
        "geo_point_2d",
        "coordonnees_geographiques",
        "wgs_84",
        "geopoint"
    ])

    station_name = get_series(gares, [name_col] if name_col else [], None).apply(clean_string)
    station_code = get_series(gares, [code_col] if code_col else [], None).apply(clean_string)
    city_name = get_series(gares, [city_col] if city_col else [], None).apply(clean_string)

    latitude = pd.to_numeric(get_series(gares, [lat_col] if lat_col else [], None), errors="coerce")
    longitude = pd.to_numeric(get_series(gares, [lon_col] if lon_col else [], None), errors="coerce")

    if geo_col is not None and latitude.isna().all():
        geo_values = gares[geo_col].apply(clean_string)

        extracted_lat = []
        extracted_lon = []

        for value in geo_values:
            if value and "," in value:
                parts = value.split(",")
                try:
                    extracted_lat.append(float(parts[0].strip()))
                    extracted_lon.append(float(parts[1].strip()))
                except Exception:
                    extracted_lat.append(None)
                    extracted_lon.append(None)
            else:
                extracted_lat.append(None)
                extracted_lon.append(None)

        latitude = pd.Series(extracted_lat)
        longitude = pd.Series(extracted_lon)

    df = pd.DataFrame({
        "station_name": station_name,
        "station_code": station_code,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Europe/Paris",
        "city_name": city_name,
        "country_name": "France",
        "country_code": "FR",
        "source_name": "Gares de voyageurs SNCF"
    })

    df["city_name"] = df["city_name"].fillna(df["station_name"])
    df = df.dropna(subset=["station_name"])
    df = df.drop_duplicates(subset=["station_code", "station_name"])

    return df


def extract_stations_from_wikipedia(wiki: pd.DataFrame):
    """
    Source scraping Wikipedia.
    Sert surtout à enrichir les pays, villes et gares européennes.
    """
    if wiki.empty:
        return pd.DataFrame()

    country_col = get_column(wiki, ["country"])
    city_col = get_column(wiki, ["city"])
    station_col = get_column(wiki, ["railway_station", "station", "name"])

    if country_col is None or city_col is None or station_col is None:
        print("[ATTENTION] Colonnes Wikipedia non reconnues. Source ignorée pour station.")
        return pd.DataFrame()

    df = pd.DataFrame({
        "station_name": wiki[station_col].apply(clean_string),
        "station_code": None,
        "latitude": None,
        "longitude": None,
        "timezone": None,
        "city_name": wiki[city_col].apply(clean_string),
        "country_name": wiki[country_col].apply(clean_string),
        "country_code": None,
        "source_name": "Wikipedia scraping"
    })

    df = df.dropna(subset=["station_name", "city_name", "country_name"])
    df = df.drop_duplicates(subset=["station_name", "city_name", "country_name"])

    return df


def extract_stations_from_back_on_track(bot_stops: pd.DataFrame):
    """
    Source Back-on-Track.
    On essaie de récupérer station, ville, pays, coordonnées.
    """
    if bot_stops.empty:
        return pd.DataFrame()

    stop_id_col = get_column(bot_stops, ["stop_id", "id", "station_id", "code", "_source_key"])
    stop_name_col = get_column(bot_stops, ["stop_name", "name", "station_name", "city"])
    city_col = get_column(bot_stops, ["city", "city_name", "town", "municipality"])
    country_col = get_column(bot_stops, ["country", "country_name", "country_code"])
    lat_col = get_column(bot_stops, ["stop_lat", "latitude", "lat"])
    lon_col = get_column(bot_stops, ["stop_lon", "longitude", "lon", "lng"])
    timezone_col = get_column(bot_stops, ["timezone", "stop_timezone"])

    station_name = get_series(bot_stops, [stop_name_col] if stop_name_col else [], None).apply(clean_string)
    station_code = get_series(bot_stops, [stop_id_col] if stop_id_col else [], None).apply(clean_string)
    city_name = get_series(bot_stops, [city_col] if city_col else [], None).apply(clean_string)
    country_raw = get_series(bot_stops, [country_col] if country_col else [], None).apply(clean_string)

    latitude = pd.to_numeric(get_series(bot_stops, [lat_col] if lat_col else [], None), errors="coerce")
    longitude = pd.to_numeric(get_series(bot_stops, [lon_col] if lon_col else [], None), errors="coerce")
    timezone = get_series(bot_stops, [timezone_col] if timezone_col else [], None).apply(clean_string)

    country_name = []
    country_code = []

    for value in country_raw:
        if value is None:
            country_name.append("Unknown")
            country_code.append("UNK")
        elif len(value) <= 3:
            country_name.append(value.upper())
            country_code.append(value.upper())
        else:
            country_name.append(value)
            country_code.append(None)

    df = pd.DataFrame({
        "station_name": station_name,
        "station_code": station_code,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "city_name": city_name,
        "country_name": country_name,
        "country_code": country_code,
        "source_name": "Back-on-Track"
    })

    df["city_name"] = df["city_name"].fillna(df["station_name"])
    df = df.dropna(subset=["station_name"])
    df = df.drop_duplicates(subset=["station_code", "station_name"])

    return df


def transform_geo_and_stations(raw):
    print("\nTransformation COUNTRY, CITY, STATION...")

    station_sources = [
        extract_stations_from_sncf_gtfs(raw["sncf_stops"]),
        extract_stations_from_gares(raw["gares"]),
        extract_stations_from_wikipedia(raw["wiki"]),
        extract_stations_from_back_on_track(raw["bot_stops"])
    ]

    all_stations_raw = pd.concat(station_sources, ignore_index=True)
    all_stations_raw = all_stations_raw.dropna(subset=["station_name"])

    all_stations_raw["station_name"] = all_stations_raw["station_name"].apply(clean_string)
    all_stations_raw["city_name"] = all_stations_raw["city_name"].apply(clean_string)
    all_stations_raw["country_name"] = all_stations_raw["country_name"].apply(clean_string)
    all_stations_raw["country_code"] = all_stations_raw["country_code"].apply(clean_string)

    all_stations_raw["city_name"] = all_stations_raw["city_name"].fillna(all_stations_raw["station_name"])
    all_stations_raw["country_name"] = all_stations_raw["country_name"].fillna("Unknown")
    all_stations_raw["country_code"] = all_stations_raw["country_code"].fillna("UNK")

    # Correction des codes pays manquants à partir du nom du pays
    all_stations_raw["country_code"] = all_stations_raw.apply(
        lambda row: fix_country_code(row["country_name"], row["country_code"]),
        axis=1
    )

    # COUNTRY
    countries = (
        all_stations_raw[["country_name", "country_code"]]
        .drop_duplicates()
        .sort_values(["country_name", "country_code"])
        .reset_index(drop=True)
    )

    countries["country_id"] = range(1, len(countries) + 1)
    countries = countries[["country_id", "country_name", "country_code"]]

    country_key_to_id = {
        build_key(row.country_name, row.country_code): row.country_id
        for row in countries.itertuples(index=False)
    }

    all_stations_raw["country_key"] = all_stations_raw.apply(
        lambda row: build_key(row["country_name"], row["country_code"]),
        axis=1
    )

    all_stations_raw["country_id"] = all_stations_raw["country_key"].map(country_key_to_id)

    # CITY
    cities = (
        all_stations_raw[["city_name", "country_id"]]
        .drop_duplicates()
        .sort_values(["country_id", "city_name"])
        .reset_index(drop=True)
    )

    cities["city_id"] = range(1, len(cities) + 1)
    cities = cities[["city_id", "city_name", "country_id"]]

    city_key_to_id = {
        build_key(row.city_name, row.country_id): row.city_id
        for row in cities.itertuples(index=False)
    }

    all_stations_raw["city_key"] = all_stations_raw.apply(
        lambda row: build_key(row["city_name"], row["country_id"]),
        axis=1
    )

    all_stations_raw["city_id"] = all_stations_raw["city_key"].map(city_key_to_id)

    # STATION
    all_stations_raw["station_key"] = all_stations_raw.apply(
        lambda row: build_key(row["station_code"], row["station_name"], row["city_id"]),
        axis=1
    )

    stations = (
        all_stations_raw
        .drop_duplicates(subset=["station_key"])
        .reset_index(drop=True)
    )

    stations["station_id"] = range(1, len(stations) + 1)

    stations = stations[
        [
            "station_id",
            "station_name",
            "station_code",
            "latitude",
            "longitude",
            "timezone",
            "city_id"
        ]
    ]

    # Mapping utile pour les trajets
    station_code_to_id = {}

    for row in stations.itertuples(index=False):
        if row.station_code is not None and not pd.isna(row.station_code):
            station_code_to_id[str(row.station_code)] = row.station_id

    return countries, cities, stations, station_code_to_id


# ============================================================
# OPERATOR
# ============================================================

def transform_operators(raw, countries):
    print("\nTransformation OPERATOR...")

    operators_data = []

    # Back-on-Track agencies
    bot_agencies = raw["bot_agencies"]

    if not bot_agencies.empty:
        agency_id_col = get_column(bot_agencies, ["agency_id", "id", "operator_id", "code", "_source_key"])
        agency_name_col = get_column(bot_agencies, ["agency_name", "name", "operator_name", "_source_key"])
        
        for _, row in bot_agencies.iterrows():
            operator_code = clean_string(row[agency_id_col]) if agency_id_col else None
            operator_name = clean_string(row[agency_name_col]) if agency_name_col else operator_code

            if operator_name:
                operators_data.append({
                    "operator_name": operator_name,
                    "operator_code": operator_code,
                    "country_code": "UNK"
                })

    # SNCF agency
    sncf_agency = raw["sncf_agency"]

    if not sncf_agency.empty:
        agency_id_col = get_column(sncf_agency, ["agency_id"])
        agency_name_col = get_column(sncf_agency, ["agency_name"])

        for _, row in sncf_agency.iterrows():
            operator_code = clean_string(row[agency_id_col]) if agency_id_col else "SNCF"
            operator_name = clean_string(row[agency_name_col]) if agency_name_col else "SNCF"

            operators_data.append({
                "operator_name": operator_name,
                "operator_code": operator_code,
                "country_code": "FR"
            })

    # Valeur par défaut
    operators_data.append({
        "operator_name": "Unknown operator",
        "operator_code": "UNKNOWN",
        "country_code": "UNK"
    })

    operators_raw = pd.DataFrame(operators_data)
    operators_raw = operators_raw.drop_duplicates(subset=["operator_name", "operator_code"])

    country_code_to_id = dict(zip(countries["country_code"], countries["country_id"]))

    if "UNK" not in country_code_to_id:
        unknown_country_id = int(countries["country_id"].iloc[0])
    else:
        unknown_country_id = country_code_to_id["UNK"]

    operators_raw["country_id"] = operators_raw["country_code"].map(country_code_to_id)
    operators_raw["country_id"] = operators_raw["country_id"].fillna(unknown_country_id).astype(int)

    operators_raw["operator_id"] = range(1, len(operators_raw) + 1)

    operators = operators_raw[
        [
            "operator_id",
            "operator_name",
            "operator_code",
            "country_id"
        ]
    ]

    operator_code_to_id = {}

    for row in operators.itertuples(index=False):
        if row.operator_code:
            operator_code_to_id[str(row.operator_code)] = row.operator_id

    unknown_operator_id = int(
        operators.loc[operators["operator_code"] == "UNKNOWN", "operator_id"].iloc[0]
    )

    return operators, operator_code_to_id, unknown_operator_id


# ============================================================
# ROUTE, TRIP, TRIP_STOP depuis SNCF GTFS
# ============================================================

def transform_sncf_trips(raw, station_code_to_id, operator_code_to_id, unknown_operator_id):
    print("\nTransformation des trajets SNCF GTFS...")

    stops = raw["sncf_stops"]
    routes_src = raw["sncf_routes"]
    trips_src = raw["sncf_trips"]
    stop_times = raw["sncf_stop_times"]
    calendar_dates = raw["sncf_calendar_dates"]

    if stops.empty or trips_src.empty or stop_times.empty:
        print("[ATTENTION] Données GTFS SNCF insuffisantes pour créer les trajets.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    stop_id_col = get_column(stops, ["stop_id"])
    stop_to_station_id = {}

    for _, row in stops.iterrows():
        stop_code = clean_string(row[stop_id_col])
        if stop_code in station_code_to_id:
            stop_to_station_id[stop_code] = station_code_to_id[stop_code]

    # Préparation stop_times
    trip_id_col = get_column(stop_times, ["trip_id"])
    stop_id_col_st = get_column(stop_times, ["stop_id"])
    stop_sequence_col = get_column(stop_times, ["stop_sequence"])
    arrival_time_col = get_column(stop_times, ["arrival_time"])
    departure_time_col = get_column(stop_times, ["departure_time"])

    st = pd.DataFrame({
        "source_trip_code": stop_times[trip_id_col].apply(clean_string),
        "source_stop_code": stop_times[stop_id_col_st].apply(clean_string),
        "stop_order": pd.to_numeric(stop_times[stop_sequence_col], errors="coerce"),
        "arrival_time_raw": stop_times[arrival_time_col].apply(clean_string),
        "departure_time_raw": stop_times[departure_time_col].apply(clean_string)
    })

    st["station_id"] = st["source_stop_code"].map(stop_to_station_id)
    st = st.dropna(subset=["source_trip_code", "station_id", "stop_order"])
    st["station_id"] = st["station_id"].astype(int)
    st["stop_order"] = st["stop_order"].astype(int)

    st = st.sort_values(["source_trip_code", "stop_order"])

    first_stops = st.groupby("source_trip_code", as_index=False).first()
    last_stops = st.groupby("source_trip_code", as_index=False).last()

    bounds = first_stops[
        [
            "source_trip_code",
            "station_id",
            "departure_time_raw"
        ]
    ].rename(columns={
        "station_id": "departure_station_id",
        "departure_time_raw": "raw_departure_time"
    })

    bounds = bounds.merge(
        last_stops[
            [
                "source_trip_code",
                "station_id",
                "arrival_time_raw"
            ]
        ],
        on="source_trip_code",
        how="inner"
    ).rename(columns={
        "station_id": "arrival_station_id",
        "arrival_time_raw": "raw_arrival_time"
    })

    # Préparation trips
    trips_trip_id_col = get_column(trips_src, ["trip_id"])
    trips_route_id_col = get_column(trips_src, ["route_id"])
    trips_service_id_col = get_column(trips_src, ["service_id"])

    trips_work = pd.DataFrame({
        "source_trip_code": trips_src[trips_trip_id_col].apply(clean_string),
        "source_route_code": trips_src[trips_route_id_col].apply(clean_string),
        "service_id": trips_src[trips_service_id_col].apply(clean_string)
    })

    # Date de service depuis calendar_dates
    if not calendar_dates.empty:
        service_col = get_column(calendar_dates, ["service_id"])
        date_col = get_column(calendar_dates, ["date"])

        service_dates = calendar_dates[[service_col, date_col]].copy()
        service_dates.columns = ["service_id", "service_date"]

        service_dates["service_id"] = service_dates["service_id"].apply(clean_string)
        service_dates["service_date"] = service_dates["service_date"].apply(clean_string)

        # On prend la première date trouvée par service_id pour simplifier la V1
        service_dates = service_dates.drop_duplicates(subset=["service_id"])

        trips_work = trips_work.merge(service_dates, on="service_id", how="left")
    else:
        trips_work["service_date"] = None

    trips_work = trips_work.merge(bounds, on="source_trip_code", how="inner")

    # Opérateur depuis routes
    if not routes_src.empty:
        route_id_col = get_column(routes_src, ["route_id"])
        agency_id_col = get_column(routes_src, ["agency_id"])

        routes_mapping = routes_src[[route_id_col, agency_id_col]].copy()
        routes_mapping.columns = ["source_route_code", "operator_code"]
        routes_mapping["source_route_code"] = routes_mapping["source_route_code"].apply(clean_string)
        routes_mapping["operator_code"] = routes_mapping["operator_code"].apply(clean_string)

        trips_work = trips_work.merge(routes_mapping, on="source_route_code", how="left")
    else:
        trips_work["operator_code"] = None

    trips_work["operator_id"] = trips_work["operator_code"].map(operator_code_to_id)
    trips_work["operator_id"] = trips_work["operator_id"].fillna(unknown_operator_id).astype(int)

    # Route key
    trips_work["route_key"] = trips_work.apply(
        lambda row: build_key(row["departure_station_id"], row["arrival_station_id"], row["operator_id"]),
        axis=1
    )

    routes = (
        trips_work[
            [
                "route_key",
                "departure_station_id",
                "arrival_station_id",
                "operator_id"
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    routes["route_id"] = range(1, len(routes) + 1)
    routes["distance_km"] = None

    route_key_to_id = dict(zip(routes["route_key"], routes["route_id"]))
    trips_work["route_id"] = trips_work["route_key"].map(route_key_to_id)

    # TRIP
    trips = trips_work.drop_duplicates(subset=["source_trip_code"]).reset_index(drop=True)
    trips["trip_id"] = range(1, len(trips) + 1)

    # SNCF GTFS = day par défaut pour cette V1
    trips["train_type_id"] = 2
    trips["data_source_id"] = 2
    trips["trip_code"] = trips["source_trip_code"]

    departure_parsed = trips["raw_departure_time"].apply(gtfs_time_to_sql_time_and_offset)
    arrival_parsed = trips["raw_arrival_time"].apply(gtfs_time_to_sql_time_and_offset)

    trips["departure_time"] = [item[0] for item in departure_parsed]
    trips["departure_day_offset"] = [item[1] for item in departure_parsed]

    trips["arrival_time"] = [item[0] for item in arrival_parsed]
    trips["arrival_day_offset"] = [item[1] for item in arrival_parsed]

    trips["_departure_minutes"] = trips["raw_departure_time"].apply(gtfs_time_to_minutes)
    trips["_arrival_minutes"] = trips["raw_arrival_time"].apply(gtfs_time_to_minutes)

    trips["duration_minutes"] = trips["_arrival_minutes"] - trips["_departure_minutes"]
    trips.loc[trips["duration_minutes"] < 0, "duration_minutes"] = None

    trips["co2_estimated_kg"] = None

    trips_final = trips[
        [
            "trip_id",
            "route_id",
            "train_type_id",
            "data_source_id",
            "trip_code",
            "service_date",
            "departure_time",
            "arrival_time",
            "departure_day_offset",
            "arrival_day_offset",
            "duration_minutes",
            "co2_estimated_kg"
        ]
    ]

    source_trip_to_trip_id = dict(zip(trips_final["trip_code"], trips_final["trip_id"]))

    # TRIP_STOP
    trip_stops = st.copy()
    trip_stops["trip_id"] = trip_stops["source_trip_code"].map(source_trip_to_trip_id)
    trip_stops = trip_stops.dropna(subset=["trip_id"])
    trip_stops["trip_id"] = trip_stops["trip_id"].astype(int)

    arrival_parsed_stop = trip_stops["arrival_time_raw"].apply(gtfs_time_to_sql_time_and_offset)
    departure_parsed_stop = trip_stops["departure_time_raw"].apply(gtfs_time_to_sql_time_and_offset)

    trip_stops["arrival_time"] = [item[0] for item in arrival_parsed_stop]
    trip_stops["arrival_day_offset"] = [item[1] for item in arrival_parsed_stop]

    trip_stops["departure_time"] = [item[0] for item in departure_parsed_stop]
    trip_stops["departure_day_offset"] = [item[1] for item in departure_parsed_stop]

    trip_stops = trip_stops.sort_values(["trip_id", "stop_order"]).reset_index(drop=True)
    trip_stops["trip_stop_id"] = range(1, len(trip_stops) + 1)

    trip_stops_final = trip_stops[
        [
            "trip_stop_id",
            "trip_id",
            "station_id",
            "stop_order",
            "arrival_time",
            "departure_time",
            "arrival_day_offset",
            "departure_day_offset"
        ]
    ]

    routes_final = routes[
        [
            "route_id",
            "departure_station_id",
            "arrival_station_id",
            "operator_id",
            "distance_km"
        ]
    ]

    return routes_final, trips_final, trip_stops_final


def transform_back_on_track_trips(
    raw,
    station_code_to_id,
    operator_code_to_id,
    unknown_operator_id,
    route_start_id,
    trip_start_id,
    trip_stop_start_id
):
    print("\nTransformation des trajets Back-on-Track night...")

    routes_src = raw["bot_routes"]
    trips_src = raw["bot_trips"]
    trip_stops_src = raw["bot_trip_stop"]
    calendar_dates = raw.get("bot_calendar_dates", pd.DataFrame())

    if trips_src.empty or trip_stops_src.empty:
        print("[ATTENTION] Données Back-on-Track insuffisantes pour créer les trajets night.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # --------------------------------------------------------
    # Préparation des arrêts Back-on-Track
    # --------------------------------------------------------

    trip_id_col = get_column(trip_stops_src, [
        "trip_id",
        "id_trip",
        "trip",
        "trip_code"
    ])

    stop_id_col = get_column(trip_stops_src, [
        "stop_id",
        "station_id",
        "stop",
        "station",
        "stop_code"
    ])

    stop_sequence_col = get_column(trip_stops_src, [
        "stop_sequence",
        "stop_order",
        "sequence",
        "order"
    ])

    arrival_time_col = get_column(trip_stops_src, [
        "arrival_time",
        "arrival",
        "time_arrival"
    ])

    departure_time_col = get_column(trip_stops_src, [
        "departure_time",
        "departure",
        "time_departure"
    ])

    if trip_id_col is None or stop_id_col is None:
        print("[ATTENTION] Colonnes trip_id ou stop_id non reconnues dans bot_trip_stop.")
        print("Colonnes disponibles :", list(trip_stops_src.columns))
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if stop_sequence_col is None:
        trip_stops_src["_generated_stop_order"] = (
            trip_stops_src.groupby(trip_id_col).cumcount() + 1
        )
        stop_sequence_col = "_generated_stop_order"

    if arrival_time_col is None:
        arrival_time_col = departure_time_col

    if departure_time_col is None:
        departure_time_col = arrival_time_col

    st = pd.DataFrame({
        "source_trip_code": trip_stops_src[trip_id_col].apply(clean_string),
        "source_stop_code": trip_stops_src[stop_id_col].apply(clean_string),
        "stop_order": pd.to_numeric(trip_stops_src[stop_sequence_col], errors="coerce"),
        "arrival_time_raw": trip_stops_src[arrival_time_col].apply(clean_string) if arrival_time_col else None,
        "departure_time_raw": trip_stops_src[departure_time_col].apply(clean_string) if departure_time_col else None,
    })

    st["station_id"] = st["source_stop_code"].map(station_code_to_id)

    st = st.dropna(subset=[
        "source_trip_code",
        "source_stop_code",
        "station_id",
        "stop_order"
    ])

    if st.empty:
        print("[ATTENTION] Aucun arrêt Back-on-Track n'a pu être associé aux stations.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    st["station_id"] = st["station_id"].astype(int)
    st["stop_order"] = st["stop_order"].astype(int)
    st = st.sort_values(["source_trip_code", "stop_order"])

    # --------------------------------------------------------
    # Départ et arrivée de chaque trip
    # --------------------------------------------------------

        # --------------------------------------------------------
    # Départ et arrivée de chaque trip
    # --------------------------------------------------------

    first_stops = st.groupby("source_trip_code", as_index=False).first()
    last_stops = st.groupby("source_trip_code", as_index=False).last()

    bounds = first_stops[
        [
            "source_trip_code",
            "station_id",
            "departure_time_raw",
            "arrival_time_raw"
        ]
    ].rename(columns={
        "station_id": "departure_station_id",
        "departure_time_raw": "raw_departure_time",
        "arrival_time_raw": "first_arrival_time_raw"
    })

    last_bounds = last_stops[
        [
            "source_trip_code",
            "station_id",
            "arrival_time_raw",
            "departure_time_raw"
        ]
    ].rename(columns={
        "station_id": "arrival_station_id",
        "arrival_time_raw": "raw_arrival_time",
        "departure_time_raw": "last_departure_time_raw"
    })

    bounds = bounds.merge(
        last_bounds,
        on="source_trip_code",
        how="inner"
    )

    # Fallback : si l'heure de départ est absente, on prend l'heure d'arrivée du premier arrêt
    bounds["raw_departure_time"] = bounds["raw_departure_time"].fillna(
        bounds["first_arrival_time_raw"]
    )

    # Fallback : si l'heure d'arrivée est absente, on prend l'heure de départ du dernier arrêt
    bounds["raw_arrival_time"] = bounds["raw_arrival_time"].fillna(
        bounds["last_departure_time_raw"]
    )

    bounds = bounds[
        [
            "source_trip_code",
            "departure_station_id",
            "arrival_station_id",
            "raw_departure_time",
            "raw_arrival_time"
        ]
    ]

    # --------------------------------------------------------
    # Préparation trips Back-on-Track
    # --------------------------------------------------------

    trips_trip_id_col = get_column(trips_src, [
        "trip_id",
        "id",
        "trip_code",
        "_source_key"
    ])

    trips_route_id_col = get_column(trips_src, [
        "route_id",
        "route",
        "route_code"
    ])

    trips_service_id_col = get_column(trips_src, [
        "service_id",
        "service"
    ])

    if trips_trip_id_col is None:
        print("[ATTENTION] Colonne trip_id non reconnue dans bot_trips.")
        print("Colonnes disponibles :", list(trips_src.columns))
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    trips_work = pd.DataFrame({
        "source_trip_code": trips_src[trips_trip_id_col].apply(clean_string),
        "source_route_code": trips_src[trips_route_id_col].apply(clean_string) if trips_route_id_col else None,
        "service_id": trips_src[trips_service_id_col].apply(clean_string) if trips_service_id_col else None,
    })

    trips_work = trips_work.dropna(subset=["source_trip_code"])
    trips_work = trips_work.merge(bounds, on="source_trip_code", how="inner")

    if trips_work.empty:
        print("[ATTENTION] Aucun trip Back-on-Track n'a pu être relié aux arrêts.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # --------------------------------------------------------
    # Date de service depuis calendar_dates si disponible
    # --------------------------------------------------------

    if calendar_dates is not None and not calendar_dates.empty and "service_id" in trips_work.columns:
        service_col = get_column(calendar_dates, ["service_id", "service"])
        date_col = get_column(calendar_dates, ["date", "service_date"])

        if service_col is not None and date_col is not None:
            service_dates = calendar_dates[[service_col, date_col]].copy()
            service_dates.columns = ["service_id", "service_date"]

            service_dates["service_id"] = service_dates["service_id"].apply(clean_string)
            service_dates["service_date"] = service_dates["service_date"].apply(clean_string)

            service_dates = service_dates.drop_duplicates(subset=["service_id"])

            trips_work = trips_work.merge(service_dates, on="service_id", how="left")
        else:
            trips_work["service_date"] = None
    else:
        trips_work["service_date"] = None

    # --------------------------------------------------------
    # Opérateur depuis bot_routes
    # --------------------------------------------------------

    trips_work["operator_code"] = None

    if not routes_src.empty and trips_route_id_col is not None:
        route_id_col = get_column(routes_src, [
            "route_id",
            "id",
            "route_code",
            "_source_key"
        ])

        agency_id_col = get_column(routes_src, [
            "agency_id",
            "operator_id",
            "agency",
            "operator"
        ])

        if route_id_col is not None and agency_id_col is not None:
            routes_mapping = routes_src[[route_id_col, agency_id_col]].copy()
            routes_mapping.columns = ["source_route_code", "operator_code"]

            routes_mapping["source_route_code"] = routes_mapping["source_route_code"].apply(clean_string)
            routes_mapping["operator_code"] = routes_mapping["operator_code"].apply(clean_string)

            trips_work = trips_work.merge(routes_mapping, on="source_route_code", how="left")

            if "operator_code_y" in trips_work.columns:
                trips_work["operator_code"] = trips_work["operator_code_y"]

    trips_work["operator_id"] = trips_work["operator_code"].map(operator_code_to_id)
    trips_work["operator_id"] = trips_work["operator_id"].fillna(unknown_operator_id).astype(int)

    # --------------------------------------------------------
    # ROUTE
    # --------------------------------------------------------

    trips_work["route_key"] = trips_work.apply(
        lambda row: build_key(
            row["departure_station_id"],
            row["arrival_station_id"],
            row["operator_id"]
        ),
        axis=1
    )

    routes = (
        trips_work[
            [
                "route_key",
                "departure_station_id",
                "arrival_station_id",
                "operator_id"
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    routes["route_id"] = range(route_start_id, route_start_id + len(routes))
    routes["distance_km"] = None

    route_key_to_id = dict(zip(routes["route_key"], routes["route_id"]))
    trips_work["route_id"] = trips_work["route_key"].map(route_key_to_id)

    routes_final = routes[
        [
            "route_id",
            "departure_station_id",
            "arrival_station_id",
            "operator_id",
            "distance_km"
        ]
    ]

    # --------------------------------------------------------
    # TRIP night
    # --------------------------------------------------------

    trips = trips_work.drop_duplicates(subset=["source_trip_code"]).reset_index(drop=True)

    trips["trip_id"] = range(trip_start_id, trip_start_id + len(trips))
    trips["train_type_id"] = 1
    trips["data_source_id"] = 1
    trips["trip_code"] = trips["source_trip_code"]

    departure_parsed = trips["raw_departure_time"].apply(gtfs_time_to_sql_time_and_offset)
    arrival_parsed = trips["raw_arrival_time"].apply(gtfs_time_to_sql_time_and_offset)

    trips["departure_time"] = [item[0] for item in departure_parsed]
    trips["departure_day_offset"] = [item[1] for item in departure_parsed]

    trips["arrival_time"] = [item[0] for item in arrival_parsed]
    trips["arrival_day_offset"] = [item[1] for item in arrival_parsed]

    trips["_departure_minutes"] = trips["raw_departure_time"].apply(gtfs_time_to_minutes)
    trips["_arrival_minutes"] = trips["raw_arrival_time"].apply(gtfs_time_to_minutes)

    trips["duration_minutes"] = trips["_arrival_minutes"] - trips["_departure_minutes"]

    # Si l'arrivée est le lendemain mais non codée en +24h, on ajoute 24h
    trips.loc[trips["duration_minutes"] < 0, "duration_minutes"] = (
        trips.loc[trips["duration_minutes"] < 0, "duration_minutes"] + 1440
    )

    trips["co2_estimated_kg"] = None

    trips_final = trips[
        [
            "trip_id",
            "route_id",
            "train_type_id",
            "data_source_id",
            "trip_code",
            "service_date",
            "departure_time",
            "arrival_time",
            "departure_day_offset",
            "arrival_day_offset",
            "duration_minutes",
            "co2_estimated_kg"
        ]
    ]

    source_trip_to_trip_id = dict(zip(trips_final["trip_code"], trips_final["trip_id"]))

    # --------------------------------------------------------
    # TRIP_STOP night
    # --------------------------------------------------------

    trip_stops = st.copy()

    trip_stops["trip_id"] = trip_stops["source_trip_code"].map(source_trip_to_trip_id)
    trip_stops = trip_stops.dropna(subset=["trip_id"])
    trip_stops["trip_id"] = trip_stops["trip_id"].astype(int)

    arrival_parsed_stop = trip_stops["arrival_time_raw"].apply(gtfs_time_to_sql_time_and_offset)
    departure_parsed_stop = trip_stops["departure_time_raw"].apply(gtfs_time_to_sql_time_and_offset)

    trip_stops["arrival_time"] = [item[0] for item in arrival_parsed_stop]
    trip_stops["arrival_day_offset"] = [item[1] for item in arrival_parsed_stop]

    trip_stops["departure_time"] = [item[0] for item in departure_parsed_stop]
    trip_stops["departure_day_offset"] = [item[1] for item in departure_parsed_stop]

    trip_stops = trip_stops.sort_values(["trip_id", "stop_order"]).reset_index(drop=True)
    trip_stops["trip_stop_id"] = range(
        trip_stop_start_id,
        trip_stop_start_id + len(trip_stops)
    )

    trip_stops_final = trip_stops[
        [
            "trip_stop_id",
            "trip_id",
            "station_id",
            "stop_order",
            "arrival_time",
            "departure_time",
            "arrival_day_offset",
            "departure_day_offset"
        ]
    ]

    print(f"[OK] Back-on-Track routes night : {len(routes_final)}")
    print(f"[OK] Back-on-Track trips night : {len(trips_final)}")
    print(f"[OK] Back-on-Track trip_stops night : {len(trip_stops_final)}")

    return routes_final, trips_final, trip_stops_final


# ============================================================
# QUALITY_CHECK
# ============================================================

def transform_quality_check(trips: pd.DataFrame):
    print("\nTransformation QUALITY_CHECK...")

    if trips.empty:
        return pd.DataFrame(columns=[
            "quality_check_id",
            "trip_id",
            "has_missing_values",
            "has_time_error",
            "is_duplicate",
            "quality_score",
            "rule_name",
            "error_message",
            "check_date"
        ])

    quality = trips.copy()

    quality["has_missing_values"] = quality[
        [
            "route_id",
            "train_type_id",
            "data_source_id",
            "departure_time",
            "arrival_time"
        ]
    ].isna().any(axis=1)

    quality["has_time_error"] = quality["duration_minutes"].isna() | (
        pd.to_numeric(quality["duration_minutes"], errors="coerce") <= 0
    )

    quality["is_duplicate"] = quality["trip_code"].duplicated(keep=False)

    quality["quality_score"] = 100
    quality.loc[quality["has_missing_values"], "quality_score"] -= 30
    quality.loc[quality["has_time_error"], "quality_score"] -= 40
    quality.loc[quality["is_duplicate"], "quality_score"] -= 20

    quality["quality_score"] = quality["quality_score"].clip(lower=0)

    def build_error_message(row):
        errors = []

        if row["has_missing_values"]:
            errors.append("Valeurs manquantes")

        if row["has_time_error"]:
            errors.append("Erreur horaire ou durée invalide")

        if row["is_duplicate"]:
            errors.append("Doublon potentiel")

        if not errors:
            return None

        return "; ".join(errors)

    quality["error_message"] = quality.apply(build_error_message, axis=1)
    quality["quality_check_id"] = range(1, len(quality) + 1)
    quality["rule_name"] = "basic_quality_rules"
    quality["check_date"] = date.today().isoformat()

    return quality[
        [
            "quality_check_id",
            "trip_id",
            "has_missing_values",
            "has_time_error",
            "is_duplicate",
            "quality_score",
            "rule_name",
            "error_message",
            "check_date"
        ]
    ]


# ============================================================
# Fonction principale
# ============================================================

def main():
    print("Début de la transformation globale...")

    ensure_output_dir()

    raw = load_raw_sources()

    data_source = transform_data_source()
    train_type = transform_train_type()

    country, city, station, station_code_to_id = transform_geo_and_stations(raw)

    operator, operator_code_to_id, unknown_operator_id = transform_operators(raw, country)

    # Trajets SNCF = day
    sncf_route, sncf_trip, sncf_trip_stop = transform_sncf_trips(
        raw=raw,
        station_code_to_id=station_code_to_id,
        operator_code_to_id=operator_code_to_id,
        unknown_operator_id=unknown_operator_id
    )

    # Trajets Back-on-Track = night
    next_route_id = len(sncf_route) + 1
    next_trip_id = len(sncf_trip) + 1
    next_trip_stop_id = len(sncf_trip_stop) + 1

    bot_route, bot_trip, bot_trip_stop = transform_back_on_track_trips(
        raw=raw,
        station_code_to_id=station_code_to_id,
        operator_code_to_id=operator_code_to_id,
        unknown_operator_id=unknown_operator_id,
        route_start_id=next_route_id,
        trip_start_id=next_trip_id,
        trip_stop_start_id=next_trip_stop_id
    )

    # Fusion day + night
    route = pd.concat([sncf_route, bot_route], ignore_index=True)
    trip = pd.concat([sncf_trip, bot_trip], ignore_index=True)
    trip_stop = pd.concat([sncf_trip_stop, bot_trip_stop], ignore_index=True)

    quality_check = transform_quality_check(trip)

        # Correction des colonnes entières nullable avant export CSV
    trip = convert_nullable_integer_columns(
        trip,
        [
            "departure_day_offset",
            "arrival_day_offset"
        ]
    )

    trip_stop = convert_nullable_integer_columns(
        trip_stop,
        [
            "stop_order",
            "arrival_day_offset",
            "departure_day_offset"
        ]
    )

    route = convert_nullable_integer_columns(
        route,
        [
            "departure_station_id",
            "arrival_station_id",
            "operator_id"
        ]
    )

    quality_check = convert_nullable_integer_columns(
        quality_check,
        [
            "quality_score"
        ]
    )

    # Sauvegarde finale
    save_csv(country, "country.csv")
    save_csv(city, "city.csv")
    save_csv(station, "station.csv")
    save_csv(operator, "operator.csv")
    save_csv(train_type, "train_type.csv")
    save_csv(data_source, "data_source.csv")
    save_csv(route, "route.csv")
    save_csv(trip, "trip.csv")
    save_csv(trip_stop, "trip_stop.csv")
    save_csv(quality_check, "quality_check.csv")

    print("\nTransformation terminée avec succès.")


if __name__ == "__main__":
    main()