"""
Invoice Agent
Extracts structured data from invoice text using AI
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
import re
import json

from .base_agent import BaseAgent
from ..models.invoice import Invoice, InvoiceItem, InvoiceError, TaxBreakdown, InvoiceStatus
from ..services.llm_service import LLMService


class InvoiceAgent(BaseAgent):
    """
    Agent for extracting structured invoice data from OCR text
    
    Responsibilities:
    - Parse invoice text to extract key fields
    - Validate GSTIN format
    - Identify missing or invalid fields
    - Structure data for downstream processing
    """
    
    agent_name = "invoice_agent"
    agent_version = "1.0.0"
    
    # GSTIN regex pattern: 2 digits + 10 chars + 1 digit + 1 char + 1 checksum
    GSTIN_PATTERN = r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}'
    
    # Common expense categories
    EXPENSE_CATEGORIES = [
        "Office Supplies",
        "IT & Software",
        "Travel & Transport",
        "Marketing & Advertising",
        "Professional Services",
        "Utilities",
        "Rent & Lease",
        "Equipment",
        "Raw Materials",
        "Inventory",
        "Other"
    ]
    
    def get_system_prompt(self) -> str:
        return """You are an expert invoice data extraction agent. Your job is to extract structured information from invoice text.

You must extract:
1. Invoice number and dates
2. Vendor (seller) information including name, address, GSTIN
3. Buyer information
4. Line items with quantities, prices, and taxes
5. Tax breakdown (CGST, SGST, IGST)
6. Total amounts

