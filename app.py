import streamlit as st

st.title("✅ App Loaded")
st.write("This is a debug test — if you're seeing this, the app is rendering!")

Python
import streamlit as st
import openai

# Set your OpenAI API key here or set environment variable OPENAI_API_KEY
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else ""

def generate_obituary(data):
    prompt = f"""
Write a respectful obituary for the following person using the details below:

Name: {data['name']}
Date of Birth: {data['dob']}
Date of Death: {data['dod']}
Place of Birth: {data.get('pob', 'N/A')}
Place of Death: {data.get('pod', 'N/A')}
Brief Life Story: {data.get('story', '')}
Survivors: {data.get('survivors', '')}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

st.title("Funeral Home Obituary Assistant")

with st.form("obituary_form"):
    name = st.text_input("Full Name", max_chars=100)
    dob = st.text_input("Date of Birth (e.g., Jan 1, 1940)")
    dod = st.text_input("Date of Death (e.g., Jun 19, 2025)")
    pob = st.text_input("Place of Birth (optional)")
    pod = st.text_input("Place of Death (optional)")
    story = st.text_area("Brief Life Story / Bio (optional)")
    survivors = st.text_area("Survivors (optional)")
    submitted = st.form_submit_button("Generate Obituary")

if submitted:
    if not name or not dob or not dod:
        st.error("Please fill in at least Name, Date of Birth, and Date of Death.")
    else:
        with st.spinner("Generating obituary..."):
            obituary_text = generate_obituary({
                "name": name,
                "dob": dob,
                "dod": dod,
                "pob": pob,
                "pod": pod,
                "story": story,
                "survivors": survivors,
            })
        st.subheader("Generated Obituary")
        st.write(obituary_text)
        st.download_button("Download as Text File", data=obituary_text, file_name=f"{name}_obituary.txt")



