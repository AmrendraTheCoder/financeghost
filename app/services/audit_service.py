"""
Audit Service
Generate audit-ready compliance reports and packages
"""

import io
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import zipfile

from ..database.db import get_db
from ..models.invoice import Invoice


class AuditService:
    """Service for generating audit compliance packages"""
    
    def __init__(self):
        self.db = get_db()
    
    def generate_compliance_report(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive tax compliance report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report data
        """
        invoices = self.db.get_all_invoices(limit=1000)
        
        # Filter by date if provided
        if start_date or end_date:
            filtered = []
            for inv in invoices:
                inv_date = inv.get('invoice_date')
                if inv_date:
                    try:
                        d = date.fromisoformat(inv_date) if isinstance(inv_date, str) else inv_date
                        if start_date and d < start_date:
                            continue
                        if end_date and d > end_date:
                            continue
                        filtered.append(inv)
                    except:
                        filtered.append(inv)
                else:
                    filtered.append(inv)
            invoices = filtered
        
        # Calculate totals
        total_amount = sum(inv.get('total_amount', 0) or 0 for inv in invoices)
        total_tax = sum(inv.get('total_tax', 0) or 0 for inv in invoices)
        total_cgst = 0
        total_sgst = 0
        total_igst = 0
        
        # Group by vendor
        vendor_summary = {}
        for inv in invoices:
            vendor = inv.get('vendor_name', 'Unknown')
            if vendor not in vendor_summary:
                vendor_summary[vendor] = {
                    'count': 0,
                    'total_amount': 0,
                    'gstin': inv.get('vendor_gstin')
                }
            vendor_summary[vendor]['count'] += 1
            vendor_summary[vendor]['total_amount'] += inv.get('total_amount', 0) or 0
        
        # Group by category
        category_summary = {}
        for inv in invoices:
            cat = inv.get('expense_category', 'Uncategorized')
            if cat not in category_summary:
                category_summary[cat] = {'count': 0, 'total_amount': 0}
            category_summary[cat]['count'] += 1
            category_summary[cat]['total_amount'] += inv.get('total_amount', 0) or 0
        
        # Status breakdown
        status_summary = {}
        for inv in invoices:
            status = inv.get('status', 'pending')
            status_summary[status] = status_summary.get(status, 0) + 1
        
        # Issues found
        issues = []
        for inv in invoices:
            errors_json = inv.get('errors_json')
            if errors_json:
                try:
                    errors = json.loads(errors_json) if isinstance(errors_json, str) else errors_json
                    if errors:
                        issues.append({
                            'invoice_number': inv.get('invoice_number'),
                            'vendor': inv.get('vendor_name'),
                            'errors': errors
                        })
                except:
                    pass
        
        return {
            'report_generated': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat() if start_date else 'All time',
                'end': end_date.isoformat() if end_date else 'Present'
            },
            'summary': {
                'total_invoices': len(invoices),
                'total_amount': total_amount,
                'total_tax': total_tax,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_igst': total_igst,
                'average_invoice_value': total_amount / len(invoices) if invoices else 0
            },
            'vendor_summary': vendor_summary,
            'category_summary': category_summary,
            'status_summary': status_summary,
            'compliance': {
                'invoices_with_gstin': sum(1 for inv in invoices if inv.get('vendor_gstin')),
                'invoices_without_gstin': sum(1 for inv in invoices if not inv.get('vendor_gstin')),
                'issues_found': len(issues),
                'compliance_rate': (len(invoices) - len(issues)) / len(invoices) * 100 if invoices else 100
            },
            'issues': issues[:20]  # Top 20 issues
        }
    
    def generate_audit_pack_zip(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> bytes:
        """
        Generate a ZIP file containing all audit materials
        
        Returns:
            ZIP file as bytes
        """
        # Create in-memory ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add compliance report
            report = self.generate_compliance_report(start_date, end_date)
            zf.writestr(
                'compliance_report.json',
                json.dumps(report, indent=2, default=str)
            )
            
            # Add human-readable report
            readable_report = self._generate_readable_report(report)
            zf.writestr('compliance_report.txt', readable_report)
            
            # Add invoice list CSV
            csv_content = self._generate_invoice_csv()
            zf.writestr('invoices.csv', csv_content)
            
            # Add vendor summary
            vendor_report = self._generate_vendor_report(report)
            zf.writestr('vendor_summary.txt', vendor_report)
            
            # Add GST summary
            gst_report = self._generate_gst_summary(report)
            zf.writestr('gst_summary.txt', gst_report)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _generate_readable_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable compliance report"""
        lines = [
            "=" * 60,
            "FINANCEGHOST - TAX COMPLIANCE REPORT",
            "=" * 60,
            "",
            f"Generated: {report['report_generated']}",
            f"Period: {report['period']['start']} to {report['period']['end']}",
            "",
            "-" * 60,
            "SUMMARY",
            "-" * 60,
            f"Total Invoices: {report['summary']['total_invoices']}",
            f"Total Amount: ₹{report['summary']['total_amount']:,.2f}",
            f"Total Tax: ₹{report['summary']['total_tax']:,.2f}",
            f"Average Invoice: ₹{report['summary']['average_invoice_value']:,.2f}",
            "",
            "-" * 60,
            "COMPLIANCE STATUS",
            "-" * 60,
            f"Invoices with GSTIN: {report['compliance']['invoices_with_gstin']}",
            f"Invoices without GSTIN: {report['compliance']['invoices_without_gstin']}",
            f"Issues Found: {report['compliance']['issues_found']}",
            f"Compliance Rate: {report['compliance']['compliance_rate']:.1f}%",
            "",
            "-" * 60,
            "STATUS BREAKDOWN",
            "-" * 60,
        ]
        
        for status, count in report['status_summary'].items():
            lines.append(f"  {status}: {count}")
        
        lines.extend([
            "",
            "-" * 60,
            "CATEGORY BREAKDOWN",
            "-" * 60,
        ])
        
        for cat, data in report['category_summary'].items():
            lines.append(f"  {cat}: {data['count']} invoices, ₹{data['total_amount']:,.2f}")
        
        if report['issues']:
            lines.extend([
                "",
                "-" * 60,
                "ISSUES REQUIRING ATTENTION",
                "-" * 60,
            ])
            for issue in report['issues'][:10]:
                lines.append(f"  Invoice {issue['invoice_number']} ({issue['vendor']}):")
                for err in issue['errors'][:3]:
                    if isinstance(err, dict):
                        lines.append(f"    - {err.get('message', str(err))}")
                    else:
                        lines.append(f"    - {err}")
        
        lines.extend(["", "=" * 60, "END OF REPORT", "=" * 60])
        return "\n".join(lines)
    
    def _generate_invoice_csv(self) -> str:
        """Generate CSV of all invoices"""
        invoices = self.db.get_all_invoices(limit=1000)
        
        lines = ["Invoice Number,Date,Vendor,GSTIN,Amount,Tax,Status,Category"]
        for inv in invoices:
            lines.append(",".join([
                str(inv.get('invoice_number', '')),
                str(inv.get('invoice_date', '')),
                str(inv.get('vendor_name', '')).replace(',', ';'),
                str(inv.get('vendor_gstin', '')),
                str(inv.get('total_amount', 0)),
                str(inv.get('total_tax', 0)),
                str(inv.get('status', '')),
                str(inv.get('expense_category', '')).replace(',', ';')
            ]))
        
        return "\n".join(lines)
    
    def _generate_vendor_report(self, report: Dict[str, Any]) -> str:
        """Generate vendor summary report"""
        lines = [
            "VENDOR SUMMARY REPORT",
            "=" * 50,
            "",
        ]
        
        # Sort by total amount
        sorted_vendors = sorted(
            report['vendor_summary'].items(),
            key=lambda x: x[1]['total_amount'],
            reverse=True
        )
        
        for vendor, data in sorted_vendors:
            lines.extend([
                f"Vendor: {vendor}",
                f"  GSTIN: {data.get('gstin', 'Not provided')}",
                f"  Invoices: {data['count']}",
                f"  Total: ₹{data['total_amount']:,.2f}",
                ""
            ])
        
        return "\n".join(lines)
    
    def _generate_gst_summary(self, report: Dict[str, Any]) -> str:
        """Generate GST summary for filing"""
        lines = [
            "GST SUMMARY FOR FILING",
            "=" * 50,
            "",
            f"Total Taxable Value: ₹{report['summary']['total_amount'] - report['summary']['total_tax']:,.2f}",
            f"Total CGST: ₹{report['summary']['total_cgst']:,.2f}",
            f"Total SGST: ₹{report['summary']['total_sgst']:,.2f}",
            f"Total IGST: ₹{report['summary']['total_igst']:,.2f}",
            f"Total Tax: ₹{report['summary']['total_tax']:,.2f}",
            "",
            "Note: Please verify these figures with your actual GST returns.",
            "This is an automated summary and may require manual adjustments.",
        ]
        return "\n".join(lines)


# Singleton
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get audit service instance"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
