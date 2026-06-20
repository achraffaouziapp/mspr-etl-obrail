from pathlib import Path
import pandas as pd


PROCESSED_DIR = Path("data/processed")

FILES = [
    "country.csv",
    "city.csv",
    "station.csv",
    "operator.csv",
    "train_type.csv",
    "data_source.csv",
    "route.csv",
    "trip.csv",
    "trip_stop.csv",
    "quality_check.csv",
]


def check_file_exists(file_name: str) -> bool:
    file_path = PROCESSED_DIR / file_name

    if not file_path.exists():
        print(f"[ERREUR] Fichier manquant : {file_name}")
        return False

    print(f"[OK] Fichier trouvé : {file_name}")
    return True


def check_basic_info(file_name: str) -> pd.DataFrame | None:
    file_path = PROCESSED_DIR / file_name

    try:
        df = pd.read_csv(file_path)
    except Exception as error:
        print(f"[ERREUR] Impossible de lire {file_name} : {error}")
        return None

    print("-" * 80)
    print(f"Fichier : {file_name}")
    print(f"Nombre de lignes : {len(df)}")
    print(f"Nombre de colonnes : {len(df.columns)}")
    print(f"Colonnes : {list(df.columns)}")

    print("\nAperçu :")
    print(df.head(5))

    print("\nValeurs manquantes par colonne :")
    missing_values = df.isna().sum()
    print(missing_values[missing_values > 0])

    return df


def check_primary_key(df: pd.DataFrame, file_name: str, primary_key: str) -> None:
    print(f"\nVérification clé primaire : {primary_key}")

    if primary_key not in df.columns:
        print(f"[ERREUR] Colonne PK absente dans {file_name} : {primary_key}")
        return

    missing_pk = df[primary_key].isna().sum()
    duplicate_pk = df[primary_key].duplicated().sum()

    if missing_pk == 0:
        print(f"[OK] Aucune clé primaire manquante")
    else:
        print(f"[ERREUR] {missing_pk} clé(s) primaire(s) manquante(s)")

    if duplicate_pk == 0:
        print(f"[OK] Aucune clé primaire dupliquée")
    else:
        print(f"[ERREUR] {duplicate_pk} clé(s) primaire(s) dupliquée(s)")


def check_foreign_key(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    child_file: str,
    parent_file: str,
    fk_column: str,
    pk_column: str
) -> None:
    print(f"\nVérification FK : {child_file}.{fk_column} -> {parent_file}.{pk_column}")

    if fk_column not in child_df.columns:
        print(f"[ERREUR] Colonne FK absente : {fk_column}")
        return

    if pk_column not in parent_df.columns:
        print(f"[ERREUR] Colonne PK parent absente : {pk_column}")
        return

    child_values = set(child_df[fk_column].dropna().astype(str))
    parent_values = set(parent_df[pk_column].dropna().astype(str))

    invalid_values = child_values - parent_values

    if len(invalid_values) == 0:
        print("[OK] Toutes les clés étrangères sont valides")
    else:
        print(f"[ERREUR] {len(invalid_values)} valeur(s) FK invalide(s)")
        print(f"Exemples : {list(invalid_values)[:10]}")


def check_trip_type_distribution(trip_df: pd.DataFrame, train_type_df: pd.DataFrame) -> None:
    print("\nRépartition des types de train")

    if "train_type_id" not in trip_df.columns:
        print("[ERREUR] train_type_id absent dans trip.csv")
        return

    distribution = trip_df["train_type_id"].value_counts(dropna=False)
    print(distribution)

    if "train_type_id" in train_type_df.columns and "type_name" in train_type_df.columns:
        merged = (
            trip_df
            .merge(train_type_df, on="train_type_id", how="left")
            .groupby("type_name")
            .size()
            .reset_index(name="number_of_trips")
        )

        print("\nRépartition lisible :")
        print(merged)

    if len(distribution) == 1:
        print("[ATTENTION] Un seul type de train est présent dans trip.csv")
        print("Cela veut probablement dire que les trains de nuit ne sont pas encore intégrés.")
    else:
        print("[OK] Plusieurs types de train sont présents")


def check_quality_scores(quality_df: pd.DataFrame) -> None:
    print("\nVérification des scores qualité")

    if "quality_score" not in quality_df.columns:
        print("[ERREUR] quality_score absent dans quality_check.csv")
        return

    quality_df["quality_score"] = pd.to_numeric(quality_df["quality_score"], errors="coerce")

    print("Score minimum :", quality_df["quality_score"].min())
    print("Score maximum :", quality_df["quality_score"].max())
    print("Score moyen :", round(quality_df["quality_score"].mean(), 2))

    if quality_df["quality_score"].between(0, 100).all():
        print("[OK] Les scores qualité sont entre 0 et 100")
    else:
        print("[ERREUR] Certains scores qualité sont hors limites")


