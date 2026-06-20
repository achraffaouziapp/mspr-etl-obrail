"""
Charge les fichiers transformés dans PostgreSQL.

Le script recrée les tables à partir du fichier SQL, importe les CSV dans le bon ordre
pour respecter les clés étrangères, puis vérifie le nombre de lignes chargées.
"""

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
    """
    Ouvre une connexion PostgreSQL avec la configuration du projet.

    La même fonction est utilisée pour toutes les opérations de création de tables, chargement et vérification.
    """
    return psycopg2.connect(**DB_CONFIG)


def execute_sql_file(connection, sql_file: Path):
    """
    Exécute le fichier SQL qui crée les tables de la base.

    Cette étape repart d'un schéma propre avant d'importer les CSV transformés.
    """
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
    """
    Charge un fichier CSV dans une table PostgreSQL avec la commande COPY.

    COPY est utilisé car il est plus rapide et plus adapté au chargement de gros fichiers qu'une insertion ligne par ligne.
    """
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
    """
    Compte le nombre de lignes présentes dans une table.

    Cette fonction sert à vérifier que le chargement a bien alimenté chaque table.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]

    return count


def verify_loading(connection):
    """
    Affiche le nombre de lignes chargées pour chaque table.

    Cela donne un contrôle rapide en fin de chargement et facilite la détection d'une table vide.
    """
    print("\nVérification du chargement")
    print("-" * 80)

    for table_name, _ in LOAD_ORDER:
        count = count_rows(connection, table_name)
        print(f"{table_name} : {count} lignes")


def main():
    """
    Point d'entrée du script.

    Cette fonction organise les étapes dans le bon ordre et affiche des messages de suivi dans le terminal.
    """
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
