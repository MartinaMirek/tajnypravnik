import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def nacist_soubory_z_disku(slozka_id):
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(info)
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(
        q=f"'{slozka_id}' in parents and trashed = false",
        pageSize=100,
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])
