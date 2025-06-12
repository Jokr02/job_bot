
from fpdf import FPDF
import os

def generate_cover_letter(job_title: str, template_path="data/anschreiben_vorlage.txt", output_path="data/anschreiben.pdf"):
    with open(template_path, encoding="utf-8") as f:
        text = f.read()
    text = text.replace("{{job_title}}", job_title)
    text = text.replace("{{sender_name}}", os.getenv("SENDER_NAME", "Max Mustermann"))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i == 0:
            pdf.set_font("Arial", "B", size=11)
        else:
            pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, line)

    pdf.output(output_path)
