"""
Extrait les données Back-on-Track sur les trains de nuit européens.

Les fichiers JSON téléchargés sont conservés en brut dans data/raw/back_on_track afin
que la transformation puisse ensuite créer les trajets night dans le modèle relationnel.
"""

from pathlib import Path
from datetime import datetime
import json
import requests


BASE_URL = "https://raw.githubusercontent.com/Back-on-Track-eu/night-train-data/main/data/latest"

FILES_TO_EXTRACT = [
    "agencies.json",
    "stops.json",
    "routes.json",
    "trips.json",
    "trip_stop.json",
    "calendar.json",
    "calendar_dates.json",
    "classes.json",
]

OUTPUT_DIR = Path("data/raw/back_on_track")


def download_json_file(file_name: str) -> dict | list:
    """
    Télécharge un fichier JSON précis depuis le dépôt Back-on-Track.

    La fonction retourne directement le contenu JSON pour qu'il puisse être sauvegardé sans modification.
    """
    url = f"{BASE_URL}/{file_name}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def save_raw_json(data: dict | list, file_name: str) -> None:
    """
    Sauvegarde un fichier JSON brut dans le dossier Back-on-Track.

    Les données sont conservées telles qu'elles viennent de la source pour garder la traçabilité.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / file_name

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"[OK] Fichier sauvegardé : {output_path}")


def save_metadata(extracted_files: list[str]) -> None:
    """
    Écrit un fichier metadata.json décrivant l'extraction.

    Les métadonnées permettent de savoir quelle source a été utilisée, quand elle a été
    extraite et quels fichiers bruts ont été produits.
    """
    metadata = {
        "source_name": "Back-on-Track Night Train Data",
        "source_url": "https://github.com/Back-on-Track-eu/night-train-data",
        "source_format": "JSON",
        "extraction_date": datetime.now().isoformat(timespec="seconds"),
        "files_extracted": extracted_files,
        "import_status": "success",
    }

    output_path = OUTPUT_DIR / "metadata.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(f"[OK] Métadonnées sauvegardées : {output_path}")


def extract_back_on_track() -> None:
    """
    Lance le téléchargement de tous les fichiers Back-on-Track nécessaires au projet.

    Chaque fichier est traité séparément afin que l'extraction continue même si une ressource échoue.
    """
    print("Début de l'extraction Back-on-Track...")

    extracted_files = []

    for file_name in FILES_TO_EXTRACT:
        try:
            print(f"Téléchargement de {file_name}...")
            data = download_json_file(file_name)
            save_raw_json(data, file_name)
            extracted_files.append(file_name)

        except requests.exceptions.RequestException as error:
            print(f"[ERREUR] Impossible de télécharger {file_name} : {error}")

        except json.JSONDecodeError as error:
            print(f"[ERREUR] JSON invalide pour {file_name} : {error}")

    save_metadata(extracted_files)

    print("Extraction terminée.")


if __name__ == "__main__":
    extract_back_on_track()
