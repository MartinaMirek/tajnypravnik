import streamlit as st
from drive_utils import nacist_soubory_z_disku

st.set_page_config(page_title="Tajný právník BDVH", page_icon="🧑‍⚖️")

st.title("🧑‍⚖️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

if st.button("📂 Načíst dokumenty z disku"):
    slozka_id = "1l25KsA_Mx3k0Hko3h9op3Z8Z9E4EpWkQ"  # nahraď podle potřeby
    dokumenty = nacist_soubory_z_disku(slozka_id)
    st.success(f"Načteno {len(dokumenty)} dokumentů.")
    for soubor in dokumenty:
        st.write(f"📄 {soubor['name']} (ID: {soubor['id']})")

