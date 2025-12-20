"""
Client Workflow Agent
Manages workflow state across all clients for month-end close tracking
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging

from .base_agent import BaseAgent
from ..database.db import get_db
from ..models.workflow import (
    MonthEndPhase,
    ClientWorkflowStatus,
    ComplianceRisk,
    RiskLevel
)

logger = logging.getLogger(__name__)


class ClientWorkflowAgent(BaseAgent):
    """
    Manages workflow state across all clients.
    - Tracks month-end close progress per client
    - Identifies bottlenecks and lagging clients
    - Proposes work prioritization
    """
    
    agent_name = "client_workflow"
    agent_version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
    
    def get_system_prompt(self) -> str:
        return """You are a workflow management agent for CA firms.
Your job is to track month-end close progress across all clients,
identify bottlenecks and lagging workflows, and prioritize work.
Focus on:
- Tracking where each client is in the month-end process
- Identifying clients that are behind schedule
- Suggesting work prioritization
- Predicting workload distribution"""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow status request"""
        action = input_data.get("action", "status")
        
        if action == "status":
            self.log("Fetching month-end status for all clients")
            statuses = self.get_month_end_status()
            return {"statuses": [s.model_dump() for s in statuses]}
        elif action == "prioritize":
            self.log("Generating prioritized work queue")
            queue = self.get_prioritized_work_queue()
            return {"work_queue": queue}
        elif action == "bottlenecks":
            self.log("Identifying workflow bottlenecks")
            bottlenecks = self.identify_bottlenecks()
            return {"bottlenecks": bottlenecks}
        else:
            return {"error": f"Unknown action: {action}"}
    
    def get_month_end_status(self) -> List[ClientWorkflowStatus]:
        """Get month-end workflow status for all clients"""
        self.log("Calculating month-end status for all clients")
        
        invoices = self.db.get_all_invoices()
        
        # Group invoices by client (using vendor_name as proxy)
        clients: Dict[str, List[Dict]] = {}
        for inv in invoices:
            vendor = inv.get("vendor_name", "Unknown")
            if vendor not in clients:
                clients[vendor] = []
            clients[vendor].append(inv)
        
        statuses = []
        for client_name, client_invoices in clients.items():
            status = self._calculate_client_status(client_name, client_invoices)
            statuses.append(status)
        
        # Sort by risk level (highest first), then by progress (lowest first)
        risk_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 3}
        statuses.sort(key=lambda s: (risk_order.get(s.risk.risk_level, 4), s.progress_percent))
        
        self.log(f"Generated status for {len(statuses)} clients")
        return statuses
    
    def get_prioritized_work_queue(self) -> List[Dict[str, Any]]:
        """Get prioritized list of work items across all clients"""
        self.log("Building prioritized work queue")
        
        work_items = []
        statuses = self.get_month_end_status()
        
        for status in statuses:
            # Add work items based on client status
            if status.phase == MonthEndPhase.NOT_STARTED:
                work_items.append({
                    "client": status.client_name,
                    "task": "Start data collection",
                    "priority": 90 if status.risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else 50,
                    "phase": status.phase.value,
                    "reason": "Month-end work not started"
                })
            elif status.phase == MonthEndPhase.DATA_COLLECTION:
                work_items.append({
                    "client": status.client_name,
                    "task": "Complete invoice collection and entry",
                    "priority": 70 + (100 - status.progress_percent) // 5,
                    "phase": status.phase.value,
                    "reason": f"Data collection {status.progress_percent}% complete"
                })
            elif status.phase == MonthEndPhase.RECONCILIATION:
                work_items.append({
                    "client": status.client_name,
                    "task": "Complete reconciliation",
                    "priority": 80 + (100 - status.progress_percent) // 4,
                    "phase": status.phase.value,
                    "reason": f"Reconciliation {status.progress_percent}% complete"
                })
            elif status.phase == MonthEndPhase.REVIEW:
                work_items.append({
                    "client": status.client_name,
                    "task": "Review and approve for filing",
                    "priority": 85,
                    "phase": status.phase.value,
                    "reason": "Ready for review"
                })
            
            # Add pending items
            for item in status.pending_items:
                work_items.append({
                    "client": status.client_name,
                    "task": item,
                    "priority": 60,
                    "phase": status.phase.value,
                    "reason": "Pending item"
                })
        
        # Sort by priority (highest first)
        work_items.sort(key=lambda x: x["priority"], reverse=True)
        
        self.log(f"Generated {len(work_items)} prioritized work items")
        return work_items[:30]  # Return top 30
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify workflow bottlenecks across the firm"""
        self.log("Analyzing for workflow bottlenecks")
        
        bottlenecks = []
        statuses = self.get_month_end_status()
        
        # Count clients at each phase
        phase_counts: Dict[str, int] = {}
        for status in statuses:
            phase = status.phase.value
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        total_clients = len(statuses)
        if total_clients == 0:
            return []
        
        # Check for phase bottlenecks (too many clients stuck at same phase)
        for phase, count in phase_counts.items():
            if count > total_clients * 0.4 and phase not in ["complete", "filing_ready"]:
                bottlenecks.append({
                    "type": "phase_congestion",
                    "phase": phase,
                    "severity": "high" if count > total_clients * 0.6 else "medium",
                    "message": f"{count} clients ({count * 100 // total_clients}%) stuck at {phase} phase",
                    "suggestion": f"Focus team resources on moving clients through {phase}"
                })
        
        # Check for high-risk clients blocking
        high_risk_count = sum(1 for s in statuses if s.risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        if high_risk_count > total_clients * 0.3:
            bottlenecks.append({
                "type": "risk_accumulation",
                "severity": "critical",
                "message": f"{high_risk_count} clients at high/critical risk - firm-wide compliance in jeopardy",
                "suggestion": "Immediate escalation to partner level; consider additional resources"
            })
        
        # Check for slow progressors
        slow_clients = [s for s in statuses if s.progress_percent < 30 and s.phase != MonthEndPhase.NOT_STARTED]
        if slow_clients:
            for client in slow_clients[:5]:
                bottlenecks.append({
                    "type": "slow_progress",
                    "client": client.client_name,
                    "severity": "medium",
                    "message": f"{client.client_name} only {client.progress_percent}% through {client.phase.value}",
                    "suggestion": f"Check for blockers with {client.client_name}"
                })
        
        # Check time-based bottleneck (late in month)
        today = date.today()
        if today.day > 20:
            incomplete = sum(1 for s in statuses if s.phase not in [MonthEndPhase.COMPLETE, MonthEndPhase.FILING_READY])
            if incomplete > 0:
                bottlenecks.append({
                    "type": "deadline_pressure",
                    "severity": "critical" if today.day > 25 else "high",
                    "message": f"{incomplete} clients not filing-ready with month-end approaching",
                    "suggestion": "Prioritize filing-critical tasks; consider deadline extensions if available"
                })
        
        self.log(f"Identified {len(bottlenecks)} bottlenecks")
        return bottlenecks
    
    def _calculate_client_status(self, client_name: str, invoices: List[Dict]) -> ClientWorkflowStatus:
        """Calculate workflow status for a single client"""
        
        # Determine phase based on invoice states
        total = len(invoices)
        if total == 0:
            phase = MonthEndPhase.NOT_STARTED
            progress = 0
        else:
            processed = sum(1 for i in invoices if i.get("status") == "processed")
            needs_review = sum(1 for i in invoices if i.get("status") == "needs_review")
            with_errors = sum(1 for i in invoices if i.get("errors") and len(i.get("errors", [])) > 0)
            
            processed_ratio = processed / total if total > 0 else 0
            
            if processed_ratio >= 0.95 and needs_review == 0:
                phase = MonthEndPhase.FILING_READY
                progress = 100
            elif processed_ratio >= 0.8:
                phase = MonthEndPhase.REVIEW
                progress = 80 + int(processed_ratio * 20)
            elif processed_ratio >= 0.5:
                phase = MonthEndPhase.RECONCILIATION
                progress = 50 + int(processed_ratio * 30)
            elif processed_ratio > 0:
                phase = MonthEndPhase.DATA_COLLECTION
                progress = int(processed_ratio * 50)
            else:
                phase = MonthEndPhase.DATA_COLLECTION
                progress = 10  # Started but nothing processed yet
        
        # Calculate risk
        risk = self._calculate_client_risk(client_name, invoices)
        
        # Identify pending items
        pending = []
        for inv in invoices:
            if inv.get("status") == "needs_review":
                pending.append(f"Review invoice {inv.get('invoice_number', 'unknown')}")
            if inv.get("errors"):
                pending.append(f"Fix errors on invoice {inv.get('invoice_number', 'unknown')}")
            if not inv.get("vendor_gstin"):
                pending.append(f"Get GSTIN for {inv.get('invoice_number', 'unknown')}")
        
        return ClientWorkflowStatus(
            client_id=client_name.lower().replace(" ", "_"),
            client_name=client_name,
            phase=phase,
            progress_percent=progress,
            risk=risk,
            pending_items=pending[:5],  # Top 5 pending items
            notes=f"{len(invoices)} invoices this period"
        )
    
    def _calculate_client_risk(self, client_name: str, invoices: List[Dict]) -> ComplianceRisk:
        """Calculate compliance risk for a client based on their invoices"""
        
        reasons = []
        actions = []
        risk_score = 0
        affected = []
        
        for inv in invoices:
            # Check for missing GSTIN
            if not inv.get("vendor_gstin"):
                reasons.append("Missing GSTIN on invoices")
                actions.append("Collect vendor GSTIN")
                risk_score += 15
                affected.append(inv.get("invoice_number", ""))
            
            # Check for errors
            if inv.get("errors"):
                error_count = len(inv.get("errors", []))
                reasons.append(f"Validation errors on invoices")
                actions.append("Review and correct validation errors")
                risk_score += 10 * error_count
                affected.append(inv.get("invoice_number", ""))
            
            # Check for overdue
            due_date = inv.get("due_date")
            if due_date:
                try:
                    if isinstance(due_date, str):
                        due = datetime.strptime(due_date, "%Y-%m-%d").date()
                    else:
                        due = due_date
                    
                    if due < date.today():
                        reasons.append("Overdue invoices")
                        actions.append("Process overdue items immediately")
                        risk_score += 20
                except (ValueError, TypeError):
                    pass
        
        # Normalize score
        risk_score = min(risk_score, 100)
        
        # Determine risk level
        if risk_score >= 70:
            level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            level = RiskLevel.HIGH
        elif risk_score >= 25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        return ComplianceRisk(
            risk_level=level,
            risk_score=risk_score,
            reasons=list(set(reasons))[:3],
            suggested_actions=list(set(actions))[:3],
            affected_invoices=list(set(affected))[:5]
        )


# Singleton
_workflow_agent: Optional[ClientWorkflowAgent] = None


def get_client_workflow_agent() -> ClientWorkflowAgent:
    """Get client workflow agent instance"""
    global _workflow_agent
    if _workflow_agent is None:
        _workflow_agent = ClientWorkflowAgent()
    return _workflow_agent
