"""
Vendor Data Model
Represents vendor/supplier information for communication
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class Vendor(BaseModel):
    """Vendor/Supplier information model"""
    
    id: Optional[str] = Field(default=None)
    name: str = Field(..., description="Vendor company name")
    gstin: Optional[str] = Field(default=None, description="GSTIN number")
    email: Optional[str] = Field(default=None, description="Contact email")
    phone: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    
    # Relationship tracking
    total_invoices: int = Field(default=0)
    total_amount: float = Field(default=0.0)
    average_response_time_hours: Optional[float] = Field(default=None)
    
    # Communication history
    last_contacted: Optional[datetime] = Field(default=None)
    emails_sent: int = Field(default=0)
    emails_responded: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def response_rate(self) -> float:
        """Calculate email response rate"""
        if self.emails_sent == 0:
            return 0.0
        return (self.emails_responded / self.emails_sent) * 100


class VendorEmail(BaseModel):
    """Email communication with a vendor"""
    
    id: Optional[str] = Field(default=None)
    vendor_id: str
    invoice_id: str
    
    subject: str
    body: str
    email_type: str = Field(default="correction_request")  # correction_request, followup, thank_you
    
    sent_at: Optional[datetime] = Field(default=None)
    responded_at: Optional[datetime] = Field(default=None)
    response_content: Optional[str] = Field(default=None)
    
    status: str = Field(default="draft")  # draft, pending_approval, sent, responded
