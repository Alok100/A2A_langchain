"""
Generate HR policy PDFs from poc_data/hr_rules_content.py.
Run from Project3: python generate_poc_data.py

Edit the text in poc_data/hr_rules_content.py, then run this script to regenerate
the PDFs in poc_data/hr_rules/ (Leave_Policy.pdf, Attendance_Policy.pdf, etc.).
"""
import os
import sys

# Ensure we can import from poc_data
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from poc_data.hr_rules_content import POLICIES

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "poc_data", "hr_rules")


def _escape(s):
    """Escape & < > for ReportLab Paragraph."""
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_to_flow(text, styles):
    """Turn plain policy text into a list of Platypus flowables (Paragraphs)."""
    flow = []
    normal = styles["Normal"]
    for block in text.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        for line in block.split("\n"):
            line = _escape(line.strip())
            if not line:
                continue
            flow.append(Paragraph(line, normal))
        flow.append(Spacer(1, 0.15 * inch))
    return flow


def build_pdf(path, title, text):
    """Build one PDF at path with the given title and body text."""
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            fontSize=14,
            spaceAfter=12,
            textColor="navy",
        )
    )
    flow = [Paragraph(_escape(title), styles["DocTitle"]), Spacer(1, 0.2 * inch)]
    flow += text_to_flow(text, styles)
    doc.build(flow)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Map policy key to a short title for the PDF header (optional)
    titles = {
        "Leave_Policy": "Leave & Time-Off Policy",
        "Attendance_Policy": "Attendance & Timesheet Policy",
        "Code_of_Conduct": "Code of Conduct & Ethics",
        "Asset_Distribution_Policy": "Asset Distribution & Management Policy",
        "Expense_Policy": "Expense & Reimbursement Policy",
        "Grievance_Policy": "Grievance Redressal Policy",
    }
    for key, text in POLICIES.items():
        if not text or not key:
            continue
        filename = f"{key}.pdf"
        out_path = os.path.join(OUTPUT_DIR, filename)
        title = titles.get(key, key.replace("_", " "))
        build_pdf(out_path, title, text)
        print(f"  {filename}")
    print(f"Done. PDFs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
