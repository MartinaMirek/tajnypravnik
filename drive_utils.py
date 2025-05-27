
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]
credentials_path = "credentials.json"

def authenticate():
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds

def nacist_soubory_z_disku(slozka_id):
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(
        q=f"'{slozka_id}' in parents and trashed = false",
        pageSize=100,
        fields="files(id, name)"
    ).execute()
    return results.get("files", [])
