"""
Cash Flow Predictor Service
Advanced predictive analytics for cash flow forecasting
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from collections import defaultdict
import statistics

from ..database.db import get_db


class CashFlowPredictor:
    """Advanced cash flow prediction service"""
    
    def __init__(self):
        self.db = get_db()
    
    def get_predictive_forecast(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Generate predictive cash flow forecast
        
        Args:
            days_ahead: Number of days to forecast
            
        Returns:
            Comprehensive forecast with predictions and alerts
        """
        invoices = self.db.get_all_invoices(limit=1000)
        
        # Group by month
        monthly_data = defaultdict(lambda: {'amount': 0, 'count': 0})
        daily_data = defaultdict(float)
        
        for inv in invoices:
            inv_date = inv.get('invoice_date')
            amount = inv.get('total_amount', 0) or 0
            
            if inv_date:
                try:
                    d = date.fromisoformat(inv_date) if isinstance(inv_date, str) else inv_date
                    month_key = d.strftime('%Y-%m')
                    monthly_data[month_key]['amount'] += amount
                    monthly_data[month_key]['count'] += 1
                    daily_data[d.isoformat()] = daily_data.get(d.isoformat(), 0) + amount
                except:
                    pass
        
        # Calculate statistics
        monthly_amounts = [v['amount'] for v in monthly_data.values()]
        
        if len(monthly_amounts) >= 2:
            avg_monthly = statistics.mean(monthly_amounts)
            std_monthly = statistics.stdev(monthly_amounts) if len(monthly_amounts) > 1 else 0
            trend = self._calculate_trend(monthly_data)
        else:
            avg_monthly = monthly_amounts[0] if monthly_amounts else 0
            std_monthly = 0
            trend = 0
        
        # Generate forecast
        today = date.today()
        forecast_dates = []
        cumulative = 0
        
        for i in range(days_ahead):
            forecast_date = today + timedelta(days=i)
            # Simple daily estimate based on monthly average
            daily_estimate = avg_monthly / 30
            # Apply trend
            daily_estimate *= (1 + trend * i / 30)
            cumulative += daily_estimate
            
            forecast_dates.append({
                'date': forecast_date.isoformat(),
                'day': forecast_date.strftime('%a'),
                'estimated_expense': round(daily_estimate, 2),
                'cumulative': round(cumulative, 2)
            })
        
        # Find upcoming due dates
        upcoming_dues = self._get_upcoming_dues(invoices, days_ahead)
        
        # Calculate confidence
        confidence = 'high' if len(monthly_amounts) >= 6 else 'medium' if len(monthly_amounts) >= 3 else 'low'
        
        # Generate alerts
        alerts = self._generate_alerts(avg_monthly, std_monthly, upcoming_dues, cumulative)
        
        return {
            'forecast_period': {
                'start': today.isoformat(),
                'end': (today + timedelta(days=days_ahead)).isoformat(),
                'days': days_ahead
            },
            'predictions': {
                'total_expected': round(cumulative, 2),
                'daily_average': round(avg_monthly / 30, 2),
                'monthly_average': round(avg_monthly, 2),
                'trend_percentage': round(trend * 100, 2),
                'trend_direction': 'increasing' if trend > 0.02 else 'decreasing' if trend < -0.02 else 'stable'
            },
            'confidence': confidence,
            'confidence_interval': {
                'low': round(cumulative * 0.85, 2),
                'high': round(cumulative * 1.15, 2)
            },
            'daily_forecast': forecast_dates[:14],  # First 2 weeks
            'weekly_summary': self._summarize_weekly(forecast_dates),
            'upcoming_dues': upcoming_dues,
            'alerts': alerts,
            'historical': {
                'months_analyzed': len(monthly_amounts),
                'monthly_data': dict(monthly_data)
            }
        }
    
    def _calculate_trend(self, monthly_data: Dict) -> float:
        """Calculate spending trend from monthly data"""
        if len(monthly_data) < 2:
            return 0
        
        sorted_months = sorted(monthly_data.items())
        if len(sorted_months) < 2:
            return 0
        
        # Simple linear trend
        first_half = sorted_months[:len(sorted_months)//2]
        second_half = sorted_months[len(sorted_months)//2:]
        
        first_avg = sum(v['amount'] for _, v in first_half) / len(first_half)
        second_avg = sum(v['amount'] for _, v in second_half) / len(second_half)
        
        if first_avg == 0:
            return 0
        
        return (second_avg - first_avg) / first_avg
    
    def _get_upcoming_dues(self, invoices: List[Dict], days_ahead: int) -> List[Dict[str, Any]]:
        """Get invoices with upcoming due dates"""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        upcoming = []
        
        for inv in invoices:
            # Check if invoice has due date info (would need to be stored)
            # For now, estimate based on invoice date + 30 days
            inv_date = inv.get('invoice_date')
            if inv_date:
                try:
                    d = date.fromisoformat(inv_date) if isinstance(inv_date, str) else inv_date
                    due_date = d + timedelta(days=30)  # Assume Net 30
                    
                    if today <= due_date <= end_date:
                        days_until = (due_date - today).days
                        upcoming.append({
                            'invoice_number': inv.get('invoice_number'),
                            'vendor': inv.get('vendor_name'),
                            'amount': inv.get('total_amount', 0),
                            'due_date': due_date.isoformat(),
                            'days_until_due': days_until,
                            'urgency': 'critical' if days_until <= 3 else 'high' if days_until <= 7 else 'normal'
                        })
                except:
                    pass
        
        # Sort by due date
        upcoming.sort(key=lambda x: x['days_until_due'])
        return upcoming[:10]  # Top 10
    
    def _summarize_weekly(self, daily_forecast: List[Dict]) -> List[Dict[str, Any]]:
        """Summarize forecast by week"""
        weeks = []
        current_week = []
        
        for day in daily_forecast:
            current_week.append(day)
            if len(current_week) == 7:
                weeks.append({
                    'week_start': current_week[0]['date'],
                    'week_end': current_week[-1]['date'],
                    'total': round(sum(d['estimated_expense'] for d in current_week), 2),
                    'daily_avg': round(sum(d['estimated_expense'] for d in current_week) / 7, 2)
                })
                current_week = []
        
        # Handle remaining days
        if current_week:
            weeks.append({
                'week_start': current_week[0]['date'],
                'week_end': current_week[-1]['date'],
                'total': round(sum(d['estimated_expense'] for d in current_week), 2),
                'daily_avg': round(sum(d['estimated_expense'] for d in current_week) / len(current_week), 2)
            })
        
        return weeks
    
    def _generate_alerts(
        self,
        avg_monthly: float,
        std_monthly: float,
        upcoming_dues: List[Dict],
        forecast_total: float
    ) -> List[Dict[str, Any]]:
        """Generate cash flow alerts"""
        alerts = []
        
        # High upcoming payments
        total_due_soon = sum(d['amount'] for d in upcoming_dues if d['days_until_due'] <= 7)
        if total_due_soon > avg_monthly * 0.5:
            alerts.append({
                'type': 'high_payments_due',
                'severity': 'warning',
                'message': f'₹{total_due_soon:,.0f} due in the next 7 days',
                'recommendation': 'Ensure sufficient funds are available'
            })
        
        # Critical due dates
        critical_dues = [d for d in upcoming_dues if d['urgency'] == 'critical']
        if critical_dues:
            alerts.append({
                'type': 'critical_due_dates',
                'severity': 'critical',
                'message': f'{len(critical_dues)} invoice(s) due within 3 days',
                'recommendation': 'Prioritize these payments to avoid late fees'
            })
        
        # Spending trend alert
        if forecast_total > avg_monthly * 1.2:
            alerts.append({
                'type': 'spending_increase',
                'severity': 'info',
                'message': 'Projected spending is 20% above average',
                'recommendation': 'Review upcoming expenses for optimization opportunities'
            })
        
        return alerts
    
    def get_cash_requirement_summary(self) -> Dict[str, Any]:
        """Get a quick summary of cash requirements"""
        forecast = self.get_predictive_forecast(30)
        
        return {
            'next_7_days': round(forecast['predictions']['daily_average'] * 7, 2),
            'next_14_days': round(forecast['predictions']['daily_average'] * 14, 2),
            'next_30_days': forecast['predictions']['total_expected'],
            'critical_payments': len([a for a in forecast['alerts'] if a['severity'] == 'critical']),
            'trend': forecast['predictions']['trend_direction'],
            'confidence': forecast['confidence']
        }


# Singleton
_predictor: Optional[CashFlowPredictor] = None


def get_cashflow_predictor() -> CashFlowPredictor:
    """Get cash flow predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = CashFlowPredictor()
    return _predictor
