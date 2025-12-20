"""
Workflow and Risk Data Models
Defines structures for firm-level intelligence and compliance tracking
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkItemType(str, Enum):
    """Types of work items"""
    INVOICE_ISSUE = "invoice_issue"
    GST_RECONCILIATION = "gst_reconciliation"
    MISSING_DATA = "missing_data"
    DEADLINE_RISK = "deadline_risk"
    TAX_MISMATCH = "tax_mismatch"
    VENDOR_FOLLOWUP = "vendor_followup"


class MonthEndPhase(str, Enum):
    """Month-end close progress phases"""
    NOT_STARTED = "not_started"
    DATA_COLLECTION = "data_collection"
    RECONCILIATION = "reconciliation"
    REVIEW = "review"
    FILING_READY = "filing_ready"
    COMPLETE = "complete"


class ComplianceRisk(BaseModel):
    """Risk assessment for a client or invoice"""
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    risk_score: int = Field(default=0, ge=0, le=100, description="0-100 risk score")
    reasons: List[str] = Field(default_factory=list, description="Why this risk level")
    suggested_actions: List[str] = Field(default_factory=list)
    affected_invoices: List[str] = Field(default_factory=list, description="Invoice IDs involved")
    deadline: Optional[date] = Field(default=None, description="Related deadline if any")


class UrgentWorkItem(BaseModel):
    """An item requiring immediate attention"""
    id: str = Field(..., description="Unique identifier")
    type: WorkItemType = Field(...)
    client_name: str = Field(...)
    title: str = Field(..., description="Short description of the issue")
    description: str = Field(..., description="Detailed explanation")
    reason: str = Field(..., description="Why this needs attention now")
    priority_score: int = Field(default=50, ge=0, le=100)
    deadline: Optional[date] = Field(default=None)
    suggested_action: str = Field(...)
    invoice_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ClientWorkflowStatus(BaseModel):
    """Month-end workflow status for a client"""
    client_id: str = Field(...)
    client_name: str = Field(...)
    phase: MonthEndPhase = Field(default=MonthEndPhase.NOT_STARTED)
    progress_percent: int = Field(default=0, ge=0, le=100)
    risk: ComplianceRisk = Field(default_factory=ComplianceRisk)
    pending_items: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    assigned_to: Optional[str] = Field(default=None, description="Team member handling")
    notes: Optional[str] = Field(default=None)


class FirmRiskDashboard(BaseModel):
    """Firm-level risk overview"""
    total_clients: int = Field(default=0)
    high_risk_clients: int = Field(default=0)
    medium_risk_clients: int = Field(default=0)
    low_risk_clients: int = Field(default=0)
    urgent_items_count: int = Field(default=0)
    upcoming_deadlines: int = Field(default=0)
    overall_health_score: int = Field(default=100, ge=0, le=100)
    risk_trend: str = Field(default="stable", description="improving, stable, worsening")
    generated_at: datetime = Field(default_factory=datetime.now)


class MonthEndDashboard(BaseModel):
    """Month-end close autopilot dashboard data"""
    current_month: str = Field(...)
    overall_progress: int = Field(default=0, ge=0, le=100)
    clients_status: List[ClientWorkflowStatus] = Field(default_factory=list)
    urgent_items: List[UrgentWorkItem] = Field(default_factory=list)
    risk_summary: FirmRiskDashboard = Field(default_factory=FirmRiskDashboard)
    ai_briefing: str = Field(default="", description="AI-generated daily briefing")
    bottlenecks: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class DayBriefing(BaseModel):
    """AI-generated daily briefing for the firm"""
    briefing_date: date = Field(default_factory=date.today)
    headline: str = Field(..., description="One-line summary")
    key_points: List[str] = Field(default_factory=list)
    urgent_actions: List[str] = Field(default_factory=list)
    risks_to_watch: List[str] = Field(default_factory=list)
    positive_notes: List[str] = Field(default_factory=list)
    full_briefing: str = Field(..., description="Full AI-generated narrative")

