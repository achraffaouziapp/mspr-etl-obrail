"""
Extrait les horaires théoriques SNCF au format GTFS.

Le fichier source est un ZIP contenant plusieurs fichiers texte GTFS. Ce script le
télécharge, le décompresse dans data/raw/sncf_gtfs et garde la liste des fichiers extraits.
"""

from pathlib import Path
from datetime import datetime
import json
import zipfile
import requests


GTFS_URL = "https://eu.ftp.opendatasoft.com/sncf/plandata/Export_OpenData_SNCF_GTFS_NewTripId.zip"

SOURCE_NAME = "Réseau SNCF TGV, Intercités et TER"
SOURCE_FORMAT = "GTFS ZIP"
SOURCE_DESCRIPTION = "Horaires théoriques SNCF TGV, Intercités et TER au format GTFS"

OUTPUT_DIR = Path("data/raw/sncf_gtfs")
ZIP_PATH = OUTPUT_DIR / "sncf_gtfs.zip"


def download_gtfs_zip() -> None:
    """
    Télécharge le ZIP GTFS de la SNCF et le sauvegarde dans le dossier raw.

    Le ZIP est conservé pour garder une copie brute de la source avant décompression.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Téléchargement de la source GTFS SNCF...")
    print(f"URL : {GTFS_URL}")

    response = requests.get(GTFS_URL, timeout=120)
    response.raise_for_status()

    with open(ZIP_PATH, "wb") as file:
        file.write(response.content)

    print(f"[OK] Fichier ZIP sauvegardé : {ZIP_PATH}")


def unzip_gtfs_file() -> list[str]:
    """
    Décompresse le fichier GTFS dans le dossier data/raw/sncf_gtfs.

    La fonction retourne la liste des fichiers extraits afin de pouvoir vérifier leur présence
    et les inscrire dans les métadonnées.
    """
    extracted_files = []

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(OUTPUT_DIR)
        extracted_files = zip_ref.namelist()

    print("[OK] Fichier GTFS décompressé")

    for file_name in extracted_files:
        print(f" - {file_name}")

    return extracted_files


def save_metadata(extracted_files: list[str]) -> None:
    """
    Écrit un fichier metadata.json décrivant l'extraction.

    Les métadonnées permettent de savoir quelle source a été utilisée, quand elle a été
    extraite et quels fichiers bruts ont été produits.
    """
    metadata = {
        "source_name": SOURCE_NAME,
        "source_url": GTFS_URL,
        "source_format": SOURCE_FORMAT,
        "source_description": SOURCE_DESCRIPTION,
        "extraction_date": datetime.now().isoformat(timespec="seconds"),
        "files_extracted": extracted_files,
        "raw_folder": str(OUTPUT_DIR),
        "import_status": "success"
    }

    metadata_path = OUTPUT_DIR / "metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(f"[OK] Métadonnées sauvegardées : {metadata_path}")


def check_expected_files(extracted_files: list[str]) -> None:
    """
    Vérifie la présence des fichiers GTFS principaux.

    Certains fichiers comme calendar.txt peuvent être absents selon l'export. Le script signale
    l'absence sans bloquer automatiquement l'extraction.
    """
    expected_files = [
        "agency.txt",
        "stops.txt",
        "routes.txt",
        "trips.txt",
        "stop_times.txt",
        "calendar.txt",
        "calendar_dates.txt"
    ]

    print("\nVérification des fichiers GTFS attendus :")

    for file_name in expected_files:
        if file_name in extracted_files:
            print(f"[OK] {file_name}")
        else:
            print(f"[ATTENTION] {file_name} absent")


def extract_sncf_gtfs() -> None:
    """
    Lance l'extraction complète de la source GTFS SNCF.

    Elle télécharge le ZIP, le décompresse, vérifie les fichiers attendus et écrit les métadonnées.
    """
    print("Début extraction source 2 : SNCF GTFS")

    download_gtfs_zip()
    extracted_files = unzip_gtfs_file()
    check_expected_files(extracted_files)
    save_metadata(extracted_files)

    print("\nExtraction source 2 terminée avec succès.")


if __name__ == "__main__":
    extract_sncf_gtfs()
