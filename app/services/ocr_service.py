"""
OCR Service
Extract text from PDFs and images using Tesseract OCR
"""

import os
import tempfile
from typing import Optional, List, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Lazy imports to handle missing dependencies gracefully
pytesseract = None
Image = None
convert_from_path = None


def _ensure_imports():
    """Lazily import OCR dependencies"""
    global pytesseract, Image, convert_from_path
    
    if pytesseract is None:
        try:
            import pytesseract as pt
            pytesseract = pt
        except ImportError:
            logger.warning("pytesseract not installed. OCR will be limited.")
    
    if Image is None:
        try:
            from PIL import Image as PILImage
            Image = PILImage
        except ImportError:
            logger.warning("PIL not installed. Image processing will be limited.")
    
    if convert_from_path is None:
        try:
            from pdf2image import convert_from_path as cfp
            convert_from_path = cfp
        except ImportError:
            logger.warning("pdf2image not installed. PDF processing will be limited.")


class OCRService:
    """Service for extracting text from documents using OCR"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_cmd: Path to tesseract executable (if not in PATH)
        """
        _ensure_imports()
        
        if tesseract_cmd and pytesseract:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_from_image(self, image_path: str) -> str:
        """
        Extract text from an image file
        
        Args:
            image_path: Path to image file (PNG, JPG, etc.)
            
        Returns:
            Extracted text
        """
        _ensure_imports()
        
        if not pytesseract or not Image:
            return self._fallback_text(image_path)
        
        try:
            image = Image.open(image_path)
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return self._fallback_text(image_path)
    
    def extract_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
        """
        _ensure_imports()
        
        if not convert_from_path:
            return self._fallback_text(pdf_path)
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=200)
            
            all_text = []
            for i, image in enumerate(images):
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    image.save(tmp.name, 'PNG')
                    page_text = self.extract_from_image(tmp.name)
                    all_text.append(f"--- Page {i+1} ---\n{page_text}")
                    os.unlink(tmp.name)
            
            return "\n\n".join(all_text)
        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            return self._fallback_text(pdf_path)
    
    def extract(self, file_path: str) -> str:
        """
        Extract text from any supported file type
        
        Args:
            file_path: Path to file (PDF or image)
            
        Returns:
            Extracted text
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.pdf':
            return self.extract_from_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
            return self.extract_from_image(file_path)
        else:
            # Try as image
            return self.extract_from_image(file_path)
    
    def extract_from_bytes(self, content: bytes, filename: str) -> str:
        """
        Extract text from file bytes
        
        Args:
            content: File content as bytes
            filename: Original filename (for extension detection)
            
        Returns:
            Extracted text
        """
        ext = Path(filename).suffix.lower()
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            text = self.extract(tmp.name)
            os.unlink(tmp.name)
            return text
    
    def _fallback_text(self, file_path: str) -> str:
        """
        Return fallback/demo text when OCR is not available
        Used for development and testing
        """
        return """
SAMPLE INVOICE (OCR NOT AVAILABLE)

Invoice No: INV-2024-001
Date: 2024-12-20
Due Date: 2025-01-20

From:
ABC Suppliers Pvt Ltd
GSTIN: 27AAAAA0000A1Z5
123 Business Street, Mumbai

To:
XYZ Company Ltd
GSTIN: 29BBBBB0000B1Z6
456 Commerce Road, Bangalore

Items:
1. Office Supplies - Qty: 10 - Rate: 500 - Amount: 5,000
2. Printer Paper - Qty: 20 - Rate: 300 - Amount: 6,000

Subtotal: 11,000
CGST (9%): 990
SGST (9%): 990
Total Tax: 1,980

Grand Total: 12,980

Note: This is demo text. Install pytesseract for real OCR.
"""


# Singleton instance
_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """Get or create OCR service singleton"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
