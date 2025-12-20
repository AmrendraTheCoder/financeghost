"""
Vendor Intelligence Service
Smart vendor analysis and negotiation recommendations
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..database.db import get_db
from ..services.llm_service import get_llm_service


class VendorIntelligenceService:
    """Service for vendor spend analysis and negotiation recommendations"""
    
    def __init__(self):
        self.db = get_db()
        self.llm = get_llm_service()
    
    def get_vendor_spend_analysis(self) -> Dict[str, Any]:
        """
        Analyze spending patterns across all vendors
        
        Returns:
            Comprehensive vendor spend analysis
        """
        invoices = self.db.get_all_invoices(limit=1000)
        
        # Aggregate by vendor
        vendor_data = defaultdict(lambda: {
            'total_amount': 0,
            'invoice_count': 0,
            'invoices': [],
            'first_invoice': None,
            'last_invoice': None,
            'gstin': None,
            'categories': defaultdict(float)
        })
        
        for inv in invoices:
            vendor = inv.get('vendor_name', 'Unknown')
            amount = inv.get('total_amount', 0) or 0
            inv_date = inv.get('invoice_date')
            
            vendor_data[vendor]['total_amount'] += amount
            vendor_data[vendor]['invoice_count'] += 1
            vendor_data[vendor]['invoices'].append(inv)
            
            if not vendor_data[vendor]['gstin']:
                vendor_data[vendor]['gstin'] = inv.get('vendor_gstin')
            
            category = inv.get('expense_category', 'Other')
            vendor_data[vendor]['categories'][category] += amount
            
            if inv_date:
                if not vendor_data[vendor]['first_invoice'] or inv_date < vendor_data[vendor]['first_invoice']:
                    vendor_data[vendor]['first_invoice'] = inv_date
                if not vendor_data[vendor]['last_invoice'] or inv_date > vendor_data[vendor]['last_invoice']:
                    vendor_data[vendor]['last_invoice'] = inv_date
        
        # Sort by total spend
        sorted_vendors = sorted(
            vendor_data.items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        )
        
        # Calculate totals
        total_spend = sum(v['total_amount'] for _, v in sorted_vendors)
        
        # Build analysis
        vendor_analysis = []
        for vendor, data in sorted_vendors[:20]:  # Top 20 vendors
            percentage = (data['total_amount'] / total_spend * 100) if total_spend > 0 else 0
            avg_invoice = data['total_amount'] / data['invoice_count'] if data['invoice_count'] > 0 else 0
            
            vendor_analysis.append({
                'vendor_name': vendor,
                'gstin': data['gstin'],
                'total_spend': data['total_amount'],
                'percentage_of_total': round(percentage, 2),
                'invoice_count': data['invoice_count'],
                'average_invoice': round(avg_invoice, 2),
                'first_invoice': data['first_invoice'],
                'last_invoice': data['last_invoice'],
                'primary_category': max(data['categories'].items(), key=lambda x: x[1])[0] if data['categories'] else 'Unknown',
                'categories': dict(data['categories'])
            })
        
        return {
            'total_spend': total_spend,
            'total_vendors': len(vendor_data),
            'top_vendors': vendor_analysis,
            'concentration': self._calculate_concentration(sorted_vendors, total_spend)
        }
    
    def _calculate_concentration(self, sorted_vendors: List, total_spend: float) -> Dict[str, Any]:
        """Calculate vendor concentration metrics"""
        if not sorted_vendors or total_spend == 0:
            return {'top_5_percentage': 0, 'top_10_percentage': 0}
        
        top_5_spend = sum(v['total_amount'] for _, v in sorted_vendors[:5])
        top_10_spend = sum(v['total_amount'] for _, v in sorted_vendors[:10])
        
        return {
            'top_5_percentage': round(top_5_spend / total_spend * 100, 2),
            'top_10_percentage': round(top_10_spend / total_spend * 100, 2),
            'risk_level': 'high' if top_5_spend / total_spend > 0.7 else 'medium' if top_5_spend / total_spend > 0.5 else 'low'
        }
    
    def get_negotiation_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identify vendors where negotiation could yield savings
        
        Returns:
            List of negotiation opportunities with recommendations
        """
        analysis = self.get_vendor_spend_analysis()
        opportunities = []
        
        for vendor in analysis['top_vendors']:
            opportunity = self._analyze_negotiation_opportunity(vendor)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)
        return opportunities[:10]  # Top 10 opportunities
    
    def _analyze_negotiation_opportunity(self, vendor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a single vendor for negotiation opportunity"""
        total_spend = vendor['total_spend']
        invoice_count = vendor['invoice_count']
        
        # Skip small vendors
        if total_spend < 50000:  # ₹50k minimum
            return None
        
        # Calculate potential discount based on spend
        if total_spend >= 1000000:  # ₹10L+
            discount_range = (8, 15)
            tier = 'platinum'
        elif total_spend >= 500000:  # ₹5L+
            discount_range = (5, 10)
            tier = 'gold'
        elif total_spend >= 100000:  # ₹1L+
            discount_range = (3, 7)
            tier = 'silver'
        else:
            discount_range = (2, 5)
            tier = 'bronze'
        
        avg_discount = (discount_range[0] + discount_range[1]) / 2
        potential_savings = total_spend * (avg_discount / 100)
        
        # Generate negotiation points
        negotiation_points = []
        
        if invoice_count >= 10:
            negotiation_points.append(f"Regular customer with {invoice_count} orders")
        
        if total_spend >= 500000:
            negotiation_points.append(f"High-value relationship (₹{total_spend/100000:.1f}L annual spend)")
        
        negotiation_points.append(f"Request {discount_range[0]}-{discount_range[1]}% volume discount")
        
        if invoice_count >= 5:
            negotiation_points.append("Propose quarterly payment terms for additional discount")
        
        return {
            'vendor_name': vendor['vendor_name'],
            'total_spend': total_spend,
            'invoice_count': invoice_count,
            'tier': tier,
            'discount_range': discount_range,
            'potential_savings': round(potential_savings, 2),
            'negotiation_points': negotiation_points,
            'priority': 'high' if potential_savings > 50000 else 'medium' if potential_savings > 20000 else 'low'
        }
    
    def generate_negotiation_script(self, vendor_name: str) -> Optional[Dict[str, str]]:
        """
        Generate an AI-powered negotiation script for a vendor
        
        Args:
            vendor_name: Name of the vendor
            
        Returns:
            Negotiation script with email and talking points
        """
        # Get vendor data
        invoices = self.db.get_invoices_by_vendor(vendor_name)
        if not invoices:
            return None
        
        total_spend = sum(inv.get('total_amount', 0) or 0 for inv in invoices)
        invoice_count = len(invoices)
        
        # Try LLM generation
        if self.llm.backend:
            try:
                prompt = f"""Generate a professional negotiation script for requesting a volume discount from a vendor.

Vendor: {vendor_name}
Total Annual Spend: ₹{total_spend:,.2f}
Number of Orders: {invoice_count}

Generate:
1. A professional email requesting a meeting to discuss pricing
2. Key talking points for the negotiation
3. Suggested discount to request based on spend volume

Return as JSON with keys: email_subject, email_body, talking_points (array), suggested_discount_percentage"""

                result = self.llm.extract_json(prompt)
                return result
            except Exception:
                pass
        
        # Fallback template
        discount = 10 if total_spend >= 500000 else 7 if total_spend >= 100000 else 5
        
        return {
            'email_subject': f'Partnership Discussion - Volume Pricing Review',
            'email_body': f"""Dear {vendor_name} Team,

I hope this email finds you well.

We have been a valued customer of {vendor_name} and have processed {invoice_count} orders totaling ₹{total_spend:,.2f} over the past year.

Given our consistent business relationship and volume, we would like to discuss the possibility of a volume-based pricing arrangement that would be mutually beneficial.

Could we schedule a call this week to discuss potential partnership terms?

Thank you for your continued support.

Best regards""",
            'talking_points': [
                f"Highlight {invoice_count} orders placed",
                f"Mention ₹{total_spend:,.2f} total spend",
                f"Request {discount}% volume discount",
                "Offer to commit to quarterly minimum orders",
                "Discuss early payment discount options"
            ],
            'suggested_discount_percentage': discount
        }


# Singleton
_vendor_service: Optional[VendorIntelligenceService] = None


def get_vendor_intelligence_service() -> VendorIntelligenceService:
    """Get vendor intelligence service instance"""
    global _vendor_service
    if _vendor_service is None:
        _vendor_service = VendorIntelligenceService()
    return _vendor_service
