from pathlib import Path
import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "obrail",
    "user": "postgres",
    "password": "postgres",
}

SQL_FILE = Path("sql/create_tables.sql")
PROCESSED_DIR = Path("data/processed")


LOAD_ORDER = [
    ("country", "country.csv"),
    ("city", "city.csv"),
    ("station", "station.csv"),
    ('"operator"', "operator.csv"),
    ("train_type", "train_type.csv"),
    ("data_source", "data_source.csv"),
    ("route", "route.csv"),
    ("trip", "trip.csv"),
    ("trip_stop", "trip_stop.csv"),
    ("quality_check", "quality_check.csv"),
]


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def execute_sql_file(connection, sql_file: Path):
    if not sql_file.exists():
        raise FileNotFoundError(f"Fichier SQL introuvable : {sql_file}")

    print(f"Exécution du script SQL : {sql_file}")

    with open(sql_file, "r", encoding="utf-8") as file:
        sql_script = file.read()

    with connection.cursor() as cursor:
        cursor.execute(sql_script)

    connection.commit()

    print("[OK] Tables créées avec succès")


def load_csv_to_table(connection, table_name: str, csv_file: str):
    csv_path = PROCESSED_DIR / csv_file

    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier CSV introuvable : {csv_path}")

    print(f"Chargement de {csv_file} vers {table_name}...")

    copy_sql = f"""
        COPY {table_name}
        FROM STDIN
        WITH (
            FORMAT CSV,
            HEADER TRUE,
            NULL '',
            DELIMITER ','
        );
    """

    with connection.cursor() as cursor:
        with open(csv_path, "r", encoding="utf-8") as file:
            cursor.copy_expert(copy_sql, file)

    connection.commit()

    print(f"[OK] {csv_file} chargé")


def count_rows(connection, table_name: str):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]

    return count


def verify_loading(connection):
    print("\nVérification du chargement")
    print("-" * 80)

    for table_name, _ in LOAD_ORDER:
        count = count_rows(connection, table_name)
        print(f"{table_name} : {count} lignes")


def main():
    print("Début du chargement PostgreSQL")

    connection = get_connection()

    try:
        execute_sql_file(connection, SQL_FILE)

        for table_name, csv_file in LOAD_ORDER:
            load_csv_to_table(connection, table_name, csv_file)

        verify_loading(connection)

        print("\nChargement PostgreSQL terminé avec succès.")

    except Exception as error:
        connection.rollback()
        print("\n[ERREUR] Le chargement a échoué.")
        print(error)

    finally:
        connection.close()


if __name__ == "__main__":
    main()