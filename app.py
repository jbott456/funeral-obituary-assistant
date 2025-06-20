import streamlit as st
import openai
from fpdf import FPDF
import base64

st.write("✅ App Loaded")  # debugging

# Debug print to test if secret is present
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ OPENAI_API_KEY not found in Streamlit secrets")
else:
    st.success("✅ API Key found!")

openai.api_key = st.secrets["OPENAI_API_KEY"]

def create_pdf(text, filename="obituary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

    with open(filename, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    return base64_pdf

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

        pdf_base64 = create_pdf(obituary_text)
        href = f'<a href="data:application/pdf;base64,{pdf_base64}" download="{name}_obituary.pdf">\ud83d\udcc4 Download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)



