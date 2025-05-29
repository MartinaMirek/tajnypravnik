import streamlit as st
import json
from google.oauth2 import service_account
from drive_utils import initialize_drive, list_files_lazy, fetch_file_content

st.set_page_config(page_title="Tajný právník BDVH", layout="wide")

st.title("📂 Tajný právník BDVH – Dokumenty z Google Disku")

# Načtení přihlašovacích údajů
service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
credentials = service_account.Credentials.from_service_account_info(service_account_info)

# Inicializace služby
drive_service = initialize_drive(credentials)

# Definice ID složek
FOLDERS = {
    "📁 BDVH – Soudní dokumenty": "1pDXRkcEfFvThAMfWZfz9I4VP1MCOqHcp",
    "📚 Právní knihovna": "1GWu-tggeKtjFz2BTMQKEpLP7naMKxBBC"
}

folder_choice = st.selectbox("Vyber složku", list(FOLDERS.keys()))
folder_id = FOLDERS[folder_choice]

st.markdown("---")
st.subheader("📄 Seznam souborů")

# Parametry pro stránkování
PAGE_SIZE = 10
page_number = st.number_input("Stránka", min_value=1, step=1, value=1)

# Lazy načtení souborů (jen metadata)
files = list(list_files_lazy(drive_service, folder_id))
total_pages = (len(files) + PAGE_SIZE - 1) // PAGE_SIZE
start_idx = (page_number - 1) * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE
paged_files = files[start_idx:end_idx]

# Zobrazení souborů
for file in paged_files:
    with st.expander(f"📎 {file['name']}"):
        st.markdown(f"**Typ:** {file['mimeType']}")
        st.markdown(f"**Velikost:** {file['size']} B")
        st.markdown(f"**Vytvořeno:** {file['createdTime']}")
        if st.button(f"📥 Načíst obsah", key=file['id']):
            content = fetch_file_content(drive_service, file['id'], file['mimeType'])
            if isinstance(content, bytes):
                st.download_button("📥 Stáhnout soubor", content, file_name=file['name'])
            elif isinstance(content, str):
                st.text_area("📃 Obsah souboru", content, height=300)
            else:
                st.warning("Soubor nelze zobrazit.")

st.markdown("---")
st.caption("🔒 Jen pro interní účely Betynka Community / Martina & Mirek AI")
