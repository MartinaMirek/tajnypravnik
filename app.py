import os
import io
import re
import streamlit as st

# Google API klient pro přístup k Disku
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Knihovny pro práci se soubory různého typu
import fitz  # PyMuPDF, pro PDF
from docx import Document  # python-docx, pro .docx soubory
from PIL import Image  # Pillow, pro otevírání obrázků
import pytesseract  # OCR knihovna pro obrazové soubory
import pandas as pd  # pro Excel soubory (tabulky)
# Ujistěte se, že máte nainstalovaný i openpyxl a xlrd pro podporu .xlsx a .xls

# Nastavení základních parametrů
st.set_page_config(page_title="Tajný právník BDVH", layout="wide")
st.title("🕵️ Tajný právník BDVH – AI právní asistent")

# Načtení přihlašovacích údajů ke Google API (service account)
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
if not os.path.isfile(SERVICE_ACCOUNT_FILE):
    st.error("Service account credentials not found! Nahrajte prosím JSON s přihlašovacími údaji.")
    st.stop()
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)
# Inicializace Google Drive API klienta
drive_service = build('drive', 'v3', credentials=credentials)

# ID složek na Google Disku (hlavní složka BDVH a složka Martina & Mirek AI)
BDVH_FOLDER_ID = "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3"
MM_FOLDER_ID = "1g5LAaJcBOsOUQMD4L1hftuAiyBUZwxRJ"
LEGAL_LIBRARY_ID = "1GWu-tggeKtjFz2BTMQKEpLP7naMKxBBC"  # podsložka "Právní knihovna"

def fetch_folder_files(folder_id, label="main"):
    """Rekurzivně projde složku na Drive a vrátí seznam souborů (mimo podsložek) s označením label."""
    files_data = []
    query = f"'{folder_id}' in parents and trashed=false"
    # Získání seznamu souborů v aktuální složce (stránkovaně pro případ většího množství)
    page_token = None
    while True:
        response = drive_service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)",
                                              pageSize=1000, pageToken=page_token).execute()
        files = response.get('files', [])
        for f in files:
            # Pokud je položka složka, rekurzivně projdi její obsah
            if f.get('mimeType') == 'application/vnd.google-apps.folder':
                # Určení labelu pro podsložky: pokud je to právní knihovna nebo již uvnitř ní, použij "legal"
                sub_label = label
                if f['id'] == LEGAL_LIBRARY_ID or label == "legal":
                    sub_label = "legal"
                # Rekurzivní získání souborů z této podsložky
                files_data.extend(fetch_folder_files(f['id'], label=sub_label))
            else:
                # Přeskoč případné zástupce/shortcuts (nebo je lze řešit zvlášť)
                if f.get('mimeType') == 'application/vnd.google-apps.shortcut':
                    continue
                # Uložení informací o souboru (obsah se načte později)
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

