"""
Tax Agent
Validates GST calculations and compliance
"""

from typing import Dict, Any, List, Optional
from datetime import date

from .base_agent import BaseAgent
from ..models.invoice import Invoice, InvoiceError, TaxBreakdown
from ..services.llm_service import LLMService


class TaxAgent(BaseAgent):
    """
    Agent for validating tax calculations and GST compliance
    
    Responsibilities:
    - Validate CGST/SGST/IGST calculations
    - Check tax slab compliance
    - Verify HSN codes
    - Calculate correct tax amounts
    - Generate tax summary reports
    """
    
    agent_name = "tax_agent"
    agent_version = "1.0.0"
    
    # GST Tax Slabs (as of 2024)
    GST_SLABS = {
        0: "Exempt (essential goods)",
        5: "Low tax (basic necessities)",
        12: "Standard low",
        18: "Standard (most goods/services)",
        28: "Luxury goods"
    }
    
    # State codes for GSTIN validation
    STATE_CODES = {
        "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
        "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
        "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
        "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
        "16": "Tripura", "17": "Meghalaya", "18": "Assam",
        "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
        "22": "Chattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
        "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
        "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
        "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
        "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh (New)"
    }
    
    def get_system_prompt(self) -> str:
        return """You are an expert GST tax validation agent for Indian businesses.
Your job is to validate tax calculations on invoices and ensure GST compliance.

Key responsibilities:
1. Verify CGST + SGST = Total GST (for intra-state)
2. Verify IGST for inter-state transactions
3. Check if tax rates match the goods/services category
4. Validate GSTIN format and state codes
5. Identify any tax calculation errors

Always be precise with calculations and cite specific GST rules when applicable."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate tax calculations for an invoice
        
        Args:
            input_data: Dict with 'invoice' key containing Invoice data
            
        Returns:
            Tax validation results
        """
        self.validate_input(input_data, ["invoice"])
        
        # Convert dict to Invoice if needed
        invoice_data = input_data["invoice"]
        if isinstance(invoice_data, dict):
            invoice = Invoice(**invoice_data)
        else:
            invoice = invoice_data
        
        self.log("Starting tax validation")
        
        # Perform validations
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "tax_summary": {},
            "recommendations": []
        }
        
        # 1. Validate GSTIN
        gstin_result = self._validate_gstin(invoice.vendor_gstin)
        if not gstin_result["valid"]:
            results["errors"].append(gstin_result)
            results["is_valid"] = False
        
        # 2. Validate tax calculations
        tax_calc_result = self._validate_tax_calculations(invoice)
        results["tax_summary"] = tax_calc_result["summary"]
        if tax_calc_result["errors"]:
            results["errors"].extend(tax_calc_result["errors"])
            results["is_valid"] = False
        if tax_calc_result["warnings"]:
            results["warnings"].extend(tax_calc_result["warnings"])
        
        # 3. Check tax slab appropriateness
        slab_result = self._check_tax_slab(invoice)
        if slab_result["warnings"]:
            results["warnings"].extend(slab_result["warnings"])
        
        # 4. Generate recommendations
        results["recommendations"] = self._generate_recommendations(invoice, results)
        
        self.log(f"Tax validation complete. Valid: {results['is_valid']}")
        
        return results
    
    def _validate_gstin(self, gstin: Optional[str]) -> Dict[str, Any]:
        """Validate GSTIN format and extract state"""
        result = {
            "field": "gstin",
            "valid": True,
            "state": None,
            "message": None
        }
        
        if not gstin:
            result["valid"] = False
            result["message"] = "GSTIN is missing"
            return result
        
        # Check length
        if len(gstin) != 15:
            result["valid"] = False
            result["message"] = f"GSTIN must be 15 characters, got {len(gstin)}"
            return result
        
        # Check state code
        state_code = gstin[:2]
        if state_code not in self.STATE_CODES:
            result["valid"] = False
            result["message"] = f"Invalid state code: {state_code}"
            return result
        
        result["state"] = self.STATE_CODES[state_code]
        result["message"] = f"Valid GSTIN from {result['state']}"
        
        return result
    
    def _validate_tax_calculations(self, invoice: Invoice) -> Dict[str, Any]:
        """Validate tax amount calculations"""
        result = {
            "summary": {},
            "errors": [],
            "warnings": []
        }
        
        subtotal = invoice.subtotal or 0
        total_tax = invoice.total_tax or 0
        total_amount = invoice.total_amount or 0
        
        # Get tax breakdown
        tb = invoice.tax_breakdown or TaxBreakdown()
        
        result["summary"] = {
            "subtotal": subtotal,
            "cgst": tb.cgst_amount,
            "sgst": tb.sgst_amount,
            "igst": tb.igst_amount,
            "total_tax": total_tax,
            "total_amount": total_amount,
            "effective_rate": (total_tax / subtotal * 100) if subtotal > 0 else 0
        }
        
        # Check CGST + SGST = Total (for intra-state)
        if tb.cgst_amount > 0 and tb.sgst_amount > 0:
            expected_total = tb.cgst_amount + tb.sgst_amount
            if abs(expected_total - total_tax) > 1:  # ₹1 tolerance
                result["errors"].append({
                    "field": "tax_total",
                    "error_type": "calculation_error",
                    "message": f"CGST (₹{tb.cgst_amount}) + SGST (₹{tb.sgst_amount}) = ₹{expected_total}, but total tax is ₹{total_tax}",
                    "severity": "error"
                })
        
        # Check if CGST == SGST (they should be equal for intra-state)
        if tb.cgst_amount > 0 and tb.sgst_amount > 0:
            if abs(tb.cgst_amount - tb.sgst_amount) > 1:
                result["warnings"].append({
                    "field": "cgst_sgst",
                    "error_type": "imbalance",
                    "message": f"CGST (₹{tb.cgst_amount}) and SGST (₹{tb.sgst_amount}) should be equal for intra-state transactions",
                    "severity": "warning"
                })
        
        # Check total amount = subtotal + tax
        if subtotal > 0 and total_amount > 0:
            expected_total = subtotal + total_tax
            if abs(expected_total - total_amount) > 1:
                result["errors"].append({
                    "field": "total_amount",
                    "error_type": "calculation_error",
                    "message": f"Subtotal (₹{subtotal}) + Tax (₹{total_tax}) = ₹{expected_total}, but total is ₹{total_amount}",
                    "severity": "error"
                })
        
        # Check effective tax rate is in valid slab
        effective_rate = result["summary"]["effective_rate"]
        valid_slabs = list(self.GST_SLABS.keys())
        
        if effective_rate > 0:
            # Find closest slab
            closest_slab = min(valid_slabs, key=lambda x: abs(x - effective_rate))
            if abs(effective_rate - closest_slab) > 1:  # More than 1% difference
                result["warnings"].append({
                    "field": "tax_rate",
                    "error_type": "unusual_rate",
                    "message": f"Effective tax rate {effective_rate:.1f}% doesn't match standard GST slabs (closest: {closest_slab}%)",
                    "severity": "warning"
                })
        
        return result
    
    def _check_tax_slab(self, invoice: Invoice) -> Dict[str, Any]:
        """Check if applied tax slab is appropriate for the goods/services"""
        result = {"warnings": []}
        
        # This would ideally use HSN code lookup
        # For now, just check if rate is in valid slabs
        for item in invoice.items:
            if item.tax_rate not in self.GST_SLABS:
                result["warnings"].append({
                    "field": f"item_{item.description}",
                    "error_type": "invalid_slab",
                    "message": f"Tax rate {item.tax_rate}% for '{item.description}' is not a standard GST slab",
                    "severity": "warning"
                })
        
        return result
    
    def _generate_recommendations(self, invoice: Invoice, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on validation"""
        recommendations = []
        
        if not results["is_valid"]:
            recommendations.append("Contact vendor to request corrected invoice")
        
        if any("gstin" in str(e).lower() for e in results["errors"]):
            recommendations.append("Verify vendor's GSTIN on GST portal (www.gst.gov.in)")
        
        if results["warnings"]:
            recommendations.append("Review flagged items before processing for ITC claim")
        
        effective_rate = results["tax_summary"].get("effective_rate", 0)
        if effective_rate > 18:
            recommendations.append("High tax rate detected. Verify if goods are correctly classified.")
        
        return recommendations
    
    def calculate_correct_tax(self, subtotal: float, rate: float = 18.0, is_interstate: bool = False) -> Dict[str, float]:
        """
        Calculate correct GST amounts
        
        Args:
            subtotal: Base amount
            rate: GST rate (default 18%)
            is_interstate: True for IGST, False for CGST+SGST
            
        Returns:
            Dict with tax breakdown
        """
        total_tax = subtotal * (rate / 100)
        
        if is_interstate:
            return {
                "cgst": 0,
                "sgst": 0,
                "igst": total_tax,
                "total_tax": total_tax,
                "total_amount": subtotal + total_tax
            }
        else:
            half_tax = total_tax / 2
            return {
                "cgst": half_tax,
                "sgst": half_tax,
                "igst": 0,
                "total_tax": total_tax,
                "total_amount": subtotal + total_tax
            }
