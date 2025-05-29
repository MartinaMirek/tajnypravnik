import streamlit as st
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload

# Vytvoření credentials z tajemství uloženého v .streamlit/secrets.toml
def get_drive_service():
    service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=credentials)

# Načti metadata souborů z určité složky na Google Disku
def list_files_in_folder(folder_id, page_size=50, next_page_token=None):
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            pageSize=page_size,
            pageToken=next_page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)"
        ).execute()

        files = results.get("files", [])
        next_token = results.get("nextPageToken", None)
        return files, next_token
    except HttpError as error:
        st.error(f"Chyba při načítání souborů: {error}")
        return [], None

# Načti obsah souboru jen při dotazu – lazy loading
def download_file_content(file_id):
    try:
        service = get_drive_service()
        file = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file["mimeType"]
        file_name = file["name"]

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)

        return {
            "name": file_name,
            "mime_type": mime_type,
            "content": fh.read()
        }
    except HttpError as error:
        st.error(f"Chyba při stahování souboru: {error}")
        return None
