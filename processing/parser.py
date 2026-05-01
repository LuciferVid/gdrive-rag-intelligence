import io
from pypdf import PdfReader

class DocumentParser:
    @staticmethod
    def extract_text(content, mime_type):
        """Extracts text based on mime type."""
        if mime_type == 'application/pdf':
            return DocumentParser._parse_pdf(content)
        elif mime_type == 'text/plain' or mime_type == 'application/vnd.google-apps.document':
            # Google Docs were exported as plain text, so we treat them as such
            return content.decode('utf-8')
        else:
            return ""

    @staticmethod
    def _parse_pdf(content):
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
 