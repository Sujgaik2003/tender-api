"""Extract text from PDF for analysis"""
import pdfplumber
import sys

def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text_content = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(f"=== PAGE {i} ===\n{page_text}")
        return "\n\n".join(text_content)
    except Exception as e:
        return f"Error extracting PDF: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    text = extract_pdf_text(pdf_path)
    print(text)
