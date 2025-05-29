import os
import io
import re
import json
import tempfile
import streamlit as st

# Google API klient pro přístup k Disku
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Knihovny pro práci se soubory různého typu
import fitz  # PyMuPDF, pro PDF
from docx import Document
from PIL import Image
import pytesseract
import pandas as pd

# Nastavení základních parametrů
st.set_page_config(page_title="Tajný právník BDVH", layout="wide")
st.title("🕵️ Tajný právník BDVH – AI právní asistent")

# --- Autentifikace pomocí proměnné prostředí GOOGLE_SERVICE_ACCOUNT (TOML)
json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
if not json_str:
    st.error("Chybí přihlašovací údaje. Zkontrolujte proměnnou GOOGLE_SERVICE_ACCOUNT ve Streamlit Secrets.")
    st.stop()

with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
    tmp.write(json_str)
    tmp_path = tmp.name

credentials = service_account.Credentials.from_service_account_file(
    tmp_path,
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive_service = build('drive', 'v3', credentials=credentials)

# --- ID složek
BDVH_FOLDER_ID = "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3"
MM_FOLDER_ID = "1g5LAaJcBOsOUQMD4L1hftuAiyBUZwxRJ"
LEGAL_LIBRARY_ID = "1GWu-tggeKtjFz2BTMQKEpLP7naMKxBBC"

# --- Funkce pro rekurzivní načtení souborů
def fetch_folder_files(folder_id, label="main"):
    files_data = []
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        response = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        for f in response.get('files', []):
            if f.get('mimeType') == 'application/vnd.google-apps.folder':
                sub_label = "legal" if f['id'] == LEGAL_LIBRARY_ID or label == "legal" else label
                files_data.extend(fetch_folder_files(f['id'], label=sub_label))
            elif f.get('mimeType') != 'application/vnd.google-apps.shortcut':
                files_data.append({
                    "id": f['id'],
                    "name": f['name'],
                    "mimeType": f.get('mimeType', ''),
                    "label": label
                })
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return files_data

# --- Načti všechny dokumenty
@st.cache_data(show_spinner=False)
def load_all_documents():
    all_files = fetch_folder_files(BDVH_FOLDER_ID, label="main") + fetch_folder_files(MM_FOLDER_ID, label="main")
    documents = []
    for file in all_files:
        file_id = file['id']
        name = file['name']
        mime = file['mimeType']
        try:
            if mime.startswith('application/vnd.google-apps'):
                if mime == 'application/vnd.google-apps.document':
                    content = drive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
                    content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
                elif mime == 'application/vnd.google-apps.spreadsheet':
                    content_bytes = drive_service.files().export(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet').execute()
                else:
                    continue
            else:
                request = drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fd=fh, request=request)
                while True:
                    _, done = downloader.next_chunk()
                    if done:
                        break
                content_bytes = fh.getvalue()
        except Exception as e:
            print(f"Chyba při stahování {name}: {e}")
            continue

        # --- Zpracování souboru
        text = ""
        try:
            if name.lower().endswith('.pdf') or mime == 'application/pdf':
                doc = fitz.open(stream=content_bytes, filetype="pdf")
                for page in doc:
                    t = page.get_text().strip()
                    if t:
                        text += t + "\n"
                    else:
                        img = Image.open(io.BytesIO(page.get_pixmap(dpi=150).tobytes()))
                        text += pytesseract.image_to_string(img, lang="ces") + "\n"
                doc.close()
            elif name.lower().endswith('.docx'):
                doc = Document(io.BytesIO(content_bytes))
                text = "\n".join([para.text for para in doc.paragraphs])
            elif name.lower().endswith('.doc'):
                text = content_bytes.decode('utf-8', errors='ignore')
            elif mime.startswith('text/') or name.lower().endswith('.txt'):
                try:
                    text = content_bytes.decode('utf-8')
                except:
                    text = content_bytes.decode('latin-1', errors='ignore')
            elif mime.startswith('image/') or name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(io.BytesIO(content_bytes))
                text = pytesseract.image_to_string(img, lang="ces")
            elif name.lower().endswith(('.xls', '.xlsx')):
                xls = pd.ExcelFile(io.BytesIO(content_bytes))
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    text += df.to_csv(index=False)
            else:
                text = content_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            text = ""
        documents.append({"name": name, "text": text, "label": file['label']})
    return documents

# --- Načti dokumenty
with st.spinner("🔄 Načítám dokumenty z Google Disku..."):
    docs = load_all_documents()
if not docs:
    st.warning("⚠️ Nepodařilo se načíst žádné dokumenty. Zkontrolujte oprávnění a konfiguraci.")
else:
    st.success(f"✅ Načteno {len(docs)} dokumentů. Můžete se zeptat na cokoliv.")

# --- Dotaz uživatele
query = st.text_input("🔎 Zadejte svůj právní dotaz:", "")
if query:
    legal_keywords = ["judikát", "zákon", "rozbor", "paragraf", "ustanovení", "nález"]
    legal_query = any(kw in query.lower() for kw in legal_keywords)

    relevant_docs = []
    for doc in docs:
        if legal_query and doc['label'] != "legal":
            continue
        score = sum(1 for word in re.findall(r"\w{3,}", query.lower()) if word in doc['text'].lower())
        if score > 0:
            relevant_docs.append((score, doc))

    relevant_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [d for _, d in relevant_docs[:3]]

    context = ""
    for d in top_docs:
        snippet = d['text']
        if len(snippet) > 2000:
            snippet = snippet[:1500] + "\n...\n" + snippet[-500:]
        context += f"### Dokument: {d['name']}\n{snippet}\n\n"

    messages = [
        {"role": "system", "content": f"Jsi AI právník. Máš k dispozici dokumenty:\n{context}\nOdpověz na dotaz česky, srozumitelně a věcně."},
        {"role": "user", "content": query}
    ]

    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", None))
        response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
        answer = response["choices"][0]["message"]["content"].strip()
        st.markdown("**Odpověď AI:**\n\n" + answer)
    except Exception as e:
        st.error(f"Nastala chyba při volání OpenAI: {e}")
