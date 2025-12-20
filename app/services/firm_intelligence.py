"""
Firm Intelligence Service
Aggregates all data sources into firm-level operational intelligence
Hero Feature: Month-End Close Autopilot
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

from ..database.db import get_db
from ..services.llm_service import get_llm_service
from ..agents.compliance_risk_agent import get_compliance_risk_agent
from ..agents.client_workflow_agent import get_client_workflow_agent
from ..models.workflow import (
    MonthEndDashboard,
    FirmRiskDashboard,
    DayBriefing,
    UrgentWorkItem,
    ClientWorkflowStatus,
    RiskLevel
)

logger = logging.getLogger(__name__)


class FirmIntelligenceService:
    """
    Aggregates all data sources into firm-level operational intelligence.
    Hero feature: "Month-End Close Autopilot"
    """
    
    def __init__(self):
        self.db = get_db()
        self.llm = get_llm_service()
        self.compliance_agent = get_compliance_risk_agent()
        self.workflow_agent = get_client_workflow_agent()
        self._demo_data = None
    
    def _load_demo_data(self) -> dict:
        """Load demo data from sample_clients.json for hackathon presentation"""
        if self._demo_data is None:
            import json
            from pathlib import Path
            demo_file = Path(__file__).parent.parent.parent / "data" / "sample_clients.json"
            if demo_file.exists():
                with open(demo_file, 'r') as f:
                    self._demo_data = json.load(f)
                logger.info("Loaded demo data from sample_clients.json")
            else:
                self._demo_data = {}
                logger.warning(f"Demo data file not found: {demo_file}")
        return self._demo_data
    
    def get_month_end_autopilot(self, use_demo: bool = True) -> MonthEndDashboard:
        """
        The hero view: Month-End Close Autopilot
        Aggregates all insights into a single actionable dashboard
        
        Args:
            use_demo: If True, use pre-loaded demo data for compelling presentation
        """
        logger.info("Generating Month-End Autopilot dashboard")
        
        # Get current month
        today = date.today()
        current_month = today.strftime("%B %Y")
        
        # Use demo data if available and requested
        demo_data = self._load_demo_data()
        if use_demo and demo_data.get("demo_scenario"):
            return self._build_demo_dashboard(demo_data, current_month)
        
        # Otherwise use real data from agents
        # Get client statuses from workflow agent
        clients_status = self.workflow_agent.get_month_end_status()
        
        # Get urgent items from compliance agent
        urgent_items = self.compliance_agent.get_urgent_items(deadline_days=7)
        
        # Get firm risk summary
        risk_summary = self.compliance_agent.generate_risk_summary()
        
        # Calculate overall progress
        if clients_status:
            total_progress = sum(c.progress_percent for c in clients_status)
            overall_progress = total_progress // len(clients_status)
        else:
            overall_progress = 0
        
        # Identify bottlenecks
        bottlenecks = self.workflow_agent.identify_bottlenecks()
        bottleneck_msgs = [b["message"] for b in bottlenecks[:5]]
        
        # Generate AI briefing
        ai_briefing = self._generate_ai_briefing(
            clients_status, urgent_items, risk_summary, bottlenecks
        )
        
        dashboard = MonthEndDashboard(
            current_month=current_month,
            overall_progress=overall_progress,
            clients_status=clients_status,
            urgent_items=urgent_items,
            risk_summary=risk_summary,
            ai_briefing=ai_briefing,
            bottlenecks=bottleneck_msgs
        )
        
        logger.info(f"Autopilot dashboard: {overall_progress}% overall, {len(urgent_items)} urgent items")
        return dashboard
    
    def _build_demo_dashboard(self, demo_data: dict, current_month: str) -> MonthEndDashboard:
        """Build a compelling demo dashboard from sample_clients.json"""
        scenario = demo_data["demo_scenario"]
        clients = demo_data["clients"]
        
        # Build client statuses
        clients_status = []
        for client in clients:
            status_data = scenario["client_statuses"].get(client["client_id"], {})
            from ..models.workflow import ComplianceRisk
            
            risk = ComplianceRisk(
                client_id=client["client_id"],
                risk_level=RiskLevel(status_data.get("risk_level", "low")),
                score=100 - (20 * ["low", "medium", "high", "critical"].index(status_data.get("risk_level", "low"))),
                reasons=[status_data.get("notes", "")],
                recommendations=[]
            )
            
            clients_status.append(ClientWorkflowStatus(
                client_id=client["client_id"],
                client_name=client["client_name"],
                phase=status_data.get("phase", "not_started"),
                progress_percent=status_data.get("progress", 0),
                pending_items=[],
                completed_items=[],
                assigned_to=None,
                risk=risk,
                gstin=client.get("gstin")
            ))
        
        # Build urgent items
        urgent_items = []
        for item in scenario.get("urgent_items", []):
            # Find client name
            client_name = next(
                (c["client_name"] for c in clients if c["client_id"] == item["client_id"]),
                "Unknown"
            )
            from ..models.workflow import WorkItemType
            urgent_items.append(UrgentWorkItem(
                id=item["id"],
                type=WorkItemType.DEADLINE_RISK,
                client_name=client_name,
                title=item["title"],
                description=item["description"],
                reason=f"Deadline on {item.get('deadline', 'soon')} - requires immediate attention",
                priority_score=item["priority_score"],
                deadline=item.get("deadline"),
                suggested_action=item["suggested_action"]
            ))
        
        # Build risk summary
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for status in scenario["client_statuses"].values():
            level = status.get("risk_level", "low")
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        risk_summary = FirmRiskDashboard(
            total_clients=len(clients),
            high_risk_clients=risk_counts["high"] + risk_counts["critical"],
            medium_risk_clients=risk_counts["medium"],
            low_risk_clients=risk_counts["low"],
            overall_health_score=88,  # Pre-calculated for demo
            top_risks=[]
        )
        
        # Calculate progress
        total_progress = sum(s.get("progress", 0) for s in scenario["client_statuses"].values())
        overall_progress = total_progress // len(scenario["client_statuses"]) if scenario["client_statuses"] else 0
        
        briefing = scenario.get("briefing", {})
        
        return MonthEndDashboard(
            current_month=current_month,
            overall_progress=overall_progress,
            clients_status=clients_status,
            urgent_items=urgent_items,
            risk_summary=risk_summary,
            ai_briefing=briefing.get("headline", ""),
            bottlenecks=scenario.get("bottlenecks", [])
        )
    
    def get_attention_needed_now(self) -> List[UrgentWorkItem]:
        """
        What MUST be done today to avoid compliance issues
        Filters to the most critical items only
        """
        logger.info("Getting attention-needed-now items")
        
        all_urgent = self.compliance_agent.get_urgent_items(deadline_days=3)
        
        # Filter to highest priority only
        critical_items = [
            item for item in all_urgent 
            if item.priority_score >= 70
        ][:10]
        
        logger.info(f"Found {len(critical_items)} critical attention items")
        return critical_items
    
    def get_firm_intelligence(self) -> Dict[str, Any]:
        """
        Complete firm intelligence summary
        Used for the Ops Intelligence dashboard
        """
        logger.info("Generating complete firm intelligence")
        
        # Get all components
        month_end = self.get_month_end_autopilot()
        urgent = self.get_attention_needed_now()
        work_queue = self.workflow_agent.get_prioritized_work_queue()
        bottlenecks = self.workflow_agent.identify_bottlenecks()
        gstr_issues = self.compliance_agent.predict_gstr_issues()
        
        return {
            "month_end_dashboard": month_end.model_dump(),
            "urgent_actions": [u.model_dump() for u in urgent],
            "work_queue": work_queue[:10],
            "bottlenecks": bottlenecks,
            "gstr_predictions": gstr_issues,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_day_briefing(self) -> DayBriefing:
        """
        Generate AI-powered daily briefing for the firm
        """
        logger.info("Generating daily briefing")
        
        # Gather data for briefing
        month_end = self.get_month_end_autopilot()
        urgent = self.get_attention_needed_now()
        bottlenecks = self.workflow_agent.identify_bottlenecks()
        
        # Build context for LLM
        context = self._build_briefing_context(month_end, urgent, bottlenecks)
        
        # Generate briefing with LLM
        try:
            full_briefing = self._generate_llm_briefing(context)
        except Exception as e:
            logger.warning(f"LLM briefing failed, using template: {e}")
            full_briefing = self._generate_template_briefing(context)
        
        # Extract key points
        key_points = []
        urgent_actions = []
        risks_to_watch = []
        positive_notes = []
        
        # Parse from month_end data
        if month_end.urgent_items:
            urgent_actions = [item.title for item in month_end.urgent_items[:3]]
        
        if bottlenecks:
            risks_to_watch = [b["message"] for b in bottlenecks[:3]]
        
        # Check for positive items
        high_progress_clients = [
            c.client_name for c in month_end.clients_status 
            if c.progress_percent >= 80
        ]
        if high_progress_clients:
            positive_notes.append(f"{len(high_progress_clients)} clients on track for filing")
        
        if month_end.risk_summary.low_risk_clients > 0:
            positive_notes.append(f"{month_end.risk_summary.low_risk_clients} clients at low risk")
        
        # Generate headline
        if month_end.risk_summary.high_risk_clients > month_end.risk_summary.total_clients // 2:
            headline = f"⚠️ Attention needed: {month_end.risk_summary.high_risk_clients} clients at elevated risk"
        elif len(urgent) > 5:
            headline = f"📋 {len(urgent)} items need attention today"
        else:
            headline = f"✅ Firm health: {month_end.risk_summary.overall_health_score}% - {month_end.overall_progress}% month-end progress"
        
        key_points = [
            f"Overall month-end progress: {month_end.overall_progress}%",
            f"Firm health score: {month_end.risk_summary.overall_health_score}/100",
            f"Clients tracked: {month_end.risk_summary.total_clients}"
        ]
        
        return DayBriefing(
            headline=headline,
            key_points=key_points,
            urgent_actions=urgent_actions,
            risks_to_watch=risks_to_watch,
            positive_notes=positive_notes,
            full_briefing=full_briefing
        )
    
    def _generate_ai_briefing(
        self,
        clients: List[ClientWorkflowStatus],
        urgent: List[UrgentWorkItem],
        risk: FirmRiskDashboard,
        bottlenecks: List[Dict]
    ) -> str:
        """Generate a short AI briefing for the dashboard"""
        
        # Build a simple briefing without LLM call for speed
        parts = []
        
        # Status summary
        if risk.overall_health_score >= 80:
            parts.append(f"Firm is in good health ({risk.overall_health_score}%).")
        elif risk.overall_health_score >= 50:
            parts.append(f"Firm health needs attention ({risk.overall_health_score}%).")
        else:
            parts.append(f"⚠️ Firm health critical ({risk.overall_health_score}%).")
        
        # Urgent summary
        if urgent:
            parts.append(f"{len(urgent)} items need immediate attention.")
        
        # Risk summary
        if risk.high_risk_clients > 0:
            parts.append(f"{risk.high_risk_clients} clients at high risk.")
        
        # Bottleneck summary
        if bottlenecks:
            top_bottleneck = bottlenecks[0]["message"]
            parts.append(f"Key bottleneck: {top_bottleneck}")
        
        return " ".join(parts)
    
    def _build_briefing_context(
        self,
        month_end: MonthEndDashboard,
        urgent: List[UrgentWorkItem],
        bottlenecks: List[Dict]
    ) -> Dict[str, Any]:
        """Build context dictionary for LLM briefing"""
        return {
            "date": date.today().isoformat(),
            "month": month_end.current_month,
            "overall_progress": month_end.overall_progress,
            "health_score": month_end.risk_summary.overall_health_score,
            "total_clients": month_end.risk_summary.total_clients,
            "high_risk_clients": month_end.risk_summary.high_risk_clients,
            "urgent_count": len(urgent),
            "top_urgents": [u.title for u in urgent[:5]],
            "bottlenecks": [b["message"] for b in bottlenecks[:3]]
        }
    
    def _generate_llm_briefing(self, context: Dict[str, Any]) -> str:
        """Generate briefing using LLM"""
        
        prompt = f"""Generate a concise daily briefing for a CA firm partner.

