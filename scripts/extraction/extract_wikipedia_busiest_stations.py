"""
Extrait un tableau Wikipedia listant des gares européennes très fréquentées.

Cette source complète les autres fichiers avec des informations géographiques issues
d'un tableau HTML. Le script sauvegarde à la fois la page brute et le CSV extrait.
"""

from pathlib import Path
from datetime import datetime
import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

print("SCRIPT LANCÉ")

SOURCE_URL = "https://en.wikipedia.org/wiki/List_of_busiest_railway_stations_in_Europe"

SOURCE_NAME = "Wikipedia - List of busiest railway stations in Europe"
SOURCE_FORMAT = "HTML scraping"
SOURCE_DESCRIPTION = (
    "Scraping d'un tableau HTML listant des gares ferroviaires européennes "
    "avec pays, ville, gare, fréquentation, nombre de quais et année de référence."
)

OUTPUT_DIR = Path("data/raw/wikipedia_busiest_stations_europe")
HTML_PATH = OUTPUT_DIR / "page.html"
CSV_PATH = OUTPUT_DIR / "busiest_railway_stations_europe.csv"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def normalize_column_name(column_name: str) -> str:
    """
    Convertit un nom de colonne en format simple et stable.

    Les espaces, accents faibles, ponctuations ou caractères spéciaux sont remplacés pour obtenir
    des noms plus faciles à utiliser pendant la transformation.
    """
    column_name = str(column_name).strip().lower()
    column_name = re.sub(r"[^a-z0-9]+", "_", column_name)
    column_name = column_name.strip("_")
    return column_name


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplatit les colonnes multi-niveaux qui peuvent apparaître dans certains tableaux HTML.

    Cette étape rend les colonnes compatibles avec un CSV classique.
    """
    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        new_columns = []

        for col in df.columns:
            clean_parts = [
                str(part)
                for part in col
                if str(part) != "nan" and not str(part).lower().startswith("unnamed")
            ]

            new_columns.append("_".join(clean_parts))

        df.columns = new_columns

    df.columns = [normalize_column_name(col) for col in df.columns]

    return df


def download_html() -> str:
    """
    Télécharge la page Wikipedia et sauvegarde le HTML brut.

    Garder le HTML permet de tracer exactement quelle page a été utilisée pour l'extraction.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "ObRail-ETL-Student-Project/1.0"
    }

    print(f"Téléchargement de la page : {SOURCE_URL}")

    response = requests.get(SOURCE_URL, headers=headers, timeout=60)
    response.raise_for_status()

    html_content = response.text

    with open(HTML_PATH, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"[OK] HTML sauvegardé : {HTML_PATH}")

    return html_content


def html_table_to_dataframe(table) -> pd.DataFrame:
    """
    Convertit un tableau HTML en DataFrame pandas sans dépendre de lxml.

    La fonction lit les lignes et cellules HTML avec BeautifulSoup, nettoie les références Wikipedia
    et reconstruit un tableau exploitable en CSV.
    """
    headers = []
    rows = []

    for tr in table.find_all("tr"):
        th_cells = tr.find_all("th")
        td_cells = tr.find_all("td")
        cells = tr.find_all(["th", "td"])

        if not cells:
            continue

        values = []

        for cell in cells:
            text = cell.get_text(" ", strip=True)


            text = re.sub(r"\[\d+\]", "", text).strip()

            colspan = int(cell.get("colspan", 1))

            for _ in range(colspan):
                values.append(text)


        if th_cells and not td_cells:
            if not headers:
                headers = values
            continue

        rows.append(values)

    if not rows:
        raise ValueError("Le tableau HTML ne contient aucune ligne de données.")

    max_columns = max(len(row) for row in rows)

    if not headers:
        headers = [f"column_{i + 1}" for i in range(max_columns)]

    if len(headers) < max_columns:
        headers += [f"column_{i + 1}" for i in range(len(headers), max_columns)]

    headers = headers[:max_columns]

    cleaned_rows = []

    for row in rows:
        if len(row) < max_columns:
            row = row + [None] * (max_columns - len(row))

        if len(row) > max_columns:
            row = row[:max_columns]

        cleaned_rows.append(row)

    df = pd.DataFrame(cleaned_rows, columns=headers)


    df.columns = [normalize_column_name(col) for col in df.columns]


    unique_columns = []
    seen = {}

    for col in df.columns:
        if col not in seen:
            seen[col] = 1
            unique_columns.append(col)
        else:
            seen[col] += 1
            unique_columns.append(f"{col}_{seen[col]}")

    df.columns = unique_columns

    return df


def find_target_table(html_content: str) -> pd.DataFrame:
    """
    Recherche dans la page HTML le tableau correspondant aux gares européennes.

    Le tableau cible est identifié grâce à des mots-clés comme country, city et railway station.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table", class_="wikitable")

    print(f"Nombre de tableaux HTML trouvés : {len(tables)}")

    for index, table in enumerate(tables, start=1):
        table_text = table.get_text(" ", strip=True).lower()

        if (
            "country" in table_text
            and "city" in table_text
            and "railway station" in table_text
        ):
            print(f"[OK] Tableau cible trouvé : table #{index}")

            df = html_table_to_dataframe(table)
            return df

    raise ValueError("Aucun tableau correspondant aux gares européennes n'a été trouvé.")


def clean_scraped_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie légèrement le tableau extrait de Wikipedia.

    Le but est seulement de supprimer les lignes vides et doublons. L'harmonisation complète est
    réalisée plus tard dans le script de transformation.
    """
    df = df.copy()

    df = df.dropna(how="all")
    df = df.drop_duplicates()

    for column in df.columns:
        df[column] = df[column].astype(str).str.strip()
        df[column] = df[column].replace({"nan": None, "None": None, "": None})

    return df


def save_csv(df: pd.DataFrame) -> None:
    """
    Sauvegarde un DataFrame dans le dossier des données transformées ou brutes.

    La fonction centralise l'écriture CSV et affiche le nombre de lignes générées.
    """
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"[OK] CSV sauvegardé : {CSV_PATH}")
    print(f"Nombre de lignes extraites : {len(df)}")
    print(f"Colonnes : {list(df.columns)}")
    print("\nAperçu :")
    print(df.head(5))


def save_metadata(row_count: int, columns: list[str]) -> None:
    """
    Écrit un fichier metadata.json décrivant l'extraction.

    Les métadonnées permettent de savoir quelle source a été utilisée, quand elle a été
    extraite et quels fichiers bruts ont été produits.
    """
    metadata = {
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "source_format": SOURCE_FORMAT,
        "source_description": SOURCE_DESCRIPTION,
        "extraction_date": datetime.now().isoformat(timespec="seconds"),
        "files_extracted": [
            "page.html",
            "busiest_railway_stations_europe.csv"
        ],
        "raw_folder": str(OUTPUT_DIR),
        "row_count": row_count,
        "columns": columns,
        "import_status": "success"
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(f"[OK] Métadonnées sauvegardées : {METADATA_PATH}")


def scrape_wikipedia_busiest_stations() -> None:
    """
    Lance l'extraction complète de la source Wikipedia.

    Elle télécharge la page, trouve le bon tableau, le nettoie, puis sauvegarde le CSV et les métadonnées.
    """
    print("Début extraction source 4 : scraping Wikipedia")

    html_content = download_html()
    df = find_target_table(html_content)
    df = clean_scraped_dataframe(df)

    save_csv(df)
    save_metadata(row_count=len(df), columns=list(df.columns))

    print("\nExtraction source 4 terminée avec succès.")


if __name__ == "__main__":
    scrape_wikipedia_busiest_stations()
