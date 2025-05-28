import streamlit as st
from drive_utils import nacist_soubory_z_disku
import openai

st.set_page_config(page_title="Tajný právník BDVH", page_icon="🧑‍⚖️")

st.title("🧑‍⚖️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# Google Drive složka
slozka_id = "1g5LAaJcBOsOUQMD4L1hftuAiyBUZwxRJ"

if st.button("📂 Načíst dokumenty z disku"):
    dokumenty = nacist_soubory_z_disku(slozka_id)
    st.success(f"Načteno {len(dokumenty)} dokumentů.")
    for doc in dokumenty:
        st.write(doc["name"])

# Otázky na AI
otazka = st.text_input("Zeptej se AI...")
if otazka:
    OPENAI_API_KEY = "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"

    odpoved = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi právník, který analyzuje dokumenty BDVH."},
            {"role": "user", "content": otazka}
        ]
    )
    st.write("🧠 Odpověď AI:")
    st.write(odpoved["choices"][0]["message"]["content"])
