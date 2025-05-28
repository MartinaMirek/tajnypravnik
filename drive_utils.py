import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def build_drive_service():
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(info)
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

def nacist_soubory_z_podslozek(root_folder_id):
    service = build_drive_service()
    
    def list_all_files(folder_id):
        files = []
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)"
        ).execute()
        items = results.get("files", [])
        for item in items:
            if item["mimeType"] == "application/vnd.google-apps.folder":
                files.extend(list_all_files(item["id"]))  # Rekurze pro podsložku
            else:
                files.append(item)
        return files

    return list_all_files(root_folder_id)
