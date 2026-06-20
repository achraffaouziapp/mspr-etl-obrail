import os
from decimal import Decimal
from datetime import date, datetime, time

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "obrail"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection():
    """
    Ouvre une connexion PostgreSQL.
    """
    return psycopg2.connect(**DB_CONFIG)


def serialize_value(value):
    """
    Convertit les types PostgreSQL non directement sérialisables en JSON.
    """
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime, time)):
        return value.isoformat()

    return value


def serialize_row(row: dict) -> dict:
    """
    Convertit une ligne SQL en dictionnaire JSON-compatible.
    """
    return {key: serialize_value(value) for key, value in row.items()}


def execute_query(query: str, params: tuple | list | None = None, fetch_one: bool = False):
    """
    Exécute une requête SQL SELECT et retourne les résultats.
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