Context:
- Date: {context['date']}
- Period: {context['month']}
- Overall month-end progress: {context['overall_progress']}%
- Firm health score: {context['health_score']}/100
- Total clients: {context['total_clients']}
- High-risk clients: {context['high_risk_clients']}
- Urgent items: {context['urgent_count']}
- Top urgents: {', '.join(context['top_urgents'])}
- Key bottlenecks: {', '.join(context['bottlenecks'])}

Write a 3-4 sentence briefing that:
1. Summarizes the firm's current state
2. Highlights the most critical issue
3. Suggests a priority focus for today
Be direct and actionable. Use Indian accounting terminology."""

        response = self.llm.generate(prompt)
        return response.get("content", self._generate_template_briefing(context))
    
    def _generate_template_briefing(self, context: Dict[str, Any]) -> str:
        """Template-based briefing as fallback"""
        
        if context['high_risk_clients'] > context['total_clients'] // 2:
            status = f"⚠️ Alert: {context['high_risk_clients']} of {context['total_clients']} clients at high risk."
        elif context['health_score'] >= 70:
            status = f"Firm health is stable at {context['health_score']}%."
        else:
            status = f"Firm health score of {context['health_score']}% needs attention."
        
        progress = f"Month-end close is {context['overall_progress']}% complete across all clients."
        
        if context['urgent_count'] > 0:
            urgent = f"Top priority: {context['top_urgents'][0] if context['top_urgents'] else 'Review urgent items'}."
        else:
            urgent = "No critical items requiring immediate attention."
        
        return f"{status} {progress} {urgent}"


# Singleton
_firm_service: Optional[FirmIntelligenceService] = None


def get_firm_intelligence_service() -> FirmIntelligenceService:
    """Get firm intelligence service instance"""
    global _firm_service
    if _firm_service is None:
        _firm_service = FirmIntelligenceService()
    return _firm_service
