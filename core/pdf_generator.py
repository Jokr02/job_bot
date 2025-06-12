import os
from fpdf import FPDF
from core.logging import logger

def generate_cover_letter(job_title: str, template_path="data/anschreiben_vorlage.txt", output_path="data/anschreiben.pdf"):
    try:
        with open(template_path, encoding="utf-8") as f:
            text = f.read()

        text = text.replace("{{job_title}}", job_title)
        text = text.replace("{{sender_name}}", os.getenv("SENDER_NAME", "Max Mustermann"))

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, f"Bewerbung als {job_title}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)

        for line in text.splitlines():
            if line.strip():
                pdf.multi_cell(0, 8, line)
            else:
                pdf.ln(4)

        pdf.output(output_path)
        logger.info(f"📄 Anschreiben gespeichert unter: {output_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des Anschreibens: {e}")
        return False
