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
    Télécharge le fichier GTFS ZIP de la SNCF.
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
    Décompresse le fichier GTFS ZIP dans data/raw/sncf_gtfs.
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
    Sauvegarde les métadonnées de l'extraction.
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
    Vérifie que les principaux fichiers GTFS sont présents.
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
    Fonction principale d'extraction de la source SNCF GTFS.
    """
    print("Début extraction source 2 : SNCF GTFS")

    download_gtfs_zip()
    extracted_files = unzip_gtfs_file()
    check_expected_files(extracted_files)
    save_metadata(extracted_files)

    print("\nExtraction source 2 terminée avec succès.")


if __name__ == "__main__":
    extract_sncf_gtfs()