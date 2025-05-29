54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
import streamlit as st
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
