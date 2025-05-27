import streamlit as st
from drive_utils import nacist_soubory_z_disku

st.set_page_config(page_title="Tajný právník BDVH", page_icon="🧑‍⚖️")

st.title("🧑‍⚖️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# 🟡 Sem zadej správné ID složky z Google Drive
slozka_id = "1g5LAaJcBOsOUQMD4L1hftuAiyBUZwxRJ"

# 💬 Vstupní pole pro otázky (zatím neaktivní)
user_input = st.chat_input("Zeptej se AI...")

if user_input:
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write("🧠 Promiň, zatím nejsem napojen na AI odpovídání – ale dokumenty ti načtu!")

# 📂 Tlačítko pro načtení dokumentů z Google Disku
if st.button("📂 Načíst dokumenty z disku"):
    try:
        dokumenty = nacist_soubory_z_disku(slozka_id)
        st.success(f"Načteno {len(dokumenty)} dokumentů:")
        for doc in dokumenty:
            st.write(f"📄 {doc['name']}")
    except Exception as e:
        st.error(f"Nepodařilo se načíst dokumenty: {e}")