def main():
    print("Début de la vérification des fichiers transformés")
    print("=" * 80)

    dataframes = {}

    for file_name in FILES:
        if check_file_exists(file_name):
            df = check_basic_info(file_name)
            if df is not None:
                dataframes[file_name] = df

    print("\n" + "=" * 80)
    print("Vérification des clés primaires")
    print("=" * 80)

    primary_keys = {
        "country.csv": "country_id",
        "city.csv": "city_id",
        "station.csv": "station_id",
        "operator.csv": "operator_id",
        "train_type.csv": "train_type_id",
        "data_source.csv": "data_source_id",
        "route.csv": "route_id",
        "trip.csv": "trip_id",
        "trip_stop.csv": "trip_stop_id",
        "quality_check.csv": "quality_check_id",
    }

    for file_name, primary_key in primary_keys.items():
        if file_name in dataframes:
            check_primary_key(dataframes[file_name], file_name, primary_key)

    print("\n" + "=" * 80)
    print("Vérification des relations entre les tables")
    print("=" * 80)

    if "city.csv" in dataframes and "country.csv" in dataframes:
        check_foreign_key(
            dataframes["city.csv"],
            dataframes["country.csv"],
            "city.csv",
            "country.csv",
            "country_id",
            "country_id"
        )

    if "station.csv" in dataframes and "city.csv" in dataframes:
        check_foreign_key(
            dataframes["station.csv"],
            dataframes["city.csv"],
            "station.csv",
            "city.csv",
            "city_id",
            "city_id"
        )

    if "operator.csv" in dataframes and "country.csv" in dataframes:
        check_foreign_key(
            dataframes["operator.csv"],
            dataframes["country.csv"],
            "operator.csv",
            "country.csv",
            "country_id",
            "country_id"
        )

    if "route.csv" in dataframes and "station.csv" in dataframes:
        check_foreign_key(
            dataframes["route.csv"],
            dataframes["station.csv"],
            "route.csv",
            "station.csv",
            "departure_station_id",
            "station_id"
        )

        check_foreign_key(
            dataframes["route.csv"],
            dataframes["station.csv"],
            "route.csv",
            "station.csv",
            "arrival_station_id",
            "station_id"
        )

    if "route.csv" in dataframes and "operator.csv" in dataframes:
        check_foreign_key(
            dataframes["route.csv"],
            dataframes["operator.csv"],
            "route.csv",
            "operator.csv",
            "operator_id",
            "operator_id"
        )

    if "trip.csv" in dataframes and "route.csv" in dataframes:
        check_foreign_key(
            dataframes["trip.csv"],
            dataframes["route.csv"],
            "trip.csv",
            "route.csv",
            "route_id",
            "route_id"
        )

    if "trip.csv" in dataframes and "train_type.csv" in dataframes:
        check_foreign_key(
            dataframes["trip.csv"],
            dataframes["train_type.csv"],
            "trip.csv",
            "train_type.csv",
            "train_type_id",
            "train_type_id"
        )

    if "trip.csv" in dataframes and "data_source.csv" in dataframes:
        check_foreign_key(
            dataframes["trip.csv"],
            dataframes["data_source.csv"],
            "trip.csv",
            "data_source.csv",
            "data_source_id",
            "data_source_id"
        )

    if "trip_stop.csv" in dataframes and "trip.csv" in dataframes:
        check_foreign_key(
            dataframes["trip_stop.csv"],
            dataframes["trip.csv"],
            "trip_stop.csv",
            "trip.csv",
            "trip_id",
            "trip_id"
        )

    if "trip_stop.csv" in dataframes and "station.csv" in dataframes:
        check_foreign_key(
            dataframes["trip_stop.csv"],
            dataframes["station.csv"],
            "trip_stop.csv",
            "station.csv",
            "station_id",
            "station_id"
        )

    if "quality_check.csv" in dataframes and "trip.csv" in dataframes:
        check_foreign_key(
            dataframes["quality_check.csv"],
            dataframes["trip.csv"],
            "quality_check.csv",
            "trip.csv",
            "trip_id",
            "trip_id"
        )

    print("\n" + "=" * 80)
    print("Vérifications métier")
    print("=" * 80)

    if "trip.csv" in dataframes and "train_type.csv" in dataframes:
        check_trip_type_distribution(dataframes["trip.csv"], dataframes["train_type.csv"])

    if "quality_check.csv" in dataframes:
        check_quality_scores(dataframes["quality_check.csv"])

    print("\n" + "=" * 80)
    print("Vérification terminée")
    print("=" * 80)


if __name__ == "__main__":
    main()