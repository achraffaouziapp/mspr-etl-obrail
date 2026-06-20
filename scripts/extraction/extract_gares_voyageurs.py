from pathlib import Path
from datetime import datetime
import json
import requests
import pandas as pd


SOURCE_NAME = "Gares de voyageurs du réseau ferré national"
SOURCE_FORMAT = "CSV"
SOURCE_DESCRIPTION = "Référentiel des gares de voyageurs SNCF avec identifiants, noms, trigrammes et coordonnées géographiques."

# URL principale du CSV
CSV_URLS = [
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/gares-de-voyageurs/exports/csv?use_labels=true",
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/gares-de-voyageurs/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B",
    "https://transport.data.gouv.fr/resources/81691/download"
]

OUTPUT_DIR = Path("data/raw/gares_voyageurs")
CSV_PATH = OUTPUT_DIR / "gares-de-voyageurs.csv"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def download_csv() -> str:
    """
    Télécharge le fichier CSV des gares de voyageurs.
    Le script essaie plusieurs URL pour être plus robuste.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    last_error = None

    for url in CSV_URLS:
        try:
            print(f"Tentative de téléchargement : {url}")

            response = requests.get(url, timeout=120, allow_redirects=True)
            response.raise_for_status()

            content = response.content

            if len(content) < 100:
                raise ValueError("Fichier téléchargé trop petit, probablement invalide.")

            if content[:50].lower().startswith(b"<!doctype") or content[:20].lower().startswith(b"<html"):
                raise ValueError("La réponse semble être une page HTML, pas un CSV.")

            with open(CSV_PATH, "wb") as file:
                file.write(content)

            print(f"[OK] Fichier CSV sauvegardé : {CSV_PATH}")
            return url

        except Exception as error:
            last_error = error
            print(f"[ERREUR] Échec avec cette URL : {error}")

    raise RuntimeError(f"Impossible de télécharger la source. Dernière erreur : {last_error}")


def check_csv_file() -> None:
    """
    Vérifie que le CSV est lisible et affiche un aperçu.
    """
    print("\nVérification du fichier CSV...")

    try:
        df = pd.read_csv(CSV_PATH, sep=None, engine="python", dtype=str, nrows=5)
        print("[OK] CSV lisible")
        print(f"Colonnes détectées : {list(df.columns)}")
        print("\nAperçu :")
        print(df.head())

    except Exception as error:
        print(f"[ATTENTION] Le fichier a été téléchargé, mais la lecture pandas a échoué : {error}")


def save_metadata(source_url_used: str) -> None:
    """
    Sauvegarde les métadonnées de l'extraction.
    """
    metadata = {
        "source_name": SOURCE_NAME,
        "source_url": source_url_used,
        "source_format": SOURCE_FORMAT,
        "source_description": SOURCE_DESCRIPTION,
        "extraction_date": datetime.now().isoformat(timespec="seconds"),
        "files_extracted": [
            "gares-de-voyageurs.csv"
        ],
        "raw_folder": str(OUTPUT_DIR),
        "import_status": "success"
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(f"[OK] Métadonnées sauvegardées : {METADATA_PATH}")


def extract_gares_voyageurs() -> None:
    """
    Fonction principale d'extraction de la source 3.
    """
    print("Début extraction source 3 : Gares de voyageurs")

    source_url_used = download_csv()
    check_csv_file()
    save_metadata(source_url_used)

    print("\nExtraction source 3 terminée avec succès.")


if __name__ == "__main__":
    extract_gares_voyageurs()