"""
Cash Flow Agent
Analyzes expenses and predicts cash flow
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict

from .base_agent import BaseAgent
from ..models.invoice import Invoice
from ..services.llm_service import LLMService


class CashFlowAgent(BaseAgent):
    """
    Agent for cash flow analysis and prediction
    
    Responsibilities:
    - Categorize expenses
    - Track spending by category
    - Predict future cash flow
    - Generate spending insights
    - Alert on budget issues
    """
    
    agent_name = "cashflow_agent"
    agent_version = "1.0.0"
    
    # Default expense categories
    CATEGORIES = [
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
        "Salaries & Wages",
        "Other"
    ]
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(llm_service)
        
        # In-memory storage for demo
        self.invoices: List[Invoice] = []
        self.monthly_totals: Dict[str, float] = defaultdict(float)
        self.category_totals: Dict[str, float] = defaultdict(float)
        self.budget_limits: Dict[str, float] = {}
    
    def get_system_prompt(self) -> str:
        return """You are a financial analyst agent specializing in cash flow analysis for SMEs.
Your job is to:
1. Categorize business expenses accurately
2. Track spending patterns
3. Predict future cash requirements
4. Identify cost-saving opportunities
5. Alert on unusual spending patterns

Be precise with numbers and provide actionable insights."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze invoice for cash flow impact
        
        Args:
            input_data: Dict with 'invoice' key containing Invoice data
            
        Returns:
            Cash flow analysis results
        """
        self.validate_input(input_data, ["invoice"])
        
        # Convert dict to Invoice if needed
        invoice_data = input_data["invoice"]
        if isinstance(invoice_data, dict):
            invoice = Invoice(**invoice_data)
        else:
            invoice = invoice_data
        
        self.log("Starting cash flow analysis")
        
        # Categorize the expense
        category = self._categorize_expense(invoice)
        invoice.expense_category = category
        
        # Add to tracking
        self._track_invoice(invoice)
        
        # Calculate metrics
        results = {
            "category": category,
            "amount": invoice.total_amount,
            "month": invoice.invoice_date.strftime("%Y-%m"),
            "monthly_summary": self._get_monthly_summary(),
            "category_breakdown": self._get_category_breakdown(),
            "predictions": self._predict_cash_flow(),
            "alerts": self._check_alerts(invoice),
            "insights": self._generate_insights(invoice)
        }
        
        self.log(f"Cash flow analysis complete. Category: {category}")
        
        return results
    
    def _categorize_expense(self, invoice: Invoice) -> str:
        """Categorize the invoice expense using AI or rules"""
        
        # Build context from invoice
        context = f"Vendor: {invoice.vendor_name}\n"
        if invoice.items:
            context += f"Items: {', '.join([i.description for i in invoice.items])}\n"
        
        # Try LLM categorization
        if self.llm.backend:
            try:
                category = self.llm.classify(
                    text=context,
                    categories=self.CATEGORIES,
                    context="Categorize this business expense for accounting"
                )
                return category
            except Exception as e:
                self.log(f"LLM categorization failed: {e}", level="warning")
        
        # Rule-based fallback
        return self._categorize_by_rules(invoice)
    
    def _categorize_by_rules(self, invoice: Invoice) -> str:
        """Rule-based expense categorization"""
        vendor_lower = invoice.vendor_name.lower()
        items_text = " ".join([i.description.lower() for i in invoice.items])
        combined = f"{vendor_lower} {items_text}"
        
        # Keyword mapping
        keywords = {
            "IT & Software": ["software", "cloud", "aws", "azure", "hosting", "domain", "tech", "computer"],
            "Office Supplies": ["stationery", "paper", "printer", "ink", "office", "desk"],
            "Travel & Transport": ["travel", "flight", "hotel", "cab", "uber", "ola", "fuel", "petrol"],
            "Marketing & Advertising": ["marketing", "ads", "advertising", "promotion", "media"],
            "Professional Services": ["consulting", "legal", "audit", "accountant", "lawyer"],
            "Utilities": ["electricity", "water", "phone", "internet", "broadband"],
            "Rent & Lease": ["rent", "lease", "property"],
            "Equipment": ["machine", "equipment", "hardware"],
            "Raw Materials": ["raw", "material", "component", "part"],
        }
        
        for category, kws in keywords.items():
            if any(kw in combined for kw in kws):
                return category
        
        return "Other"
    
    def _track_invoice(self, invoice: Invoice):
        """Add invoice to tracking"""
        self.invoices.append(invoice)
        
        month_key = invoice.invoice_date.strftime("%Y-%m")
        self.monthly_totals[month_key] += invoice.total_amount
        
        category = invoice.expense_category or "Other"
        self.category_totals[category] += invoice.total_amount
    
    def _get_monthly_summary(self) -> Dict[str, Any]:
        """Get summary of monthly spending"""
        current_month = date.today().strftime("%Y-%m")
        current_total = self.monthly_totals.get(current_month, 0)
        
        # Calculate average of last 3 months
        months = sorted(self.monthly_totals.keys())[-3:]
        avg_monthly = sum(self.monthly_totals[m] for m in months) / len(months) if months else 0
        
        return {
            "current_month": current_month,
            "current_total": current_total,
            "average_monthly": avg_monthly,
            "trend": "up" if current_total > avg_monthly else "down",
            "all_months": dict(self.monthly_totals)
        }
    
    def _get_category_breakdown(self) -> Dict[str, Any]:
        """Get spending breakdown by category"""
        total = sum(self.category_totals.values())
        
        breakdown = {}
        for category, amount in self.category_totals.items():
            breakdown[category] = {
                "amount": amount,
                "percentage": (amount / total * 100) if total > 0 else 0
            }
        
        return {
            "total": total,
            "categories": breakdown,
            "top_category": max(self.category_totals.items(), key=lambda x: x[1])[0] if self.category_totals else None
        }
    
    def _predict_cash_flow(self) -> Dict[str, Any]:
        """Simple cash flow prediction based on historical data"""
        if len(self.monthly_totals) < 1:
            return {
                "next_month_estimate": 0,
                "confidence": "low",
                "note": "Insufficient data for prediction"
            }
        
        # Simple average-based prediction
        monthly_values = list(self.monthly_totals.values())
        avg = sum(monthly_values) / len(monthly_values)
        
        # Add 5% growth assumption
        next_month_estimate = avg * 1.05
        
        return {
            "next_month_estimate": round(next_month_estimate, 2),
            "confidence": "medium" if len(monthly_values) >= 3 else "low",
            "based_on_months": len(monthly_values),
            "monthly_average": round(avg, 2)
        }
    
    def _check_alerts(self, invoice: Invoice) -> List[Dict[str, Any]]:
        """Check for any spending alerts"""
        alerts = []
        
        # Large transaction alert
        if invoice.total_amount > 100000:  # ₹1 lakh
            alerts.append({
                "type": "large_transaction",
                "severity": "info",
                "message": f"Large transaction: ₹{invoice.total_amount:,.2f} from {invoice.vendor_name}"
            })
        
        # Budget exceeded (if set)
        category = invoice.expense_category or "Other"
        if category in self.budget_limits:
            if self.category_totals[category] > self.budget_limits[category]:
                alerts.append({
                    "type": "budget_exceeded",
                    "severity": "warning",
                    "message": f"Budget exceeded for {category}: ₹{self.category_totals[category]:,.2f} / ₹{self.budget_limits[category]:,.2f}"
                })
        
        # Unusual spending pattern
        category_avg = sum(self.category_totals.values()) / len(self.category_totals) if self.category_totals else 0
        if invoice.total_amount > category_avg * 3:
            alerts.append({
                "type": "unusual_spending",
                "severity": "info",
                "message": f"This transaction is 3x higher than average"
            })
        
        return alerts
    
    def _generate_insights(self, invoice: Invoice) -> List[str]:
        """Generate spending insights"""
        insights = []
        
        # Category insight
        category = invoice.expense_category or "Other"
        category_total = self.category_totals.get(category, 0)
        total_spending = sum(self.category_totals.values())
        
        if total_spending > 0:
            percentage = (category_total / total_spending) * 100
            insights.append(f"{category} accounts for {percentage:.1f}% of total spending")
        
        # Vendor frequency
        vendor_invoices = [i for i in self.invoices if i.vendor_name == invoice.vendor_name]
        if len(vendor_invoices) > 1:
            vendor_total = sum(i.total_amount for i in vendor_invoices)
            insights.append(f"Total spent with {invoice.vendor_name}: ₹{vendor_total:,.2f} across {len(vendor_invoices)} invoices")
        
        # Monthly trend
        monthly = self._get_monthly_summary()
        if monthly["trend"] == "up":
            insights.append("Monthly spending is trending upward")
        else:
            insights.append("Monthly spending is stable or decreasing")
        
        return insights
    
    def set_budget(self, category: str, limit: float):
        """Set budget limit for a category"""
        self.budget_limits[category] = limit
        self.log(f"Budget set for {category}: ₹{limit:,.2f}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data for dashboard display"""
        return {
            "monthly_summary": self._get_monthly_summary(),
            "category_breakdown": self._get_category_breakdown(),
            "predictions": self._predict_cash_flow(),
            "recent_invoices": [inv.model_dump() for inv in self.invoices[-10:]],
            "total_invoices": len(self.invoices),
            "budget_status": {
                cat: {
                    "spent": self.category_totals.get(cat, 0),
                    "limit": limit,
                    "remaining": limit - self.category_totals.get(cat, 0)
                }
                for cat, limit in self.budget_limits.items()
            }
        }