@st.cache_data(show_spinner=False)
def load_all_documents():
    """Načte všechny dokumenty z definovaných složek, vrátí list s obsahem a metadaty."""
    # Získání všech souborů (mimo složek) z hlavní složky a složky M&M AI
    all_files = []
    all_files.extend(fetch_folder_files(BDVH_FOLDER_ID, label="main"))
    all_files.extend(fetch_folder_files(MM_FOLDER_ID, label="main"))
    # (Pozn.: soubory ve složce Právní knihovna uvnitř M&M AI budou označeny label "legal" díky výše uvedené logice.)
    documents = []
    for file in all_files:
        file_id = file['id']
        name = file['name']
        mime = file['mimeType']
        # Stažení obsahu souboru z Drive
        try:
            if mime.startswith('application/vnd.google-apps'):
                # Google Docs, Sheets apod. - je třeba exportovat
                if mime == 'application/vnd.google-apps.document':
                    # Export Google Doc do textu
                    content = drive_service.files().export(fileId=file_id, mimeType='text/plain').execute()
                    content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
                elif mime == 'application/vnd.google-apps.spreadsheet':
                    # Export Google Sheet do Excel (.xlsx)
                    content_bytes = drive_service.files().export(fileId=file_id,
                                            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                                        ).execute()
                else:
                    # Nezpracovávané typy (Slides atd.) lze případně doplnit
                    continue
            else:
                # Ostatní soubory (PDF, DOCX, atd.) - stáhnout binární obsah
                request = drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fd=fh, request=request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content_bytes = fh.getvalue()
        except Exception as e:
            # Pokud soubor nelze stáhnout (chyba autorizace apod.), přeskoč
            print(f"Chyba při stahování {name}: {e}")
            continue

        # Zpracování obsahu souboru na čitelný text
        text = ""
        try:
            # PDF soubor
            if name.lower().endswith('.pdf') or mime == 'application/pdf':
                doc = fitz.open(stream=content_bytes, filetype="pdf")
                for page in doc:
                    page_text = page.get_text().strip()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        # Pokud stránka nemá text (sken), použij OCR
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.pixels))
                        # Pozn.: Při použití českých dokumentů zajistěte, že Tesseract má nainstalovaný český jazyk 
                        ocr_text = pytesseract.image_to_string(img, lang="ces")
                        text += ocr_text + "\n"
                doc.close()
            # Word dokument (.docx)
            elif name.lower().endswith('.docx') or mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                doc = Document(io.BytesIO(content_bytes))
                full_text = [para.text for para in doc.paragraphs]
                text = "\n".join(full_text)
            # Starý Word .doc (pokud je podporováno, základní podpora – může vyžadovat alternativní přístup)
            elif name.lower().endswith('.doc') or mime == 'application/msword':
                # python-docx nepodporuje .doc, pro jednoduchost pokus o načtení jako text
                try:
                    text = content_bytes.decode('utf-8', errors='ignore')
                except:
                    text = ""
            # Textový soubor .txt
            elif mime.startswith('text/') or name.lower().endswith('.txt'):
                try:
                    text = content_bytes.decode('utf-8')
                except:
                    text = content_bytes.decode('latin-1', errors='ignore')
            # Obrázek (JPG, PNG, atd.)
            elif mime.startswith('image/') or name.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img = Image.open(io.BytesIO(content_bytes))
                    # OCR na obrázku
                    text = pytesseract.image_to_string(img, lang="ces")
                except Exception as e:
                    text = ""
            # Excel soubor (.xls, .xlsx)
            elif name.lower().endswith(('.xls', '.xlsx')) or mime in ['application/vnd.ms-excel',
                                                                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                try:
                    # Načti všechny listy Excelu a konvertuj do CSV textu
                    xls = pd.ExcelFile(io.BytesIO(content_bytes))
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        text += df.to_csv(index=False)
                except Exception as e:
                    text = ""
            else:
                # Ostatní typy (pokud jsou nějaké nezpracované) - pokus o dekódování jako text
                try:
                    text = content_bytes.decode('utf-8', errors='ignore')
                except:
                    text = str(content_bytes)
        except Exception as e:
            text = ""
        # Ulož text dokumentu spolu s názvem a štítkem (main/legal)
        documents.append({
            "name": name,
            "text": text,
            "label": file['label']
        })
    return documents

# Načti dokumenty (s cache – provede se jen jednou a pak při dalším běhu načte z paměti)
with st.spinner("Načítám dokumenty z Google Disku..."):
    docs = load_all_documents()
if not docs:
    st.warning("Nepodařilo se načíst žádné dokumenty. Zkontrolujte konfiguraci.")
else:
    st.success(f"Načteno {len(docs)} dokumentů. Můžete zadat dotaz.")

# Uživatelské rozhraní pro zadání dotazu
query = st.text_input("🔎 Zadejte svůj právní dotaz:", "")
if query:
    # Urči, zda dotaz spadá do právní oblasti (klíčová slova)
    legal_query = False
    legal_keywords = ["judikát", "zákon", "rozbor", "paragraf", "ustanovení", "nález"]
    q_lower = query.lower()
    for kw in legal_keywords:
        if kw in q_lower:
            legal_query = True
            break
    # Vyber dokumenty relevantní pro dotaz
    relevant_docs = []
    for doc in docs:
        # Pokud dotaz je právní a dokument není z právní knihovny, můžeme méně preferovat (zde filtrujeme přísně)
        if legal_query and doc['label'] != "legal":
            continue
        # Jednoduché fulltextové hledání klíčových slov dotazu v textu dokumentu
        # Rozdělíme dotaz na slova a zjistíme, kolikrát se v dokumentu vyskytují
        score = 0
        for word in re.findall(r"\w{3,}", q_lower):
            if word in doc['text'].lower():
                score += 1
        # Pokud alespoň jedno shodné klíčové slovo, vezmeme dokument v potaz
        if score > 0:
            relevant_docs.append((score, doc))
    # Seřaď nalezené dokumenty podle skóre (počtu shod) sestupně
    relevant_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [d for _, d in relevant_docs[:3]]  # vezmeme maximálně 3 nejrelevantnější dokumenty

    # Sestav kontext z dokumentů
    context_text = ""
    for d in top_docs:
        # Zkrácení textu dokumentu pro vložení do promptu (pokud je velmi dlouhý)
        doc_text = d['text']
        if len(doc_text) > 2000:
            doc_text = doc_text[:1500] + "\n...\n" + doc_text[-500:]
        context_text += f"### Dokument: {d['name']}\n{doc_text}\n\n"
    if context_text:
        system_prompt = (
            "Jsi právní AI asistent a máš k dispozici následující informace z interních dokumentů BDVH:\n"
            + context_text +
            "Použij tyto informace (a své obecné znalosti) k zodpovězení dotazu uživatele. "
            "Odpověz česky a co nejvěcněji.\n"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    else:
        # Pokud nemáme žádné kontextové info, prostě předáme dotaz rovnou
        messages = [
            {"role": "system", "content": "Jsi právní AI asistent, odpovídáš na dotazy uživatele na základě své znalosti."},
            {"role": "user", "content": query}
        ]
    # Zavolej OpenAI API pro dokončení
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY", None))
        response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    except Exception as e:
        # Pokud nastala chyba (např. neexistující model, nedostupnost), zkus fallback na GPT-3.5
        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        except Exception as e2:
            st.error(f"Nastala chyba při volání OpenAI API: {e2}")
            st.stop()
    # Získání textu odpovědi
    answer = response["choices"][0]["message"]["content"].strip()
    # Zobrazení odpovědi
    st.markdown("**Odpověď AI:**\n\n" + answer)
