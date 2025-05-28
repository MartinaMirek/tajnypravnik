import os
import json
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build

def build_drive_service():
    # Načti proměnnou prostředí jako string
    json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT")

    if not json_str:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT není nastavena!")

    # Ulož JSON do dočasného souboru
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
        tmp.write(json_str)
        tmp_path = tmp.name

    # Vytvoř přihlašovací údaje
    creds = service_account.Credentials.from_service_account_file(tmp_path)
    service = build("drive", "v3", credentials=creds)
    return service

def nacist_soubory_z_disku(slozka_id):
    service = build_drive_service()
    results = service.files().list(
        q=f"'{slozka_id}' in parents and trashed = false",
        pageSize=100,
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])

def nacist_soubory_z_podlozek(root_folder_id):
    service = build_drive_service()
    folders = nacist_soubory_z_disku(root_folder_id)
    all_files = []
    for folder in folders:
        files = nacist_soubory_z_disku(folder["id"])
        all_files.extend(files)
    return all_files
