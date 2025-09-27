import io, os, zipfile, tempfile, base64, json
from typing import Dict, Any
import pdfplumber
from docx import Document
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from openai import OpenAI

SYSTEM_PROMPT = """
You are an expert resume parser. Given raw resume text, output ONLY JSON with fields:
- Full_Name (must extract the person's name from the resume header or text, required field)
- Professional_Summary
- Work_Experience (list of descriptions)
- Training_Experience (list of training-specific activities)
- Skill_Set (dictionary: categories -> list of skills)
- Certifications (list)
- Clients (list)

Rules:
- Respond with JSON only. No markdown, no prose.
- Full_Name is REQUIRED. If unclear, infer from the first line or email in the resume.
- Group skills into categories meaningfully.
"""

USER_PROMPT_TEMPLATE = """
Here is the text:

{text}
"""

def process_resume(file_bytes: bytes, openai_key: str):
    raw_text = extract_text_safely(file_bytes)
    if not raw_text.strip():
        raw_text = " "

    data = call_openai_structured(raw_text, openai_key)

    # --- fallback if name missing ---
    if not data.get("Full_Name"):
        first_line = raw_text.splitlines()[0].strip()
        if 2 <= len(first_line.split()) <= 4:
            data["Full_Name"] = first_line
        else:
            data["Full_Name"] = "Trainer"

    html = render_html(data)
    pdf_bytes = html_to_pdf(html)

    return pdf_bytes, data.get("Full_Name", "Trainer")


# -----------------------------
# Extraction (basic PDF & DOCX)
# -----------------------------
def extract_text_safely(file_bytes: bytes) -> str:
    # PDF
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages)
            if text.strip():
                return text
    except Exception:
        pass

    # DOCX
    try:
        buf = io.BytesIO(file_bytes)
        doc = Document(buf)
        paras = [p.text for p in doc.paragraphs]
        text = "\n".join(paras)
        if text.strip():
            return text
    except Exception:
        pass

    # Fallback
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# -----------------------------
# OpenAI call
# -----------------------------
def call_openai_structured(text: str, openai_key: str) -> Dict[str, Any]:
    client = OpenAI(api_key=openai_key)
    prompt_user = USER_PROMPT_TEMPLATE.format(text=text)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content if resp and resp.choices else "{}"
    try:
        return json.loads(_extract_json(content))
    except Exception:
        return {}


def _extract_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
    return s


# -----------------------------
# HTML + PDF
# -----------------------------
def render_html(data: Dict[str, Any]) -> str:
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("template.html")
    logo_b64 = load_logo_base64("app/static/3ek-logo.png")
    return template.render(**data, logo_b64=logo_b64)


def html_to_pdf(html: str) -> bytes:
    pdf_io = io.BytesIO()
    HTML(string=html, base_url=os.getcwd()).write_pdf(pdf_io)
    return pdf_io.getvalue()


def load_logo_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        return ""