import os
from decimal import Decimal
from datetime import date, datetime, time

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# Charge les variables du fichier .env afin d'éviter d'écrire les identifiants
# de connexion directement dans le code.
load_dotenv()


# Regroupe tous les paramètres nécessaires pour se connecter à PostgreSQL.
# Les valeurs par défaut permettent de lancer le projet en local avec Docker.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "obrail"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection():
    """
    Crée une nouvelle connexion à la base PostgreSQL.

    Cette fonction centralise la connexion afin que le reste de l'API n'ait pas
    besoin de connaître les détails techniques comme le host, le port ou le mot
    de passe. Chaque requête ouvre une connexion puis la referme proprement.
    """
    return psycopg2.connect(**DB_CONFIG)


def serialize_value(value):
    """
    Transforme une valeur PostgreSQL en valeur compatible avec une réponse JSON.

    FastAPI sait retourner du JSON, mais certains types venant de PostgreSQL,
    comme Decimal, date, datetime ou time, doivent être convertis avant d'être
    envoyés au navigateur ou à Postman.
    """
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime, time)):
        return value.isoformat()

    return value


def serialize_row(row: dict) -> dict:
    """
    Convertit une ligne SQL complète en dictionnaire compatible JSON.

    La base renvoie une ligne sous forme de dictionnaire. Cette fonction parcourt
    chaque colonne et applique la conversion adaptée à sa valeur.
    """
    return {key: serialize_value(value) for key, value in row.items()}


def execute_query(query: str, params: tuple | list | None = None, fetch_one: bool = False):
    """
    Exécute une requête SQL et retourne le résultat sous forme de dictionnaire.

    - query contient la requête SQL à exécuter.
    - params contient les valeurs utilisées dans les filtres SQL.
    - fetch_one permet de récupérer une seule ligne au lieu d'une liste.

    La fonction utilise RealDictCursor pour obtenir directement des résultats
    lisibles, avec le nom des colonnes comme clés.
    """
    connection = get_connection()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)

            if fetch_one:
                row = cursor.fetchone()
                return serialize_row(row) if row else None

            rows = cursor.fetchall()
            return [serialize_row(row) for row in rows]

    finally:
        connection.close()
