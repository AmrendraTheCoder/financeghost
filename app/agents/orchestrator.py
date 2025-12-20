"""
Agent Orchestrator
Coordinates all agents to process invoices end-to-end
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time
import logging

from .base_agent import BaseAgent
from .invoice_agent import InvoiceAgent
from .tax_agent import TaxAgent
from .cashflow_agent import CashFlowAgent
from ..services.ocr_service import OCRService, get_ocr_service
from ..services.email_generator import EmailGenerator, get_email_generator
from ..services.llm_service import LLMService, get_llm_service
from ..models.invoice import Invoice, InvoiceProcessingResult, InvoiceStatus

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent pipeline for invoice processing
    
    Pipeline:
    1. OCR: Extract text from document
    2. Invoice Agent: Parse and structure data
    3. Tax Agent: Validate tax calculations
    4. Cash Flow Agent: Categorize and analyze
    5. Email Generator: Create vendor email if errors found
    """
    
    _global_logs: List[Dict[str, str]] = []  # Global log buffer for all agent activity
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        ocr_service: Optional[OCRService] = None
    ):
        # Services
        self.llm = llm_service or get_llm_service()
        self.ocr = ocr_service or get_ocr_service()
        
        # Agents
        self.invoice_agent = InvoiceAgent(self.llm)
        self.tax_agent = TaxAgent(self.llm)
        self.cashflow_agent = CashFlowAgent(self.llm)
        
        # Email generator
        self.email_generator = get_email_generator()
        
        # Processing logs (instance-specific for a single processing run)
        self.logs: List[str] = []
    
    @classmethod
    def get_global_logs(cls, limit: int = 50) -> List[Dict[str, str]]:
        """Get recent global agent activity logs"""
        return cls._global_logs[-limit:]
    
    @classmethod
    def add_global_log(cls, agent: str, message: str, level: str = "info"):
        """Add a log entry to the global buffer and broadcast via WebSocket"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "message": message,
            "level": level
        }
        cls._global_logs.append(entry)
        # Keep buffer manageable
        if len(cls._global_logs) > 200:
            cls._global_logs = cls._global_logs[-200:]
        
        # Broadcast via WebSocket (async)
        try:
            import asyncio
            from ..websocket import get_ws_manager
            manager = get_ws_manager()
            # Schedule the broadcast
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(manager.broadcast_log(entry))
            except RuntimeError:
                pass  # No event loop, skip WebSocket broadcast
        except ImportError:
            pass  # WebSocket module not available
    
    def log(self, message: str, level: str = "info"):
        """Add to orchestrator log (instance-specific) and global log"""
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [ORCHESTRATOR] [{level.upper()}] {message}"
        self.logs.append(entry)
        self.add_global_log("ORCHESTRATOR", message, level)
        logger.info(entry)
    
    def process_document(
        self,
        file_path: Optional[str] = None,
        file_content: Optional[bytes] = None,
        filename: Optional[str] = None,
        raw_text: Optional[str] = None,
        company_name: str = "FinanceGhost User"
    ) -> InvoiceProcessingResult:
        """
        Process a document through the full agent pipeline
        
        Args:
            file_path: Path to document file (PDF or image)
            file_content: Raw file bytes (alternative to file_path)
            filename: Original filename (required if using file_content)
            raw_text: Pre-extracted text (skip OCR)
            company_name: Sender company name for email generation
            
        Returns:
            Complete processing result with invoice, validations, and email
        """
        start_time = time.time()
        self.logs = []
        agent_logs = []
        
        self.log("Starting document processing")
        
        # Step 1: OCR - Extract text
        if raw_text:
            text = raw_text
            self.log("Using provided text (OCR skipped)")
        elif file_content and filename:
            self.log(f"Extracting text from bytes: {filename}")
            text = self.ocr.extract_from_bytes(file_content, filename)
        elif file_path:
            self.log(f"Extracting text from file: {file_path}")
            text = self.ocr.extract(file_path)
        else:
            raise ValueError("Must provide file_path, file_content+filename, or raw_text")
        
        self.log(f"Extracted {len(text)} characters")
        
        # Step 2: Invoice Agent - Extract structured data
        self.log("Invoking Invoice Agent")
        invoice_result = self.invoice_agent.safe_process({
            "text": text,
            "file_path": file_path
        })
        agent_logs.extend(self.invoice_agent.get_logs())
        
        if not invoice_result["success"]:
            self.log(f"Invoice Agent failed: {invoice_result['error']}", level="error")
            raise ValueError(f"Invoice extraction failed: {invoice_result['error']}")
        
        invoice = Invoice(**invoice_result["data"])
        self.log(f"Invoice extracted: {invoice.invoice_number} from {invoice.vendor_name}")
        
        # Step 3: Tax Agent - Validate taxes
        self.log("Invoking Tax Agent")
        tax_result = self.tax_agent.safe_process({
            "invoice": invoice.model_dump()
        })
        agent_logs.extend(self.tax_agent.get_logs())
        
        tax_validation = tax_result.get("data", {}) if tax_result["success"] else {"error": tax_result.get("error")}
        self.log(f"Tax validation: {'valid' if tax_validation.get('is_valid') else 'issues found'}")
        
        # Step 4: Cash Flow Agent - Categorize and analyze
        self.log("Invoking Cash Flow Agent")
        cashflow_result = self.cashflow_agent.safe_process({
            "invoice": invoice.model_dump()
        })
        agent_logs.extend(self.cashflow_agent.get_logs())
        
        cashflow_analysis = cashflow_result.get("data", {}) if cashflow_result["success"] else {}
        invoice.expense_category = cashflow_analysis.get("category", "Other")
        self.log(f"Expense category: {invoice.expense_category}")
        
        # Step 5: Generate email if errors found
        generated_email = None
        if invoice.errors:
            self.log("Errors found, generating vendor email")
            email_result = self.email_generator.generate_batch_email(invoice, company_name)
            if email_result:
                generated_email = f"Subject: {email_result['subject']}\n\n{email_result['body']}"
                invoice.status = InvoiceStatus.NEEDS_REVIEW
            self.log("Vendor email generated")
        else:
            invoice.status = InvoiceStatus.PROCESSED
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        self.log(f"Processing complete in {processing_time:.0f}ms")
        
        # Build result
        return InvoiceProcessingResult(
            invoice=invoice,
            tax_validation=tax_validation,
            cashflow_analysis=cashflow_analysis,
            generated_email=generated_email,
            processing_time_ms=processing_time,
            agent_logs=agent_logs + self.logs
        )
    
    def process_text(self, text: str, company_name: str = "FinanceGhost User") -> InvoiceProcessingResult:
        """
        Process raw invoice text (convenience method)
        
        Args:
            text: Invoice text content
            company_name: Sender company name
            
        Returns:
            Processing result
        """
        return self.process_document(raw_text=text, company_name=company_name)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated data for dashboard display"""
        return self.cashflow_agent.get_dashboard_data()
    
    def get_recent_invoices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently processed invoices"""
        return [inv.model_dump() for inv in self.cashflow_agent.invoices[-limit:]]


# Singleton instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator

def get_global_agent_logs(limit: int = 50) -> List[Dict[str, str]]:
    """Helper to access global logs"""
    return AgentOrchestrator.get_global_logs(limit)
