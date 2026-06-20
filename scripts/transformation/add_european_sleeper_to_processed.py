"""
Transformation additionnelle - European Sleeper

Ce script s'exécute après scripts/transformation/transform_all_sources.py.
Il enrichit les fichiers data/processed/*.csv avec une nouvelle source de trains de nuit :
European Sleeper Timetable.

Ordre conseillé :
1. python scripts/extraction/extract_european_sleeper.py
2. python scripts/transformation/transform_all_sources.py
3. python scripts/transformation/add_european_sleeper_to_processed.py
4. python scripts/loading/load_to_postgres.py
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw" / "european_sleeper"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

SERVICE_START_DATE = date(2026, 6, 19)
SERVICE_END_DATE = date(2026, 12, 31)

DAY_NAME_TO_WEEKDAY = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


# ============================================================
# Fonctions fichiers
# ============================================================

def read_processed_csv(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    return pd.read_csv(path)


def write_processed_csv(df: pd.DataFrame, name: str) -> None:
    path = PROCESSED_DIR / name
    df.to_csv(path, index=False, encoding="utf-8")


# ============================================================
# Fonctions utilitaires
# ============================================================

def next_id(df: pd.DataFrame, id_column: str) -> int:
    if df.empty or id_column not in df.columns:
        return 1

    values = pd.to_numeric(df[id_column], errors="coerce")

    if values.dropna().empty:
        return 1

    return int(values.max()) + 1


def clean(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def to_int(value):
    if pd.isna(value) or str(value).strip() == "":
        return None

    return int(float(value))


def force_integer_csv_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """
    Force certaines colonnes à être exportées comme entiers propres dans le CSV.

    Exemple :
    0.0 -> 0
    1.0 -> 1
    NaN -> vide
    """
    df = df.copy()

    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
            df[column] = df[column].apply(
                lambda value: "" if pd.isna(value) else str(int(value))
            )

    return df


def time_to_minutes(time_value, day_offset=0):
    if pd.isna(time_value) or str(time_value).strip() == "":
        return None

    parts = str(time_value).split(":")
    hours = int(parts[0])
    minutes = int(parts[1])

    return int(day_offset or 0) * 1440 + hours * 60 + minutes


def generate_service_dates(operating_days: str):
    allowed_weekdays = {
        DAY_NAME_TO_WEEKDAY[item.strip()]
        for item in operating_days.split(",")
        if item.strip() in DAY_NAME_TO_WEEKDAY
    }

    current_date = SERVICE_START_DATE

    while current_date <= SERVICE_END_DATE:
        if current_date.weekday() in allowed_weekdays:
            yield current_date

        current_date += timedelta(days=1)


# ============================================================
# Fonctions d'ajout des dimensions
# ============================================================

def get_or_add_country(country_df, country_name, country_code):
    country_name = clean(country_name)
    country_code = clean(country_code).upper()

    match = country_df[
        (country_df["country_name"].astype(str).str.lower() == country_name.lower())
        & (country_df["country_code"].astype(str).str.upper() == country_code)
    ]

    if not match.empty:
        return int(match.iloc[0]["country_id"]), country_df

    new_id = next_id(country_df, "country_id")

    new_row = {
        "country_id": new_id,
        "country_name": country_name,
        "country_code": country_code,
    }

    country_df = pd.concat(
        [country_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, country_df


def get_or_add_city(city_df, city_name, country_id):
    city_name = clean(city_name)

    match = city_df[
        (city_df["city_name"].astype(str).str.lower() == city_name.lower())
        & (pd.to_numeric(city_df["country_id"], errors="coerce") == int(country_id))
    ]

    if not match.empty:
        return int(match.iloc[0]["city_id"]), city_df

    new_id = next_id(city_df, "city_id")

    new_row = {
        "city_id": new_id,
        "city_name": city_name,
        "country_id": country_id,
    }

    city_df = pd.concat(
        [city_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, city_df


def get_or_add_station(station_df, station_row, city_id):
    station_code = clean(station_row["station_code"])
    station_name = clean(station_row["station_name"])

    if "station_code" in station_df.columns:
        match_by_code = station_df[
            station_df["station_code"].fillna("").astype(str).str.upper()
            == station_code.upper()
        ]

        if not match_by_code.empty:
            return int(match_by_code.iloc[0]["station_id"]), station_df

    match_by_name_city = station_df[
        (station_df["station_name"].astype(str).str.lower() == station_name.lower())
        & (pd.to_numeric(station_df["city_id"], errors="coerce") == int(city_id))
    ]

    if not match_by_name_city.empty:
        return int(match_by_name_city.iloc[0]["station_id"]), station_df

    new_id = next_id(station_df, "station_id")

    new_row = {
        "station_id": new_id,
        "station_name": station_name,
        "station_code": station_code,
        "latitude": station_row.get("latitude", ""),
        "longitude": station_row.get("longitude", ""),
        "timezone": station_row.get("timezone", ""),
        "city_id": city_id,
    }

    station_df = pd.concat(
        [station_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, station_df


def get_or_add_operator(operator_df, country_df):
    operator_name = "European Sleeper"
    operator_code = "ES"

    country_id, country_df = get_or_add_country(
        country_df,
        "Netherlands",
        "NL"
    )

    match = operator_df[
        operator_df["operator_name"].astype(str).str.lower()
        == operator_name.lower()
    ]

    if not match.empty:
        return int(match.iloc[0]["operator_id"]), operator_df, country_df

    new_id = next_id(operator_df, "operator_id")

    new_row = {
        "operator_id": new_id,
        "operator_name": operator_name,
        "operator_code": operator_code,
        "country_id": country_id,
    }

    operator_df = pd.concat(
        [operator_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, operator_df, country_df


def get_or_add_train_type(train_type_df):
    match = train_type_df[
        train_type_df["type_name"].astype(str).str.lower() == "night"
    ]

    if not match.empty:
        return int(match.iloc[0]["train_type_id"]), train_type_df

    new_id = next_id(train_type_df, "train_type_id")

    new_row = {
        "train_type_id": new_id,
        "type_name": "night",
    }

    train_type_df = pd.concat(
        [train_type_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, train_type_df


def get_or_add_data_source(data_source_df):
    metadata_path = RAW_DIR / "metadata.json"

    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as file:
            metadata = json.load(file)
    else:
        metadata = {}

    source_name = "European Sleeper Timetable"

    match = data_source_df[
        data_source_df["source_name"].astype(str).str.lower()
        == source_name.lower()
    ]

    if not match.empty:
        return int(match.iloc[0]["data_source_id"]), data_source_df

    new_id = next_id(data_source_df, "data_source_id")

    new_row = {
        "data_source_id": new_id,
        "source_name": source_name,
        "source_url": metadata.get(
            "source_url",
            "https://www.europeansleeper.eu/timetable"
        ),
        "source_format": metadata.get("source_format", "HTML + structured CSV"),
        "extraction_date": metadata.get(
            "extraction_date",
            datetime.now(timezone.utc).isoformat()
        ),
        "licence": metadata.get("licence", "Public timetable page"),
        "raw_file_name": "data/raw/european_sleeper",
        "import_status": metadata.get("import_status", "OK"),
    }

    data_source_df = pd.concat(
        [data_source_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, data_source_df


def get_or_add_route(route_df, departure_station_id, arrival_station_id, operator_id):
    numeric_route = route_df.copy()
    numeric_route["departure_station_id"] = pd.to_numeric(
        numeric_route["departure_station_id"],
        errors="coerce"
    )
    numeric_route["arrival_station_id"] = pd.to_numeric(
        numeric_route["arrival_station_id"],
        errors="coerce"
    )
    numeric_route["operator_id"] = pd.to_numeric(
        numeric_route["operator_id"],
        errors="coerce"
    )

    match = numeric_route[
        (numeric_route["departure_station_id"] == int(departure_station_id))
        & (numeric_route["arrival_station_id"] == int(arrival_station_id))
        & (numeric_route["operator_id"] == int(operator_id))
    ]

    if not match.empty:
        return int(match.iloc[0]["route_id"]), route_df

    new_id = next_id(route_df, "route_id")

    new_row = {
        "route_id": new_id,
        "departure_station_id": departure_station_id,
        "arrival_station_id": arrival_station_id,
        "operator_id": operator_id,
        "distance_km": "",
    }

    route_df = pd.concat(
        [route_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return new_id, route_df


# ============================================================
# Programme principal
# ============================================================

def main():
    print("Ajout de la source European Sleeper dans data/processed...")

    required_files = [
        RAW_DIR / "european_sleeper_stations.csv",
        RAW_DIR / "european_sleeper_routes.csv",
        RAW_DIR / "european_sleeper_stop_times.csv",
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"{path} introuvable. "
                "Lance d'abord scripts/extraction/extract_european_sleeper.py"
            )

    es_stations = pd.read_csv(RAW_DIR / "european_sleeper_stations.csv")
    es_routes = pd.read_csv(RAW_DIR / "european_sleeper_routes.csv")
    es_stop_times = pd.read_csv(RAW_DIR / "european_sleeper_stop_times.csv")

    country_df = read_processed_csv("country.csv")
    city_df = read_processed_csv("city.csv")
    station_df = read_processed_csv("station.csv")
    operator_df = read_processed_csv("operator.csv")
    train_type_df = read_processed_csv("train_type.csv")
    data_source_df = read_processed_csv("data_source.csv")
    route_df = read_processed_csv("route.csv")
    trip_df = read_processed_csv("trip.csv")
    trip_stop_df = read_processed_csv("trip_stop.csv")
    quality_df = read_processed_csv("quality_check.csv")

    station_code_to_id = {}

    # Ajout des pays, villes et gares European Sleeper
    for _, station_row in es_stations.iterrows():
        country_id, country_df = get_or_add_country(
            country_df,
            station_row["country_name"],
            station_row["country_code"]
        )

        city_id, city_df = get_or_add_city(
            city_df,
            station_row["city_name"],
            country_id
        )

        station_id, station_df = get_or_add_station(
            station_df,
            station_row,
            city_id
        )

        station_code_to_id[clean(station_row["station_code"])] = station_id

    operator_id, operator_df, country_df = get_or_add_operator(
        operator_df,
        country_df
    )

    train_type_id, train_type_df = get_or_add_train_type(train_type_df)
    data_source_id, data_source_df = get_or_add_data_source(data_source_df)

    existing_trip_codes = set(trip_df["trip_code"].astype(str).tolist())

    next_trip_id = next_id(trip_df, "trip_id")
    next_trip_stop_id = next_id(trip_stop_df, "trip_stop_id")
    next_quality_id = next_id(quality_df, "quality_check_id")

    new_trip_rows = []
    new_trip_stop_rows = []
    new_quality_rows = []

    for _, route_row in es_routes.iterrows():
        train_code = clean(route_row["train_code"])

        departure_station_id = station_code_to_id[
            clean(route_row["origin_station_code"])
        ]
        arrival_station_id = station_code_to_id[
            clean(route_row["destination_station_code"])
        ]

        route_id, route_df = get_or_add_route(
            route_df,
            departure_station_id,
            arrival_station_id,
            operator_id
        )

        pattern_stops = es_stop_times[
            es_stop_times["train_code"].astype(str) == train_code
        ].sort_values("stop_order")

        first_stop = pattern_stops.iloc[0]
        last_stop = pattern_stops.iloc[-1]

        departure_time = clean(first_stop["departure_time"])
        departure_day_offset = to_int(first_stop["departure_day_offset"]) or 0

        arrival_time = clean(last_stop["arrival_time"])
        arrival_day_offset = to_int(last_stop["arrival_day_offset"]) or 0

        departure_minutes = time_to_minutes(departure_time, departure_day_offset)
        arrival_minutes = time_to_minutes(arrival_time, arrival_day_offset)

        duration_minutes = ""

        if departure_minutes is not None and arrival_minutes is not None:
            duration_minutes = arrival_minutes - departure_minutes

        for service_date in generate_service_dates(clean(route_row["operating_days"])):
            trip_code = (
                f"EUROPEAN_SLEEPER_"
                f"{train_code.replace(' ', '')}_"
                f"{service_date.strftime('%Y%m%d')}"
            )

            if trip_code in existing_trip_codes:
                continue

            trip_id = next_trip_id
            next_trip_id += 1
            existing_trip_codes.add(trip_code)

            has_missing_values = (
                departure_time == ""
                or arrival_time == ""
                or duration_minutes == ""
            )

            has_time_error = (
                duration_minutes == ""
                or int(duration_minutes) <= 0
            )

            quality_score = 100
            error_messages = []

            if has_missing_values:
                quality_score -= 40
                error_messages.append("Valeurs manquantes")

            if has_time_error:
                quality_score -= 30
                error_messages.append("Erreur horaire ou durée invalide")

            new_trip_rows.append({
                "trip_id": trip_id,
                "route_id": route_id,
                "train_type_id": train_type_id,
                "data_source_id": data_source_id,
                "trip_code": trip_code,
                "service_date": service_date.isoformat(),
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "departure_day_offset": departure_day_offset,
                "arrival_day_offset": arrival_day_offset,
                "duration_minutes": duration_minutes,
                "co2_estimated_kg": "",
            })

            for _, stop_row in pattern_stops.iterrows():
                station_id = station_code_to_id[clean(stop_row["station_code"])]

                new_trip_stop_rows.append({
                    "trip_stop_id": next_trip_stop_id,
                    "trip_id": trip_id,
                    "station_id": station_id,
                    "stop_order": int(stop_row["stop_order"]),
                    "arrival_time": clean(stop_row["arrival_time"]),
                    "departure_time": clean(stop_row["departure_time"]),
                    "arrival_day_offset": clean(stop_row["arrival_day_offset"]),
                    "departure_day_offset": clean(stop_row["departure_day_offset"]),
                })

                next_trip_stop_id += 1

            new_quality_rows.append({
                "quality_check_id": next_quality_id,
                "trip_id": trip_id,
                "has_missing_values": bool(has_missing_values),
                "has_time_error": bool(has_time_error),
                "is_duplicate": False,
                "quality_score": max(0, quality_score),
                "rule_name": "European Sleeper quality rules",
                "error_message": "; ".join(error_messages),
                "check_date": date.today().isoformat(),
            })

            next_quality_id += 1

    if new_trip_rows:
        trip_df = pd.concat(
            [trip_df, pd.DataFrame(new_trip_rows)],
            ignore_index=True
        )
        trip_stop_df = pd.concat(
            [trip_stop_df, pd.DataFrame(new_trip_stop_rows)],
            ignore_index=True
        )
        quality_df = pd.concat(
            [quality_df, pd.DataFrame(new_quality_rows)],
            ignore_index=True
        )

    # ========================================================
    # Correction importante avant export CSV
    # Empêche PostgreSQL de recevoir 0.0 dans les colonnes INTEGER
    # ========================================================

    country_df = force_integer_csv_columns(
        country_df,
        ["country_id"]
    )

    city_df = force_integer_csv_columns(
        city_df,
        ["city_id", "country_id"]
    )

    station_df = force_integer_csv_columns(
        station_df,
        ["station_id", "city_id"]
    )

    operator_df = force_integer_csv_columns(
        operator_df,
        ["operator_id", "country_id"]
    )

    train_type_df = force_integer_csv_columns(
        train_type_df,
        ["train_type_id"]
    )

    data_source_df = force_integer_csv_columns(
        data_source_df,
        ["data_source_id"]
    )

    route_df = force_integer_csv_columns(
        route_df,
        [
            "route_id",
            "departure_station_id",
            "arrival_station_id",
            "operator_id",
        ]
    )

    trip_df = force_integer_csv_columns(
        trip_df,
        [
            "trip_id",
            "route_id",
            "train_type_id",
            "data_source_id",
            "departure_day_offset",
            "arrival_day_offset",
        ]
    )

    trip_stop_df = force_integer_csv_columns(
        trip_stop_df,
        [
            "trip_stop_id",
            "trip_id",
            "station_id",
            "stop_order",
            "arrival_day_offset",
            "departure_day_offset",
        ]
    )

    quality_df = force_integer_csv_columns(
        quality_df,
        [
            "quality_check_id",
            "trip_id",
            "quality_score",
        ]
    )

    write_processed_csv(country_df, "country.csv")
    write_processed_csv(city_df, "city.csv")
    write_processed_csv(station_df, "station.csv")
    write_processed_csv(operator_df, "operator.csv")
    write_processed_csv(train_type_df, "train_type.csv")
    write_processed_csv(data_source_df, "data_source.csv")
    write_processed_csv(route_df, "route.csv")
    write_processed_csv(trip_df, "trip.csv")
    write_processed_csv(trip_stop_df, "trip_stop.csv")
    write_processed_csv(quality_df, "quality_check.csv")

    print("[OK] European Sleeper ajouté aux fichiers processed")
    print(f"Nouveaux trips ajoutés : {len(new_trip_rows)}")
    print(f"Nouveaux trip_stop ajoutés : {len(new_trip_stop_rows)}")
    print(f"Nouveaux quality_check ajoutés : {len(new_quality_rows)}")


if __name__ == "__main__":
    main()
