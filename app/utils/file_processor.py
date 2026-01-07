import io
from typing import Optional
from docx import Document
import PyPDF2


class FileProcessor:
    """Utility class for processing resume files"""
    
    ALLOWED_EXTENSIONS = {".doc", ".docx", ".pdf"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def is_valid_extension(filename: str) -> bool:
        """Check if file has a valid extension"""
        return any(filename.lower().endswith(ext) for ext in FileProcessor.ALLOWED_EXTENSIONS)
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """Get file type from filename"""
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf"):
            return "pdf"
        elif filename_lower.endswith(".docx"):
            return "docx"
        elif filename_lower.endswith(".doc"):
            return "doc"
        return "unknown"
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_doc(file_content: bytes) -> str:
        """Extract text from DOC file (legacy format)"""
        # DOC files require additional libraries like python-docx2txt or pypandoc
        # For now, we'll raise an error suggesting conversion to DOCX
        raise ValueError(
            "DOC files (legacy format) are not directly supported. "
            "Please convert your file to DOCX or PDF format."
        )
    
    @staticmethod
    def extract_text(file_content: bytes, filename: str) -> str:
        """Extract text from resume file based on file type"""
        file_type = FileProcessor.get_file_type(filename)
        
        if file_type == "pdf":
            return FileProcessor.extract_text_from_pdf(file_content)
        elif file_type == "docx":
            return FileProcessor.extract_text_from_docx(file_content)
        elif file_type == "doc":
            return FileProcessor.extract_text_from_doc(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

