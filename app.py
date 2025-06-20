import streamlit as st
import openai
from fpdf import FPDF
import base64
import io
from pdf2image import convert_from_bytes
from google.cloud import vision
from PIL import Image
from pyairtable import Api  # Airtable integration

# Page setup
st.set_page_config(page_title="Funeral Obituary Assistant", page_icon="🕊️")
st.title("🕊️ Funeral Home Obituary Assistant")

# API key check
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ OPENAI_API_KEY not found in Streamlit secrets")
    st.stop()
else:
    st.success("✅ API Key found!")

# Initialize clients
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
vision_client = vision.ImageAnnotatorClient()

# Airtable save function
def upload_to_airtable(data, obituary_text):
    token = st.secrets.get("AIRTABLE_TOKEN")
    base_id = st.secrets.get("AIRTABLE_BASE_ID")
    table_name = st.secrets.get("AIRTABLE_TABLE_NAME")

    if not token or not base_id or not table_name:
        st.warning("⚠️ Airtable credentials not set properly.")
        return

    try:
        api = Api(token)
        table = api.table(base_id, table_name)
        table.create({
            "Name": data["name"],
            "Date of Birth": data["dob"],
            "Date of Death": data["dod"],
            "Place of Birth": data.get("pob", ""),
            "Place of Death": data.get("pod", ""),
            "Bio": data.get("story", ""),
            "Survivors": data.get("survivors", ""),
            "Obituary Text": obituary_text,
        })
        st.success("✅ Obituary saved to Airtable.")
    except Exception as e:
        st.error(f"❌ Airtable error: {e}")

# PDF generation
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

# GPT generation
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
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# OCR from uploaded PDF
def extract_text_from_pdf(uploaded_file):
    pdf_bytes = uploaded_file.read()
    images = convert_from_bytes(pdf_bytes, dpi=300)
    first_image = images[0]

    buf = io.BytesIO()
    first_image.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    image = vision.Image(content=image_bytes)
    response = vision_client.document_text_detection(image=image)
    if response.error.message:
        st.error(f"Google OCR Error: {response.error.message}")
        return ""

    return response.full_text_annotation.text

# Basic field extraction from OCR'd text
def basic_parse_ocr_text(text):
    lines = text.split("\n")
    data = {"name": "", "dob": "", "dod": "", "pob": "", "pod": "", "story": "", "survivors": ""}
    for line in lines:
        line_lower = line.lower()
        if "name" in line_lower and not data["name"]:
            data["name"] = line.split(":")[-1].strip()
        elif "date of birth" in line_lower:
            data["dob"] = line.split(":")[-1].strip()
        elif "date of death" in line_lower:
            data["dod"] = line.split(":")[-1].strip()
        elif "place of birth" in line_lower:
            data["pob"] = line.split(":")[-1].strip()
        elif "place of death" in line_lower:
            data["pod"] = line.split(":")[-1].strip()
        elif "survivors" in line_lower:
            data["survivors"] = line.split(":")[-1].strip()
        elif "bio" in line_lower or "story" in line_lower:
            data["story"] += line.strip() + " "
    return data

# UI: file upload
st.subheader("Upload Handwritten or Typed Obituary Form (PDF)")
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

pre_filled = {"name": "", "dob": "", "dod": "", "pob": "", "pod": "", "story": "", "survivors": ""}

if uploaded_file:
    with st.spinner("Extracting text with OCR..."):
        ocr_text = extract_text_from_pdf(uploaded_file)
        pre_filled = basic_parse_ocr_text(ocr_text)
    st.success("✅ Text extracted and pre-filled in the form below")

# Form UI
with st.form("obituary_form"):
    name = st.text_input("Full Name", value=pre_filled.get("name", ""))
    dob = st.text_input("Date of Birth", value=pre_filled.get("dob", ""))
    dod = st.text_input("Date of Death", value=pre_filled.get("dod", ""))
    pob = st.text_input("Place of Birth", value=pre_filled.get("pob", ""))
    pod = st.text_input("Place of Death", value=pre_filled.get("pod", ""))
    story = st.text_area("Brief Life Story", value=pre_filled.get("story", ""))
    survivors = st.text_area("Survivors", value=pre_filled.get("survivors", ""))
    submitted = st.form_submit_button("Generate Obituary")

# Generate result
if submitted:
    if not name or not dob or not dod:
        st.error("Please fill in at least Name, Date of Birth, and Date of Death.")
    else:
        with st.spinner("Generating obituary..."):
            data_input = {
