import streamlit as st
from openai import OpenAI
from drive_utils import nacist_soubory_z_podslozek

st.set_page_config(page_title="Tajný právník BDVH", page_icon="🕵️")

st.title("🕵️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# Google Drive složka (načte všechny podsložky)
slozka_id = "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3"

if st.button("📁 Načíst dokumenty z disku"):
    dokumenty = nacist_soubory_z_podslozek(slozka_id)
    st.success(f"Načteno {len(dokumenty)} dokumentů.")
    for doc in dokumenty:
        st.write(doc["name"])

# Otázky na AI
st.markdown("---")
otazka = st.text_input("Zeptej se AI...")

if otazka:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    odpoved = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH."},
            {"role": "user", "content": otazka}
        ]
    )
    st.markdown("**Odpověď AI:**")
    st.write(odpoved.choices[0].message.content)
