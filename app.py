import streamlit as st
import openai
from drive_utils import nacist_soubory_z_podslozek

# Konfigurace stránky
st.set_page_config(page_title="Tajný právník BDVH", page_icon="🕵️")

# Titulek a úvodní text
st.title("🕵️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# ID hlavní složky (načítá i podsložky)
slozka_id = "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3"

# Tlačítko pro načtení dokumentů
if st.button("📁 Načíst dokumenty z disku"):
    dokumenty = nacist_soubory_z_podslozek(slozka_id)
    st.success(f"Načteno {len(dokumenty)} dokumentů.")
    for doc in dokumenty:
        st.write(doc["name"])

# Pole pro dotazy na AI
st.markdown("---")
otazka = st.text_input("Zeptej se AI...")

if otazka:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    try:
        odpoved = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH."},
                {"role": "user", "content": otazka}
            ]
        )
        st.markdown("**Odpověď AI:**")
        st.write(odpoved.choices[0].message["content"])

    except openai.error.OpenAIError as e:
        st.error(f"Nastala chyba při volání OpenAI API: {e}")
