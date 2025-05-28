from openai import OpenAI

def ziskej_odpoved(otazka: str):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    try:
        return client.chat.completions.create(
            model="gpt-4",  # Zkusí GPT-4
            messages=[
                {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH."},
                {"role": "user", "content": otazka}
            ]
        ).choices[0].message.content
    except Exception as e:
        print("Fallback na GPT-3.5:", e)
        return client.chat.completions.create(
            model="gpt-3.5-turbo",  # Když GPT-4 nejde
            messages=[
                {"role": "system", "content": "Jsi právní AI asistent, který pomáhá s kauzou BDVH."},
                {"role": "user", "content": otazka}
            ]
        ).choices[0].message.content
