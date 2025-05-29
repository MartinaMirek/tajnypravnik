import streamlit as st
import openai
import tempfile
from drive_utils import list_files_in_folder, download_file_content
import fitz  # PyMuPDF
import docx2txt
import pytesseract
from PIL import Image
import io
import datetime

# Nastavení klíče OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Nastavení základního rozhraní
st.set_page_config(page_title="Tajný právník BDVH", layout="wide")
st.title("📚 Tajný právník BDVH – AI Asistent")

# Výběr složky
folders = {
    "BDVH – spory a dokumenty": "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3",
    "15 – Právní knihovna": "1g5LAaJcBOsOUQMD4L1hftuAiyBUZwxRJ",
    "Moje důkazy (AI označené)": "1GtvnJgAFTknYgUd_ERYLootGdWB8ey9"
}

folder_label = st.selectbox("Vyber složku:", list(folders.keys()))
FOLDER_ID = folders[folder_label]

if "next_page_token" not in st.session_state:
    st.session_state.next_page_token = None
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

st.subheader("📂 Dokumenty ve složce")

if st.button("🔄 Načíst znovu"):
    st.session_state.next_page_token = None
    st.session_state.selected_file = None

files, next_token = list_files_in_folder(FOLDER_ID, page_size=10, next_page_token=st.session_state.next_page_token)

if files:
    for file in files:
        st.markdown(f"**📄 {file['name']}** – {file['mimeType']} – {round(int(file.get('size', 0))/1024, 1)} KB")
        if st.button(f"🔍 Otevřít: {file['name']}", key=file['id']):
            st.session_state.selected_file = file['id']
else:
    st.info("Nenalezeny žádné soubory nebo došlo k chybě.")

if next_token:
    if st.button("➡️ Další stránka"):
        st.session_state.next_page_token = next_token
else:
    st.write("📍 Konec seznamu souborů.")

# Funkce na extrakci textu

def extract_text_from_file(data):
    mime = data['mime_type']
    content = data['content']
    if mime == 'application/pdf':
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            with fitz.open(tmp.name) as doc:
                text = "\n".join([page.get_text() for page in doc])
        return text
    elif mime in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(content)
            tmp.flush()
            return docx2txt.process(tmp.name)
    elif mime.startswith("image/"):
        image = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(image)
    elif mime.startswith("text"):
        return content.decode('utf-8', errors='ignore')
    else:
        return "Nepodporovaný formát souboru pro čtení textu."

if st.session_state.selected_file:
    data = download_file_content(st.session_state.selected_file)
    if data:
        st.subheader(f"📘 Obsah: {data['name']}")
        extracted_text = extract_text_from_file(data)
        st.text_area("📄 Extrahovaný text:", extracted_text[:3000], height=200)

        st.subheader("💬 Zeptej se na cokoliv k tomuto dokumentu")
        user_question = st.text_input("Tvoje otázka")

        if user_question:
            with st.spinner("Přemýšlím jako právník…"):
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Jsi právník specializovaný na české právo. Odpovídej stručně, přesně a věcně."},
                        {"role": "user", "content": f"Tady je obsah dokumentu: {extracted_text[:7000]}"},
                        {"role": "user", "content": f"Otázka: {user_question}"}
                    ]
                )
                answer = response.choices[0].message.content
                st.markdown(f"**🧠 Odpověď AI:**\n{answer}")

        st.subheader("🧠 AI návrh důkazů a poznámek")
        if st.button("🔎 Najdi podezřelé věty"):
            suspect_prompt = f"Zde je text dokumentu. Najdi a vypiš 5 vět, které mohou být důkazem nebo obsahují problémové či klíčové tvrzení v právním sporu.\n{textwrap.shorten(extracted_text, 7000)}"
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Analyzuj právní dokumenty. Vyber právně významné věty."},
                    {"role": "user", "content": suspect_prompt}
                ]
            )
            suspect_lines = response.choices[0].message.content.split("\n")

            for line in suspect_lines:
                if line.strip():
                    st.markdown(f"🔸 {line.strip()}")
                    if st.button("📌 Uložit jako důkaz", key=line):
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
                        filename = f"DUKAZ_{timestamp}_{data['name'].replace(' ', '_')}.txt"
                        content = f"Zdroj: {data['name']}\nVěta: {line.strip()}\nDatum: {timestamp}"
                        with open(f"/mnt/data/{filename}", "w", encoding="utf-8") as f:
                            f.write(content)
                        st.success(f"💾 Důkaz uložen: {filename}")
                        # TODO: Nahraj do Google Drive do složky "Moje důkazy"
else:
    st.info("Vyber nejprve soubor, který chceš analyzovat.")