Be precise with numbers. If a field is not present, use null.
Always return valid JSON matching the expected schema."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract invoice data from OCR text
        
        Args:
            input_data: Dict with 'text' key containing OCR text
            
        Returns:
            Extracted invoice data
        """
        self.validate_input(input_data, ["text"])
        text = input_data["text"]
        file_path = input_data.get("file_path")
        
        self.log("Starting invoice extraction")
        
        # Try LLM extraction first
        if self.llm.backend:
            try:
                invoice_data = self._extract_with_llm(text)
                self.log("LLM extraction successful")
            except Exception as e:
                self.log(f"LLM extraction failed: {e}, using regex fallback", level="warning")
                invoice_data = self._extract_with_regex(text)
        else:
            self.log("No LLM available, using regex extraction")
            invoice_data = self._extract_with_regex(text)
        
        # Build Invoice model
        invoice = self._build_invoice(invoice_data, text, file_path)
        
        # Validate and find errors
        errors = self._validate_invoice(invoice)
        invoice.errors = errors
        
        if errors:
            invoice.status = InvoiceStatus.NEEDS_REVIEW
            self.log(f"Found {len(errors)} validation issues")
        else:
            invoice.status = InvoiceStatus.PROCESSED
            self.log("Invoice validated successfully")
        
        return invoice.model_dump()
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Extract invoice data using LLM"""
        
        schema_hint = """{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD or null",
  "vendor_name": "string",
  "vendor_gstin": "string or null",
  "vendor_address": "string or null",
  "vendor_email": "string or null",
  "buyer_name": "string or null",
  "buyer_gstin": "string or null",
  "items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "hsn_code": "string or null",
      "tax_rate": number,
      "tax_amount": number,
      "total": number
    }
  ],
  "subtotal": number,
  "cgst_amount": number,
  "sgst_amount": number,
  "igst_amount": number,
  "total_tax": number,
  "total_amount": number,
  "currency": "INR"
}"""
        
        prompt = f"""Extract invoice data from the following text:

{text}

Return a JSON object with the invoice information."""
        
        return self.llm.extract_json(prompt, system_prompt=self.get_system_prompt(), schema_hint=schema_hint)
    
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based extraction"""
        
        data = {
            "invoice_number": self._extract_invoice_number(text),
            "invoice_date": self._extract_date(text, ["invoice date", "date:", "dated"]),
            "due_date": self._extract_date(text, ["due date", "payment due"]),
            "vendor_name": self._extract_vendor_name(text),
            "vendor_gstin": self._extract_gstin(text),
            "subtotal": self._extract_amount(text, ["subtotal", "sub total", "sub-total"]),
            "total_tax": self._extract_amount(text, ["total tax", "tax total", "gst"]),
            "total_amount": self._extract_amount(text, ["grand total", "total amount", "total:", "amount due"]),
            "items": [],
            "cgst_amount": self._extract_amount(text, ["cgst"]),
            "sgst_amount": self._extract_amount(text, ["sgst"]),
            "igst_amount": self._extract_amount(text, ["igst"]),
        }
        
        return data
    
    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number from text"""
        patterns = [
            r'invoice\s*(?:no|number|#)?[:\s]*([A-Z0-9\-/]+)',
            r'inv[:\s]*([A-Z0-9\-/]+)',
            r'bill\s*(?:no|number)?[:\s]*([A-Z0-9\-/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "UNKNOWN"
    
    def _extract_date(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract date near specified keywords"""
        # Date patterns
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-12-20
            r'(\d{2}/\d{2}/\d{4})',  # 20/12/2024
            r'(\d{2}-\d{2}-\d{4})',  # 20-12-2024
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})',  # 20 Dec 2024
        ]
        
        for keyword in keywords:
            # Find text around keyword
            pattern = rf'{keyword}[:\s]*(.{{0,30}})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                context = match.group(1)
                for date_pattern in date_patterns:
                    date_match = re.search(date_pattern, context, re.IGNORECASE)
                    if date_match:
                        return self._normalize_date(date_match.group(1))
        
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        from datetime import datetime
        
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d %b %Y",
            "%d %B %Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return date_str
    
    def _extract_gstin(self, text: str) -> Optional[str]:
        """Extract GSTIN from text"""
        match = re.search(self.GSTIN_PATTERN, text)
        return match.group(0) if match else None
    
    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor/company name from text"""
        # Look for patterns like "From:", "Seller:", company names
        patterns = [
            r'(?:from|seller|vendor)[:\s]+([A-Za-z\s]+(?:pvt\.?\s*ltd\.?|limited|inc\.?|llp|corp\.?))',
            r'^([A-Za-z\s]+(?:pvt\.?\s*ltd\.?|limited|inc\.?|llp|corp\.?))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Vendor"
    
    def _extract_amount(self, text: str, keywords: List[str]) -> float:
        """Extract amount near specified keywords"""
        for keyword in keywords:
            # Pattern: keyword followed by optional Rs/₹/INR and number
            pattern = rf'{keyword}[:\s]*(?:rs\.?|₹|inr)?\s*([\d,]+(?:\.\d{2})?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return 0.0
    
    def _build_invoice(self, data: Dict[str, Any], raw_text: str, file_path: Optional[str]) -> Invoice:
        """Build Invoice model from extracted data"""
        
        # Parse date
        invoice_date = data.get("invoice_date")
        if isinstance(invoice_date, str):
            try:
                invoice_date = date.fromisoformat(invoice_date)
            except:
                invoice_date = date.today()
        elif not invoice_date:
            invoice_date = date.today()
        
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = date.fromisoformat(due_date)
            except:
                due_date = None
        
        # Build items
        items = []
        for item_data in data.get("items", []):
            try:
                items.append(InvoiceItem(
                    description=item_data.get("description", "Unknown Item"),
                    quantity=float(item_data.get("quantity", 1)),
                    unit_price=float(item_data.get("unit_price", 0)),
                    hsn_code=item_data.get("hsn_code"),
                    tax_rate=float(item_data.get("tax_rate", 18)),
                    tax_amount=float(item_data.get("tax_amount", 0)),
                    total=float(item_data.get("total", 0))
                ))
            except Exception as e:
                self.log(f"Failed to parse item: {e}", level="warning")
        
        # Build tax breakdown
        tax_breakdown = TaxBreakdown(
            cgst_amount=float(data.get("cgst_amount", 0)),
            sgst_amount=float(data.get("sgst_amount", 0)),
            igst_amount=float(data.get("igst_amount", 0)),
            total_tax=float(data.get("total_tax", 0))
        )
        
        return Invoice(
            invoice_number=data.get("invoice_number", "UNKNOWN"),
            invoice_date=invoice_date,
            due_date=due_date,
            vendor_name=data.get("vendor_name", "Unknown Vendor"),
            vendor_gstin=data.get("vendor_gstin"),
            vendor_address=data.get("vendor_address"),
            vendor_email=data.get("vendor_email"),
            buyer_name=data.get("buyer_name"),
            buyer_gstin=data.get("buyer_gstin"),
            items=items,
            subtotal=float(data.get("subtotal", 0)),
            tax_breakdown=tax_breakdown,
            total_tax=float(data.get("total_tax", 0)),
            total_amount=float(data.get("total_amount", 0)),
            currency=data.get("currency", "INR"),
            raw_text=raw_text,
            file_path=file_path
        )
    
    def _validate_invoice(self, invoice: Invoice) -> List[InvoiceError]:
        """Validate invoice and return list of errors"""
        errors = []
        
        # Check for missing GSTIN
        if not invoice.vendor_gstin:
            errors.append(InvoiceError(
                field="vendor_gstin",
                error_type="missing_field",
                message="Vendor GSTIN is missing from the invoice",
                severity="error",
                suggested_action="Request vendor to provide GSTIN"
            ))
        elif not invoice.validate_gstin(invoice.vendor_gstin):
            errors.append(InvoiceError(
                field="vendor_gstin",
                error_type="invalid_format",
                message=f"Vendor GSTIN '{invoice.vendor_gstin}' has invalid format",
                severity="error",
                suggested_action="Verify GSTIN format with vendor"
            ))
        
        # Check tax calculations
        if invoice.subtotal > 0 and invoice.total_tax > 0:
            expected_tax = invoice.subtotal * 0.18  # Standard 18% GST
            tolerance = invoice.subtotal * 0.02  # 2% tolerance
            
            if abs(invoice.total_tax - expected_tax) > tolerance:
                errors.append(InvoiceError(
                    field="total_tax",
                    error_type="calculation_mismatch",
                    message=f"Tax amount ₹{invoice.total_tax:,.2f} doesn't match expected 18% (₹{expected_tax:,.2f})",
                    severity="warning",
                    suggested_action="Verify tax rate and calculations"
                ))
        
        # Check total amount
        if invoice.subtotal > 0 and invoice.total_amount > 0:
            expected_total = invoice.subtotal + invoice.total_tax
            if abs(invoice.total_amount - expected_total) > 1:  # ₹1 tolerance
                errors.append(InvoiceError(
                    field="total_amount",
                    error_type="calculation_mismatch",
                    message=f"Total ₹{invoice.total_amount:,.2f} doesn't match subtotal + tax (₹{expected_total:,.2f})",
                    severity="warning",
                    suggested_action="Verify invoice totals"
                ))
        
        # Check for missing invoice number
        if invoice.invoice_number in ["UNKNOWN", "", None]:
            errors.append(InvoiceError(
                field="invoice_number",
                error_type="missing_field",
                message="Invoice number could not be extracted",
                severity="warning",
                suggested_action="Verify invoice number manually"
            ))
        
        return errors
    
    def categorize_expense(self, invoice: Invoice) -> str:
        """Categorize the invoice into an expense category"""
        if self.llm.backend:
            try:
                return self.llm.classify(
                    text=f"Vendor: {invoice.vendor_name}\nItems: {', '.join([i.description for i in invoice.items])}",
                    categories=self.EXPENSE_CATEGORIES,
                    context="Categorize this business expense"
                )
            except:
                pass
        return "Other"
