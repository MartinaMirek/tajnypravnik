import streamlit as st
import os
import io
import json
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import openai
from docx import Document
import tempfile

# ============================
# 1. Načti API klíče a přihlašovací údaje
# ============================

service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
credentials = service_account.Credentials.from_service_account_info(service_account_info)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ============================
# 2. Připoj se ke Google Drive API
# ============================

drive_service = build("drive", "v3", credentials=credentials)

# ============================
# 3. Funkce pro stažení obsahu souboru z Google Disku
# ============================

def stahni_obsah_souboru(file_id, mime_type):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)

    if mime_type == "application/pdf":
        text = ""
        doc = fitz.open(stream=fh.read(), filetype="pdf")
        for page in doc:
            text += page.get_text()
        return text

    elif mime_type.startswith("image/"):
        image = Image.open(fh)
        return pytesseract.image_to_string(image)

    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(fh.read())
            tmp_path = tmp.name
        doc = Document(tmp_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text

    elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(fh, engine="openpyxl")
        return df.to_string(index=False)

    elif mime_type == "application/vnd.ms-excel":
        df = pd.read_excel(fh, engine="xlrd")
        return df.to_string(index=False)

    else:
        return "Nepodporovaný formát souboru."

# ============================
# 4. Funkce pro zodpovězení dotazu pomocí OpenAI
# ============================

def odpovez_na_dotaz(dotaz, kontext):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jsi právní asistent. Odpovídej výstižně a věcně."},
                {"role": "user", "content": f"Na základě tohoto textu odpověz na dotaz: {dotaz}\n\nText:\n{kontext}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Došlo k chybě při dotazu na OpenAI: {e}"

# ============================
# 5. Uživatelské rozhraní
# ============================

st.title("⚖️ Tajný právník – Právní dokumenty z Disku a odpovědi GPT")

file_id = st.text_input("Zadej ID souboru z Google Disku:")
dotaz = st.text_area("Zadej právní dotaz k obsahu souboru:")

if st.button("🔍 Získat odpověď"):
    if file_id and dotaz:
        file_metadata = drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        mime_type = file_metadata["mimeType"]
        nazev = file_metadata["name"]
        with st.spinner(f"Stahuji a zpracovávám soubor: {nazev}..."):
            obsah = stahni_obsah_souboru(file_id, mime_type)
            odpoved = odpovez_na_dotaz(dotaz, obsah)
        st.subheader("📄 Výstup GPT:")
        st.write(odpoved)
    else:
        st.warning("Zadej prosím ID souboru a dotaz.")
