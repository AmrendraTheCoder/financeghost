"""
Compliance Risk Agent
Analyzes multi-client compliance posture and identifies risks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging

from .base_agent import BaseAgent
from ..database.db import get_db
from ..models.workflow import (
    RiskLevel,
    WorkItemType,
    ComplianceRisk,
    UrgentWorkItem,
    FirmRiskDashboard
)

logger = logging.getLogger(__name__)


class ComplianceRiskAgent(BaseAgent):
    """
    Analyzes multi-client compliance posture.
    - Identifies invoices at risk of compliance issues
    - Predicts GSTR filing problems before deadline
    - Surfaces "attention needed today" items
    """
    
    agent_name = "compliance_risk"
    agent_version = "1.0.0"
    
    # GSTR filing deadlines (day of month)
    GSTR1_DEADLINE = 11  # GSTR-1 due by 11th
    GSTR3B_DEADLINE = 20  # GSTR-3B due by 20th
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
    
    def get_system_prompt(self) -> str:
        return """You are a compliance risk analysis agent for Indian CA firms.
Your job is to identify compliance risks across clients, predict GSTR filing issues,
and surface items that need immediate attention. Focus on:
- GST compliance and ITC reconciliation
- Invoice validation issues
- Upcoming filing deadlines
- Tax calculation mismatches
Generate clear, actionable insights for the CA to address."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process compliance risk analysis request
        
        Args:
            input_data: May contain client_id for specific client, or empty for firm-wide
        """
        client_id = input_data.get("client_id")
        
        if client_id:
            self.log(f"Analyzing compliance risk for client: {client_id}")
            risk = self.get_client_compliance_posture(client_id)
            return {"client_risk": risk.model_dump() if risk else None}
        else:
            self.log("Analyzing firm-wide compliance risk")
            dashboard = self.generate_risk_summary()
            return {"firm_dashboard": dashboard.model_dump()}
    
    def get_client_compliance_posture(self, client_id: str) -> ComplianceRisk:
        """Get compliance risk assessment for a specific client"""
        self.log(f"Assessing compliance posture for client {client_id}")
        
        # Get client invoices from database
        invoices = self.db.get_all_invoices()
        client_invoices = [i for i in invoices if i.get("vendor_name") == client_id or i.get("buyer_name") == client_id]
        
        reasons = []
        actions = []
        affected_invoice_ids = []
        risk_score = 0
        
        # Check for issues
        for inv in client_invoices:
            invoice_issues = self._analyze_invoice_risks(inv)
            if invoice_issues:
                reasons.extend(invoice_issues["reasons"])
                actions.extend(invoice_issues["actions"])
                affected_invoice_ids.append(inv.get("invoice_number", "unknown"))
                risk_score += invoice_issues["score_impact"]
        
        # Check deadline proximity
        deadline_risk = self._check_deadline_risks()
        if deadline_risk:
            reasons.extend(deadline_risk["reasons"])
            actions.extend(deadline_risk["actions"])
            risk_score += deadline_risk["score_impact"]
        
        # Determine risk level
        risk_score = min(risk_score, 100)
        if risk_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        self.log(f"Client {client_id} risk level: {risk_level.value} (score: {risk_score})")
        
        return ComplianceRisk(
            risk_level=risk_level,
            risk_score=risk_score,
            reasons=list(set(reasons))[:5],  # Top 5 unique reasons
            suggested_actions=list(set(actions))[:5],
            affected_invoices=affected_invoice_ids[:10],
            deadline=self._get_next_deadline()
        )
    
    def get_urgent_items(self, deadline_days: int = 7) -> List[UrgentWorkItem]:
        """Get items requiring immediate attention"""
        self.log(f"Scanning for urgent items (deadline within {deadline_days} days)")
        
        urgent_items = []
        invoices = self.db.get_all_invoices()
        
        today = date.today()
        cutoff_date = today + timedelta(days=deadline_days)
        
        # Check for invoices with issues
        for inv in invoices:
            # Check tax validation issues
            if inv.get("errors") and len(inv.get("errors", [])) > 0:
                urgent_items.append(UrgentWorkItem(
                    id=f"tax-{inv.get('invoice_number', 'unknown')}",
                    type=WorkItemType.TAX_MISMATCH,
                    client_name=inv.get("vendor_name", "Unknown Vendor"),
                    title=f"Tax validation issue on invoice {inv.get('invoice_number')}",
                    description=f"Invoice has {len(inv.get('errors', []))} validation errors that need resolution",
                    reason="Tax mismatches will cause GSTR filing rejection",
                    priority_score=70,
                    suggested_action="Review and correct tax calculations or contact vendor for revised invoice",
                    invoice_ids=[inv.get("invoice_number", "")]
                ))
            
            # Check for missing GSTIN
            if not inv.get("vendor_gstin"):
                urgent_items.append(UrgentWorkItem(
                    id=f"gstin-{inv.get('invoice_number', 'unknown')}",
                    type=WorkItemType.MISSING_DATA,
                    client_name=inv.get("vendor_name", "Unknown Vendor"),
                    title=f"Missing GSTIN on invoice {inv.get('invoice_number')}",
                    description="Invoice is missing vendor GSTIN, cannot claim ITC",
                    reason="ITC claim will be rejected without valid GSTIN",
                    priority_score=80,
                    suggested_action="Request vendor to provide valid GSTIN or obtain corrected invoice",
                    invoice_ids=[inv.get("invoice_number", "")]
                ))
            
            # Check for due date approaching
            due_date_str = inv.get("due_date")
            if due_date_str:
                try:
                    if isinstance(due_date_str, str):
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                    else:
                        due_date = due_date_str
                    
                    if due_date <= cutoff_date and due_date >= today:
                        days_until = (due_date - today).days
                        urgent_items.append(UrgentWorkItem(
                            id=f"due-{inv.get('invoice_number', 'unknown')}",
                            type=WorkItemType.DEADLINE_RISK,
                            client_name=inv.get("vendor_name", "Unknown Vendor"),
                            title=f"Payment due in {days_until} days",
                            description=f"Invoice {inv.get('invoice_number')} for ₹{inv.get('total_amount', 0):,.2f} due on {due_date}",
                            reason="Late payment may affect vendor relationships and credit terms",
                            priority_score=60 + (7 - days_until) * 5,
                            deadline=due_date,
                            suggested_action="Schedule payment or communicate delay to vendor",
                            invoice_ids=[inv.get("invoice_number", "")]
                        ))
                except (ValueError, TypeError):
                    pass
        
        # Add GSTR deadline warnings
        gstr_urgents = self._get_gstr_deadline_urgents()
        urgent_items.extend(gstr_urgents)
        
        # Sort by priority
        urgent_items.sort(key=lambda x: x.priority_score, reverse=True)
        
        self.log(f"Found {len(urgent_items)} urgent items")
        return urgent_items[:20]  # Return top 20
    
    def predict_gstr_issues(self) -> List[Dict[str, Any]]:
        """Predict potential issues with upcoming GSTR filings"""
        self.log("Predicting GSTR filing issues")
        
        issues = []
        invoices = self.db.get_all_invoices()
        
        # Aggregate by month for current period
        current_month = date.today().month
        current_year = date.today().year
        
        monthly_invoices = []
        for inv in invoices:
            inv_date = inv.get("invoice_date")
            if inv_date:
                try:
                    if isinstance(inv_date, str):
                        parsed_date = datetime.strptime(inv_date, "%Y-%m-%d").date()
                    else:
                        parsed_date = inv_date
                    
                    if parsed_date.month == current_month and parsed_date.year == current_year:
                        monthly_invoices.append(inv)
                except (ValueError, TypeError):
                    pass
        
        # Check for common issues
        missing_gstin_count = sum(1 for i in monthly_invoices if not i.get("vendor_gstin"))
        if missing_gstin_count > 0:
            issues.append({
                "type": "missing_gstin",
                "severity": "high" if missing_gstin_count > 5 else "medium",
                "message": f"{missing_gstin_count} invoices missing GSTIN - ITC claim at risk",
                "affected_count": missing_gstin_count
            })
        
        # Check tax calculation issues
        tax_issue_count = sum(1 for i in monthly_invoices if i.get("errors"))
        if tax_issue_count > 0:
            issues.append({
                "type": "tax_mismatch",
                "severity": "high",
                "message": f"{tax_issue_count} invoices with tax calculation issues",
                "affected_count": tax_issue_count
            })
        
        # Check for potential reconciliation gaps
        total_invoices = len(monthly_invoices)
        if total_invoices < 10:
            issues.append({
                "type": "low_volume",
                "severity": "info",
                "message": f"Only {total_invoices} invoices for current period - verify completeness",
                "affected_count": total_invoices
            })
        
        self.log(f"Predicted {len(issues)} potential GSTR issues")
        return issues
    
    def generate_risk_summary(self) -> FirmRiskDashboard:
        """Generate firm-level risk dashboard"""
        self.log("Generating firm-wide risk summary")
        
        invoices = self.db.get_all_invoices()
        
        # Get unique "clients" (using vendor names as proxy)
        clients = set(inv.get("vendor_name", "Unknown") for inv in invoices)
        total_clients = len(clients)
        
        # Count risk levels
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        
        for client in clients:
            posture = self.get_client_compliance_posture(client)
            if posture.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                high_risk += 1
            elif posture.risk_level == RiskLevel.MEDIUM:
                medium_risk += 1
            else:
                low_risk += 1
        
        # Get urgent items count
        urgent_items = self.get_urgent_items()
        
        # Calculate overall health
        if total_clients > 0:
            health_score = int(100 - (high_risk * 30 + medium_risk * 15) / total_clients)
        else:
            health_score = 100
        health_score = max(0, min(100, health_score))
        
        # Determine trend (simplified)
        if high_risk > total_clients * 0.3:
            trend = "worsening"
        elif high_risk < total_clients * 0.1:
            trend = "improving"
        else:
            trend = "stable"
        
        dashboard = FirmRiskDashboard(
            total_clients=total_clients,
            high_risk_clients=high_risk,
            medium_risk_clients=medium_risk,
            low_risk_clients=low_risk,
            urgent_items_count=len(urgent_items),
            upcoming_deadlines=self._count_upcoming_deadlines(),
            overall_health_score=health_score,
            risk_trend=trend
        )
        
        self.log(f"Firm health score: {health_score}, trend: {trend}")
        return dashboard
    
    def _analyze_invoice_risks(self, invoice: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze risks for a single invoice"""
        reasons = []
        actions = []
        score_impact = 0
        
        # Missing GSTIN
        if not invoice.get("vendor_gstin"):
            reasons.append("Missing vendor GSTIN - ITC cannot be claimed")
            actions.append("Request GSTIN from vendor")
            score_impact += 20
        
        # Validation errors
        errors = invoice.get("errors", [])
        if errors:
            reasons.append(f"{len(errors)} validation errors on invoice")
            actions.append("Review and correct invoice errors")
            score_impact += 15 * len(errors)
        
        # Check tax calculation (simplified)
        total = invoice.get("total_amount", 0)
        tax = invoice.get("total_tax", 0)
        if total > 0 and tax > 0:
            effective_rate = (tax / (total - tax)) * 100 if total != tax else 0
            if effective_rate not in [0, 5, 12, 18, 28]:
                reasons.append(f"Non-standard tax rate detected ({effective_rate:.1f}%)")
                actions.append("Verify tax rate matches GST slab")
                score_impact += 10
        
        if reasons:
            return {
                "reasons": reasons,
                "actions": actions,
                "score_impact": min(score_impact, 50)
            }
        return None
    
    def _check_deadline_risks(self) -> Optional[Dict[str, Any]]:
        """Check for upcoming deadline risks"""
        today = date.today()
        day = today.day
        
        reasons = []
        actions = []
        score_impact = 0
        
        # GSTR-1 deadline approaching
        if day <= self.GSTR1_DEADLINE and day >= self.GSTR1_DEADLINE - 3:
            reasons.append(f"GSTR-1 deadline in {self.GSTR1_DEADLINE - day} days")
            actions.append("Finalize sales invoice data for GSTR-1")
            score_impact += 25
        
        # GSTR-3B deadline approaching
        if day <= self.GSTR3B_DEADLINE and day >= self.GSTR3B_DEADLINE - 3:
            reasons.append(f"GSTR-3B deadline in {self.GSTR3B_DEADLINE - day} days")
            actions.append("Complete purchase reconciliation for GSTR-3B")
            score_impact += 25
        
        if reasons:
            return {
                "reasons": reasons,
                "actions": actions,
                "score_impact": score_impact
            }
        return None
    
    def _get_next_deadline(self) -> date:
        """Get the next GST filing deadline"""
        today = date.today()
        day = today.day
        
        if day < self.GSTR1_DEADLINE:
            return date(today.year, today.month, self.GSTR1_DEADLINE)
        elif day < self.GSTR3B_DEADLINE:
            return date(today.year, today.month, self.GSTR3B_DEADLINE)
        else:
            # Next month GSTR-1
            if today.month == 12:
                return date(today.year + 1, 1, self.GSTR1_DEADLINE)
            return date(today.year, today.month + 1, self.GSTR1_DEADLINE)
    
    def _get_gstr_deadline_urgents(self) -> List[UrgentWorkItem]:
        """Generate urgent items for GSTR deadlines"""
        urgents = []
        today = date.today()
        day = today.day
        
        if day >= self.GSTR1_DEADLINE - 3 and day < self.GSTR1_DEADLINE:
            urgents.append(UrgentWorkItem(
                id="gstr1-deadline",
                type=WorkItemType.DEADLINE_RISK,
                client_name="All Clients",
                title=f"GSTR-1 deadline in {self.GSTR1_DEADLINE - day} days",
                description="GSTR-1 filing deadline is approaching for all clients",
                reason="Late filing attracts penalties and affects client compliance rating",
                priority_score=90,
                deadline=date(today.year, today.month, self.GSTR1_DEADLINE),
                suggested_action="Verify all sales invoices are recorded and reconciled"
            ))
        
        if day >= self.GSTR3B_DEADLINE - 3 and day < self.GSTR3B_DEADLINE:
            urgents.append(UrgentWorkItem(
                id="gstr3b-deadline",
                type=WorkItemType.DEADLINE_RISK,
                client_name="All Clients",
                title=f"GSTR-3B deadline in {self.GSTR3B_DEADLINE - day} days",
                description="GSTR-3B filing deadline is approaching for all clients",
                reason="Late GSTR-3B filing blocks ITC claims and attracts penalties",
                priority_score=95,
                deadline=date(today.year, today.month, self.GSTR3B_DEADLINE),
                suggested_action="Complete ITC reconciliation and tax liability calculation"
            ))
        
        return urgents
    
    def _count_upcoming_deadlines(self, days: int = 7) -> int:
        """Count deadlines in the next N days"""
        today = date.today()
        count = 0
        
        for d in range(1, days + 1):
            check_date = today + timedelta(days=d)
            if check_date.day == self.GSTR1_DEADLINE or check_date.day == self.GSTR3B_DEADLINE:
                count += 1
        
        return count


# Singleton
_compliance_agent: Optional[ComplianceRiskAgent] = None


def get_compliance_risk_agent() -> ComplianceRiskAgent:
    """Get compliance risk agent instance"""
    global _compliance_agent
    if _compliance_agent is None:
        _compliance_agent = ComplianceRiskAgent()
    return _compliance_agent
