import streamlit as st

st.set_page_config(page_title="Tajný právník BDVH", page_icon="🧑‍⚖️")

st.title("🧑‍⚖️ Tajný právník BDVH")
st.markdown("Vítej! Tady ti AI pomůže vyznat se v právní džungli BDVH.")
st.info("Zeptej se na cokoliv ohledně historie, dokumentů, stanov nebo právních kroků kolem BDVH.")

# Textové vstupní pole (zatím bez napojení na AI)
user_input = st.chat_input("Zeptej se AI...")

if user_input:
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write("🧠 Promiň, zatím nejsem napojen na Google Disk ani AI, ale to brzy přijde!")
