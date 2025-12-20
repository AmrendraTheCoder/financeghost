"""
FinanceGhost API
FastAPI backend for invoice processing
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
import logging
import uvicorn
import asyncio

from .config import settings
from .agents.orchestrator import get_orchestrator
from .database.db import get_db
from .models.invoice import InvoiceProcessingResult
from .websocket import get_ws_manager
from .services.audit_service import get_audit_service
from .services.vendor_intelligence import get_vendor_intelligence_service
from .services.cashflow_predictor import get_cashflow_predictor
from .services.firm_intelligence import get_firm_intelligence_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FinanceGhost Autonomous",
    description="AI-Powered Invoice Processing System with Autonomous Vendor Communication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class TextProcessRequest(BaseModel):
    text: str
    company_name: Optional[str] = "FinanceGhost User"


class ProcessingResponse(BaseModel):
    success: bool
    invoice_id: Optional[int] = None
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    errors_count: int = 0
    has_email: bool = False
    generated_email: Optional[str] = None
    processing_time_ms: float = 0
    message: str = ""


# Health check
@app.get("/")
async def root():
    return {
        "name": "FinanceGhost Autonomous",
        "version": "0.1.0",
        "status": "running",
        "message": "AI-Powered Invoice Processing System"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Invoice upload endpoint
@app.post("/upload", response_model=ProcessingResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    company_name: str = "FinanceGhost User"
):
    """
    Upload and process an invoice (PDF or image)
    
    Returns processed invoice data with any errors and generated vendor email
    """
    try:
        # Read file
        content = await file.read()
        filename = file.filename or "unknown.pdf"
        
        logger.info(f"Processing upload: {filename} ({len(content)} bytes)")
        
        # Process through orchestrator
        orchestrator = get_orchestrator()
        result = orchestrator.process_document(
            file_content=content,
            filename=filename,
            company_name=company_name
        )
        
        # Save to database
        db = get_db()
        invoice_id = db.save_invoice(result.invoice)
        
        # Save email if generated
        if result.generated_email:
            db.save_email(
                invoice_id=invoice_id,
                vendor_name=result.invoice.vendor_name,
                subject=f"Invoice Correction - {result.invoice.invoice_number}",
                body=result.generated_email
            )
        
        return ProcessingResponse(
            success=True,
            invoice_id=invoice_id,
            invoice_number=result.invoice.invoice_number,
            vendor_name=result.invoice.vendor_name,
            total_amount=result.invoice.total_amount,
            status=result.invoice.status.value,
            errors_count=len(result.invoice.errors),
            has_email=result.generated_email is not None,
            generated_email=result.generated_email,
            processing_time_ms=result.processing_time_ms,
            message=f"Invoice processed successfully in {result.processing_time_ms:.0f}ms"
        )
        
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Process raw text endpoint
@app.post("/process-text", response_model=ProcessingResponse)
async def process_text(request: TextProcessRequest):
    """
    Process raw invoice text
    
    Useful for testing or when OCR is done externally
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.process_text(
            text=request.text,
            company_name=request.company_name
        )
        
        # Save to database
        db = get_db()
        invoice_id = db.save_invoice(result.invoice)
        
        return ProcessingResponse(
            success=True,
            invoice_id=invoice_id,
            invoice_number=result.invoice.invoice_number,
            vendor_name=result.invoice.vendor_name,
            total_amount=result.invoice.total_amount,
            status=result.invoice.status.value,
            errors_count=len(result.invoice.errors),
            has_email=result.generated_email is not None,
            generated_email=result.generated_email,
            processing_time_ms=result.processing_time_ms,
            message="Invoice processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get all invoices
@app.get("/invoices")
async def get_invoices(limit: int = 100, offset: int = 0):
    """Get all processed invoices"""
    try:
        db = get_db()
        invoices = db.get_all_invoices(limit=limit, offset=offset)
        return {"invoices": invoices, "count": len(invoices)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get single invoice
@app.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: int):
    """Get invoice by ID"""
    try:
        db = get_db()
        invoice = db.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get invoices needing review
@app.get("/invoices/status/needs-review")
async def get_invoices_needing_review():
    """Get invoices that need review (have errors)"""
    try:
        db = get_db()
        invoices = db.get_invoices_by_status("needs_review")
        return {"invoices": invoices, "count": len(invoices)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get emails
@app.get("/emails")
async def get_emails(invoice_id: Optional[int] = None):
    """Get generated vendor emails"""
    try:
        db = get_db()
        emails = db.get_emails(invoice_id)
        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard data
@app.get("/dashboard")
async def get_dashboard():
    """Get dashboard summary data"""
    try:
        orchestrator = get_orchestrator()
        db = get_db()
        predictor = get_cashflow_predictor()
        
        # Combine in-memory and database stats
        dashboard_data = orchestrator.get_dashboard_data()
        db_stats = db.get_summary_stats()
        cash_requirement = predictor.get_cash_requirement_summary()
        
        return {
            "summary": db_stats,
            "cashflow": dashboard_data,
            "recent_invoices": orchestrator.get_recent_invoices(5),
            "cash_forecast": cash_requirement
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Logs Endpoint
@app.get("/agent-logs")
async def get_agent_logs():
    """Get real-time agent activity logs"""
    from .agents.orchestrator import get_global_agent_logs
    return {"logs": get_global_agent_logs(50)}


# Demo endpoint with sample invoice
@app.get("/demo")
async def demo():
    """
    Process a demo invoice to showcase the system
    """
    import random
    
    # Multiple sample invoices for variety
    demo_invoices = [
        """
INVOICE
Invoice No: INV-2024-001
Date: 2024-12-20
Due Date: 2025-01-20

From:
ABC Suppliers Pvt Ltd
GSTIN: 27AAACE1234F1ZP
123 Business Street, Mumbai
Maharashtra - 400001

To:
XYZ Company Ltd
GSTIN: 29BBBBB0000B1Z6
456 Commerce Road, Bangalore

Items:
1. Office Supplies - Qty: 10 - Rate: 500 - Amount: 5,000
2. Printer Paper - Qty: 20 - Rate: 300 - Amount: 6,000

Subtotal: 11,000
CGST (9%): 990
SGST (9%): 990
Total Tax: 1,980

Grand Total: ₹12,980
""",
        """
INVOICE
Invoice No: INV-2024-002
Date: 2024-12-18

Vendor: Tech Solutions India
GSTIN: 07AABCT1234F1ZK
Address: Nehru Place, New Delhi

Bill To:
Demo Corp Pvt Ltd
GSTIN: 27AACCD5678G1ZH

Products:
- Laptop Dell XPS 15 x 2 @ 85000 = 170,000
- Wireless Mouse x 5 @ 1500 = 7,500
- USB Hub x 3 @ 2000 = 6,000

Subtotal: 183,500
IGST (18%): 33,030
Grand Total: ₹2,16,530

Payment Terms: Net 30
""",
        """
TAX INVOICE
No: TI/2024/1234
Date: 15-12-2024

From: Premium Foods Ltd
GST: 19AABCP8765K1ZY
Kolkata, West Bengal

To: Restaurant Chain India
GST: 33AABCR0000A1ZX

Items:
Basmati Rice 50kg x 10 @ 2500 = 25000
Cooking Oil 15L x 20 @ 1800 = 36000
Spices Package x 50 @ 500 = 25000

Sub-Total: 86,000
CGST 2.5%: 2,150
SGST 2.5%: 2,150
Total: ₹90,300

Note: Food items at 5% GST
"""
    ]
    
    # Pick a random invoice for variety
    demo_text = random.choice(demo_invoices)
    
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.process_text(demo_text)
        
        # Save to database
        db = get_db()
        invoice_id = db.save_invoice(result.invoice)
        
        # Save email if generated
        if result.generated_email:
            db.save_email(
                invoice_id=invoice_id,
                vendor_name=result.invoice.vendor_name or "Unknown Vendor",
                subject=f"Invoice Correction Required - {result.invoice.invoice_number}",
                body=result.generated_email
            )
        
        return {
            "success": True,
            "message": "Demo invoice processed and saved!",
            "invoice_id": invoice_id,
            "invoice": result.invoice.model_dump(),
            "tax_validation": result.tax_validation,
            "cashflow_analysis": result.cashflow_analysis,
            "generated_email": result.generated_email,
            "processing_time_ms": result.processing_time_ms
        }
    except Exception as e:
        logger.error(f"Demo processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


# ============================================
# WebSocket Endpoint for Ghost Mode Live Logs
# ============================================

@app.websocket("/ws/agent-logs")
async def websocket_agent_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent activity streaming
    Ghost Mode - Live terminal view of AI agent thinking
    """
    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle any incoming messages
            data = await websocket.receive_text()
            # Could handle commands from client here
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================
# Predictive Cash Flow Endpoints
# ============================================

@app.get("/cashflow/forecast")
async def get_cashflow_forecast(days: int = Query(default=30, ge=7, le=90)):
    """
    Get predictive cash flow forecast
    
    Args:
        days: Number of days to forecast (7-90)
    """
    try:
        predictor = get_cashflow_predictor()
        forecast = predictor.get_predictive_forecast(days)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cashflow/summary")
async def get_cashflow_summary():
    """Get quick cash requirement summary"""
    try:
        predictor = get_cashflow_predictor()
        return predictor.get_cash_requirement_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Vendor Intelligence Endpoints
# ============================================

@app.get("/vendors/analysis")
async def get_vendor_analysis():
    """Get comprehensive vendor spend analysis"""
    try:
        service = get_vendor_intelligence_service()
        return service.get_vendor_spend_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vendors/negotiations")
async def get_negotiation_opportunities():
    """Get vendor negotiation opportunities with potential savings"""
    try:
        service = get_vendor_intelligence_service()
        opportunities = service.get_negotiation_opportunities()
        return {"opportunities": opportunities, "count": len(opportunities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vendors/{vendor_name}/negotiation-script")
async def get_negotiation_script(vendor_name: str):
    """Generate AI-powered negotiation script for a vendor"""
    try:
        service = get_vendor_intelligence_service()
        script = service.generate_negotiation_script(vendor_name)
        if not script:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return script
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Audit & Compliance Endpoints
# ============================================

@app.get("/audit/report")
async def get_audit_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get comprehensive tax compliance report"""
    try:
        service = get_audit_service()
        
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        report = service.generate_compliance_report(start, end)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/download")
async def download_audit_pack(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Download complete audit pack as ZIP file
    Contains: compliance report, invoice CSV, vendor summary, GST summary
    """
    try:
        service = get_audit_service()
        
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None
        
        zip_bytes = service.generate_audit_pack_zip(start, end)
        
        filename = f"audit_pack_{date.today().isoformat()}.zip"
        
        return StreamingResponse(
            iter([zip_bytes]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Voice Command Endpoint
# ============================================

class VoiceCommandRequest(BaseModel):
    transcript: str
    context: Optional[str] = None


@app.post("/voice/command")
async def process_voice_command(request: VoiceCommandRequest):
    """
    Process voice command and return appropriate response
    Supports queries like:
    - "How much did we spend on travel this month?"
    - "Show me invoices from Dell"
    - "What's our cash flow forecast?"
    """
    try:
        transcript = request.transcript.lower()
        db = get_db()
        
        # Parse intent
        if any(word in transcript for word in ['spend', 'spent', 'expense', 'cost']):
            # Spending query
            stats = db.get_summary_stats()
            category_match = None
            
            for cat in stats.get('by_category', {}).keys():
                if cat.lower() in transcript:
                    category_match = cat
                    break
            
            if category_match:
                amount = stats['by_category'].get(category_match, 0)
                return {
                    "intent": "spending_query",
                    "response": f"You've spent ₹{amount:,.2f} on {category_match}.",
                    "data": {"category": category_match, "amount": amount}
                }
            else:
                return {
                    "intent": "spending_query",
                    "response": f"Your total spending is ₹{stats['total_amount']:,.2f} across {stats['total_invoices']} invoices.",
                    "data": stats
                }
        
        elif any(word in transcript for word in ['invoice', 'invoices', 'bill']):
            # Invoice query
            if 'review' in transcript or 'error' in transcript or 'issue' in transcript:
                invoices = db.get_invoices_by_status('needs_review')
                return {
                    "intent": "invoice_query",
                    "response": f"You have {len(invoices)} invoices that need review.",
                    "data": {"count": len(invoices), "invoices": invoices[:5]}
                }
            else:
                invoices = db.get_all_invoices(limit=5)
                return {
                    "intent": "invoice_query",
                    "response": f"Here are your recent invoices.",
                    "data": {"invoices": invoices}
                }
        
        elif any(word in transcript for word in ['forecast', 'predict', 'cash flow', 'cashflow']):
            # Cash flow query
            predictor = get_cashflow_predictor()
            summary = predictor.get_cash_requirement_summary()
            return {
                "intent": "cashflow_query",
                "response": f"Based on your spending patterns, you'll need approximately ₹{summary['next_30_days']:,.0f} in the next 30 days. The trend is {summary['trend']}.",
                "data": summary
            }
        
        elif any(word in transcript for word in ['vendor', 'supplier']):
            # Vendor query
            service = get_vendor_intelligence_service()
            analysis = service.get_vendor_spend_analysis()
            top_vendor = analysis['top_vendors'][0] if analysis['top_vendors'] else None
            
            if top_vendor:
                return {
                    "intent": "vendor_query",
                    "response": f"Your top vendor is {top_vendor['vendor_name']} with ₹{top_vendor['total_spend']:,.0f} in spending.",
                    "data": {"top_vendors": analysis['top_vendors'][:5]}
                }
        
        # Default response
        return {
            "intent": "unknown",
            "response": "I can help you with spending queries, invoice lookups, cash flow forecasts, and vendor analysis. Try asking something like 'How much did we spend on IT?' or 'Show me invoices that need review'.",
            "suggestions": [
                "How much did we spend this month?",
                "Show invoices that need review",
                "What's our cash flow forecast?",
                "Who are our top vendors?"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    start_server()


# ============================================
# Firm Intelligence Endpoints (NEW)
# ============================================

@app.get("/firm/intelligence")
async def get_firm_intelligence():
    """
    Get complete firm-level operational intelligence
    The hero endpoint for Ops Intelligence dashboard
    """
    try:
        service = get_firm_intelligence_service()
        return service.get_firm_intelligence()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/firm/month-end")
async def get_month_end_dashboard():
    """
    Get Month-End Close Autopilot dashboard
    Shows progress, risks, and urgent items across all clients
    """
    try:
        service = get_firm_intelligence_service()
        dashboard = service.get_month_end_autopilot()
        return dashboard.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/firm/urgent")
async def get_urgent_items():
    """
    Get items requiring immediate attention
    'What needs to be done TODAY to avoid problems?'
    """
    try:
        service = get_firm_intelligence_service()
        items = service.get_attention_needed_now()
        return {
            "items": [item.model_dump() for item in items],
            "count": len(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/firm/briefing")
async def get_daily_briefing():
    """
    Get AI-generated daily briefing for firm partners
    Summarizes state, risks, and priorities
    """
    try:
        service = get_firm_intelligence_service()
        briefing = service.generate_day_briefing()
        return briefing.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clients/{client_id}/risk")
async def get_client_risk(client_id: str):
    """
    Get compliance risk assessment for a specific client
    """
    try:
        from .agents.compliance_risk_agent import get_compliance_risk_agent
        agent = get_compliance_risk_agent()
        risk = agent.get_client_compliance_posture(client_id)
        return risk.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

