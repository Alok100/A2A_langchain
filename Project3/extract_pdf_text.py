"""
Extract text from a PDF and save to a .txt file.
Run: python extract_pdf_text.py [path/to/file.pdf]
     python extract_pdf_text.py   (uses Project3/AI-Powered HR Decision Assistant.pdf)
Output: same path with .pdf replaced by .txt (e.g. AI-Powered HR Decision Assistant.txt)
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def extract_pdf_to_text(pdf_path: str, out_path: str = None) -> str:
    """Extract text from PDF; write to out_path or pdf_path with .txt. Returns extracted text."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Install PyMuPDF: pip install pymupdf")
        sys.exit(1)
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    text = "\n".join(text_parts)
    if out_path is None:
        out_path = pdf_path.replace(".pdf", ".txt").replace(".PDF", ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Extracted to: {os.path.abspath(out_path)}")
    return text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = os.path.join(SCRIPT_DIR, "AI-Powered HR Decision Assistant.pdf")
    if not os.path.isfile(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)
    extract_pdf_to_text(pdf_path)
