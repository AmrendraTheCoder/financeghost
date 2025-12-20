"""
Email Generator Service
Generate professional vendor communication emails using AI
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .llm_service import LLMService, get_llm_service
from ..models.invoice import Invoice, InvoiceError

logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generate professional emails for vendor communication"""
    
    # Email templates for when LLM is not available
    TEMPLATES = {
        "missing_gstin": """
Subject: Request for GSTIN - Invoice {invoice_number}

Dear {vendor_name} Team,

We hope this email finds you well.

We recently received invoice {invoice_number} dated {invoice_date} from your organization. However, we noticed that the GSTIN (Goods and Services Tax Identification Number) is missing from the invoice.

As per GST regulations, this information is mandatory for us to process the invoice and claim Input Tax Credit (ITC). Could you please provide a revised invoice with the correct GSTIN included?

Invoice Details:
- Invoice Number: {invoice_number}
- Invoice Date: {invoice_date}
- Invoice Amount: ₹{total_amount}

We would appreciate it if you could send the corrected invoice at your earliest convenience.

Thank you for your understanding and cooperation.

Best regards,
{company_name}
""",
        "incorrect_tax": """
Subject: Tax Calculation Discrepancy - Invoice {invoice_number}

Dear {vendor_name} Team,

We hope this email finds you well.

Upon reviewing invoice {invoice_number} dated {invoice_date}, we noticed a discrepancy in the tax calculations:

Issue: {error_message}

Current Values:
- Subtotal: ₹{subtotal}
- Tax Applied: ₹{tax_applied}
- Expected Tax (18%): ₹{expected_tax}

Could you please verify the calculations and issue a revised invoice if necessary?

Thank you for your prompt attention to this matter.

Best regards,
{company_name}
""",
        "general_error": """
Subject: Invoice Correction Required - Invoice {invoice_number}

Dear {vendor_name} Team,

We recently received invoice {invoice_number} dated {invoice_date} from your organization.

Upon review, we identified the following issue(s) that require correction:

{error_details}

Could you please review and send a corrected invoice at your earliest convenience?

Thank you for your cooperation.

Best regards,
{company_name}
"""
    }
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or get_llm_service()
        self.company_name = "FinanceGhost User"  # Default, can be configured
    
    def generate_email(
        self,
        invoice: Invoice,
        error: InvoiceError,
        company_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a professional email for a specific invoice error
        
        Args:
            invoice: Invoice with the error
            error: The specific error to address
            company_name: Optional sender company name
            
        Returns:
            Dict with 'subject' and 'body' keys
        """
        company = company_name or self.company_name
        
        # Try LLM first
        if self.llm.backend:
            try:
                return self._generate_with_llm(invoice, error, company)
            except Exception as e:
                logger.warning(f"LLM email generation failed: {e}. Using template.")
        
        # Fall back to templates
        return self._generate_from_template(invoice, error, company)
    
    def _generate_with_llm(
        self,
        invoice: Invoice,
        error: InvoiceError,
        company_name: str
    ) -> Dict[str, str]:
        """Generate email using LLM"""
        
        system_prompt = """You are a professional finance assistant generating vendor communication emails.
Write clear, polite, and professional emails that:
- Are respectful and maintain good business relationships
- Clearly state the issue and what action is needed
- Include relevant invoice details
- Are concise but complete

Return JSON with 'subject' and 'body' keys."""

        prompt = f"""Generate a professional email to a vendor requesting a correction for an invoice issue.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Invoice Date: {invoice.invoice_date}
- Vendor Name: {invoice.vendor_name}
- Total Amount: ₹{invoice.total_amount:,.2f}
- Subtotal: ₹{invoice.subtotal:,.2f}
- Tax Amount: ₹{invoice.total_tax:,.2f}

Issue Found:
- Field: {error.field}
- Error Type: {error.error_type}
- Description: {error.message}
- Severity: {error.severity}
- Suggested Action: {error.suggested_action or 'Request correction'}

Sender Company: {company_name}

Generate a professional email requesting the vendor to fix this issue."""

        result = self.llm.extract_json(prompt, system_prompt=system_prompt)
        return {
            "subject": result.get("subject", f"Invoice Correction Required - {invoice.invoice_number}"),
            "body": result.get("body", "Please review and correct the invoice.")
        }
    
    def _generate_from_template(
        self,
        invoice: Invoice,
        error: InvoiceError,
        company_name: str
    ) -> Dict[str, str]:
        """Generate email using predefined templates"""
        
        # Select template based on error type
        if "gstin" in error.field.lower() or "gst" in error.error_type.lower():
            template_key = "missing_gstin"
        elif "tax" in error.field.lower() or "tax" in error.error_type.lower():
            template_key = "incorrect_tax"
        else:
            template_key = "general_error"
        
        template = self.TEMPLATES[template_key]
        
        # Calculate expected tax for tax errors
        expected_tax = invoice.subtotal * 0.18 if invoice.subtotal else 0
        
        # Format the template
        body = template.format(
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            vendor_name=invoice.vendor_name,
            total_amount=f"{invoice.total_amount:,.2f}",
            subtotal=f"{invoice.subtotal:,.2f}",
            tax_applied=f"{invoice.total_tax:,.2f}",
            expected_tax=f"{expected_tax:,.2f}",
            error_message=error.message,
            error_details=f"- {error.field}: {error.message}",
            company_name=company_name
        )
        
        # Extract subject from body
        lines = body.strip().split('\n')
        subject = lines[0].replace("Subject:", "").strip() if lines[0].startswith("Subject:") else f"Invoice Correction - {invoice.invoice_number}"
        body = "\n".join(lines[1:]).strip() if lines[0].startswith("Subject:") else body
        
        return {
            "subject": subject,
            "body": body
        }
    
    def generate_batch_email(
        self,
        invoice: Invoice,
        company_name: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Generate email for all errors in an invoice
        
        Args:
            invoice: Invoice with errors
            company_name: Optional sender company name
            
        Returns:
            Combined email addressing all issues, or None if no errors
        """
        if not invoice.errors:
            return None
        
        # For single error, use specific email
        if len(invoice.errors) == 1:
            return self.generate_email(invoice, invoice.errors[0], company_name)
        
        # For multiple errors, generate combined email
        company = company_name or self.company_name
        
        error_list = "\n".join([
            f"- {e.field}: {e.message}" for e in invoice.errors
        ])
        
        body = f"""Dear {invoice.vendor_name} Team,

We recently received invoice {invoice.invoice_number} dated {invoice.invoice_date}.

Upon review, we identified the following issues that require your attention:

{error_list}

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Invoice Date: {invoice.invoice_date}
- Invoice Amount: ₹{invoice.total_amount:,.2f}

Could you please review these issues and send a corrected invoice at your earliest convenience?

Thank you for your cooperation.

Best regards,
{company}"""

        return {
            "subject": f"Invoice Correction Required - {invoice.invoice_number} ({len(invoice.errors)} issues)",
            "body": body
        }


# Factory function
def get_email_generator() -> EmailGenerator:
    """Get email generator instance"""
    return EmailGenerator()
