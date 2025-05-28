# tajnypravnik/app.py

import streamlit as st
from openai import OpenAI
from drive_utils import nacist_soubory_z_podslozek
import fitz  # PyMuPDF
import pdfplumber
import docx
import pytesseract
from PIL import Image
import os

# -------------------------------
# FUNKCE NA ZÍSKÁNÍ OBSAHU DOKUMENTŮ
# -------------------------------
def ziskej_obsah_souboru(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                return "\n".join([page.extract_text() or "" for page in pdf.pages])
        elif ext == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in [".jpg", ".jpeg", ".png"]:
            return pytesseract.image_to_string(Image.open(file_path))
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return "Nepodporovaný formát souboru: " + file_path
    except Exception as e:
        return f"Chyba při čtení souboru {file_path}: {e}"


# -------------------------------
# AI ODPOVĚĎ
# -------------------------------
def ziskej_odpoved(otazka: str):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    try:
        return client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH a má přístup k dokumentům z Google Disku. Pokud dotaz obsahuje 'judikát', 'zákon', 'analýza', přizvi na pomoc experta přes OpenAI API."},
                {"role": "user", "content": otazka},
            ]
        ).choices[0].message.content
    except Exception as e:
        print("Fallback na GPT-3.5:", e)
        return client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH a má přístup k dokumentům z Google Disku."},
                {"role": "user", "content": otazka},
            ]
        ).choices[0].message.content


# -------------------------------
# STRÁNKA STREAMLIT
# -------------------------------
st.set_page_config(page_title="Tajný právník BDVH", page_icon="🕵️")
st.title("🕵️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# ID složky na Google Disku
slozka_id = "1pDXRkcEfFvThAMfPBPdFchHgkCk29x_3"  # <- zkontroluj že je aktuální

if st.button("📁 Načíst dokumenty z disku"):
    dokumenty = nacist_soubory_z_podslozek(slozka_id)
    st.success(f"Načteno {len(dokumenty)} dokumentů.")
    for doc in dokumenty[:20]:  # zobrazíme max 20 názvů
        st.write(doc["name"])

st.markdown("---")
otazka = st.text_input("Zeptej se AI...")

if otazka:
    odpoved = ziskej_odpoved(otazka)
    st.markdown("**Odpověď AI:**")
    st.write(odpoved)
