"""
Invoice Data Models
Defines the structure for invoice data throughout the system
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from decimal import Decimal


class InvoiceStatus(str, Enum):
    """Status of invoice processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"
    NEEDS_REVIEW = "needs_review"
    VENDOR_CONTACTED = "vendor_contacted"


class InvoiceItem(BaseModel):
    """Individual line item on an invoice"""
    description: str = Field(..., description="Item description")
    quantity: float = Field(default=1.0, ge=0)
    unit_price: float = Field(..., ge=0)
    hsn_code: Optional[str] = Field(default=None, description="HSN/SAC code for GST")
    tax_rate: float = Field(default=18.0, description="Tax rate percentage")
    tax_amount: float = Field(default=0.0, ge=0)
    total: float = Field(..., ge=0)
    
    def calculate_tax(self) -> float:
        """Calculate tax amount based on unit price and tax rate"""
        subtotal = self.quantity * self.unit_price
        return subtotal * (self.tax_rate / 100)


class TaxBreakdown(BaseModel):
    """GST tax breakdown"""
    cgst_rate: float = Field(default=9.0, description="CGST rate")
    cgst_amount: float = Field(default=0.0)
    sgst_rate: float = Field(default=9.0, description="SGST rate")
    sgst_amount: float = Field(default=0.0)
    igst_rate: float = Field(default=0.0, description="IGST rate (for inter-state)")
    igst_amount: float = Field(default=0.0)
    cess_amount: float = Field(default=0.0)
    total_tax: float = Field(default=0.0)


class InvoiceError(BaseModel):
    """Represents an error or issue found in the invoice"""
    field: str = Field(..., description="Field with the error")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Human-readable error message")
    severity: str = Field(default="warning", description="error, warning, or info")
    suggested_action: Optional[str] = Field(default=None)


class Invoice(BaseModel):
    """Complete invoice data model"""
    
    # Identification
    id: Optional[str] = Field(default=None)
    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(default=None)
    
    # Vendor Information
    vendor_name: str = Field(..., description="Vendor/Seller name")
    vendor_gstin: Optional[str] = Field(default=None, description="Vendor GSTIN")
    vendor_address: Optional[str] = Field(default=None)
    vendor_email: Optional[str] = Field(default=None)
    vendor_phone: Optional[str] = Field(default=None)
    
    # Buyer Information
    buyer_name: Optional[str] = Field(default=None)
    buyer_gstin: Optional[str] = Field(default=None)
    buyer_address: Optional[str] = Field(default=None)
    
    # Items
    items: List[InvoiceItem] = Field(default_factory=list)
    
    # Financial Summary
    subtotal: float = Field(default=0.0, ge=0)
    tax_breakdown: Optional[TaxBreakdown] = Field(default=None)
    total_tax: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="INR")
    
    # Processing
    status: InvoiceStatus = Field(default=InvoiceStatus.PENDING)
    errors: List[InvoiceError] = Field(default_factory=list)
    raw_text: Optional[str] = Field(default=None, description="Original OCR text")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = Field(default=None)
    file_path: Optional[str] = Field(default=None)
    
    # Cash Flow Category
    expense_category: Optional[str] = Field(default=None)
    
    def has_errors(self) -> bool:
        """Check if invoice has any errors"""
        return len([e for e in self.errors if e.severity == "error"]) > 0
    
    def has_warnings(self) -> bool:
        """Check if invoice has warnings"""
        return len([e for e in self.errors if e.severity == "warning"]) > 0
    
    def validate_gstin(self, gstin: str) -> bool:
        """Validate GSTIN format (basic validation)"""
        if not gstin:
            return False
        # GSTIN format: 22AAAAA0000A1Z5
        if len(gstin) != 15:
            return False
        # First 2 digits: State code (01-37)
        if not gstin[:2].isdigit():
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()


class InvoiceProcessingResult(BaseModel):
    """Result of processing an invoice through all agents"""
    invoice: Invoice
    tax_validation: Dict[str, Any] = Field(default_factory=dict)
    cashflow_analysis: Dict[str, Any] = Field(default_factory=dict)
    generated_email: Optional[str] = Field(default=None)
    processing_time_ms: float = Field(default=0.0)
    agent_logs: List[str] = Field(default_factory=list)
