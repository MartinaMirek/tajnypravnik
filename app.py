import streamlit as st
from drive_utils import list_files_in_folder, download_file_content

# Nastavení základního rozhraní
st.set_page_config(page_title="Tajný právník BDVH", layout="wide")
st.title("📚 Tajný právník BDVH – AI Asistent")

# ID složky na Google Drive, kterou chceš prohledávat
FOLDER_ID = "1pDXRkcEfFvThAMfxxxxxxxxxxxx"  # ← ZDE vlož reálné ID složky

# Uložení tokenu pro stránkování
if "next_page_token" not in st.session_state:
    st.session_state.next_page_token = None

st.subheader("📂 Dokumenty ve složce")

# Tlačítko pro resetování stránkování
if st.button("🔄 Načíst znovu"):
    st.session_state.next_page_token = None

# Načti seznam souborů
files, next_token = list_files_in_folder(FOLDER_ID, page_size=10, next_page_token=st.session_state.next_page_token)

if files:
    for file in files:
        with st.expander(f"📄 {file['name']} | {file['mimeType']} | {round(int(file.get('size', 0))/1024, 1)} KB"):
            if st.button(f"📥 Načíst obsah souboru: {file['name']}", key=file['id']):
                data = download_file_content(file['id'])
                if data:
                    st.write(f"Soubor: {data['name']} ({data['mime_type']})")
                    if data['mime_type'] == 'application/pdf':
                        st.download_button("📎 Stáhnout PDF", data=data['content'], file_name=data['name'])
                    elif data['mime_type'].startswith("text"):
                        st.text(data['content'].decode('utf-8', errors='ignore'))
                    else:
                        st.success("Obsah načten – neznámý typ, stáhni si ho níže")
                        st.download_button("📎 Stáhnout soubor", data=data['content'], file_name=data['name'])
else:
    st.info("Nenalezeny žádné soubory nebo došlo k chybě.")

# Další stránka
if next_token:
    if st.button("➡️ Další stránka"):
        st.session_state.next_page_token = next_token
else:
    st.write("📍 Konec seznamu souborů.")
