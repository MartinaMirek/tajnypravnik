import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def initialize_drive(credentials):
    return build('drive', 'v3', credentials=credentials)

def list_files_lazy(drive_service, folder_id, label="main", page_size=100):
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        response = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size, createdTime)',
            pageSize=page_size,
            pageToken=page_token
        ).execute()
        for file in response.get('files', []):
            yield {
                'id': file['id'],
                'name': file['name'],
                'mimeType': file.get('mimeType', ''),
                'size': file.get('size'),
                'createdTime': file.get('createdTime'),
                'label': label
            }
        page_token = response.get('nextPageToken')
        if not page_token:
            break

def fetch_file_content(drive_service, file_id, mime_type):
    try:
        if mime_type.startswith('application/vnd.google-apps'):
            if mime_type == 'application/vnd.google-apps.document':
                content = drive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
                return content.decode('utf-8') if isinstance(content, bytes) else content
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                return drive_service.files().export(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ).execute()
        else:
            request = drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return fh.getvalue()
    except Exception as e:
        print(f"Chyba při načítání obsahu souboru {file_id}: {e}")
        return None
