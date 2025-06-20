import streamlit as st
import openai
from fpdf import FPDF
import base64
import io
from pdf2image import convert_from_bytes
from google.cloud import vision
from PIL import Image

# Load API key
st.write("✅ App Loaded")  # debugging

if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ OPENAI_API_KEY not found in Streamlit secrets")
else:
    st.success("✅ API Key found!")

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Google Cloud Vision client (auto-auth from service account env var or secret)
vision_client = vision.ImageAnnotatorClient()

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
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

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
            pass
