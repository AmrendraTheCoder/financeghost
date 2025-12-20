"""
Database Layer
SQLite database operations for persisting invoices
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sqlite3
from pathlib import Path
import logging

from ..models.invoice import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)


class Database:
    """Simple SQLite database for invoice storage"""
    
    def __init__(self, db_path: str = "financeghost.db"):
        self.db_path = db_path
        self._ensure_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                invoice_date TEXT,
                vendor_name TEXT,
                vendor_gstin TEXT,
                total_amount REAL,
                total_tax REAL,
                subtotal REAL,
                currency TEXT DEFAULT 'INR',
                status TEXT DEFAULT 'pending',
                expense_category TEXT,
                raw_text TEXT,
                errors_json TEXT,
                items_json TEXT,
                file_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT
            )
        """)
        
        # Vendors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gstin TEXT UNIQUE,
                email TEXT,
                phone TEXT,
                address TEXT,
                total_invoices INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendor_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                vendor_name TEXT,
                subject TEXT,
                body TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database tables initialized")
    
    def save_invoice(self, invoice: Invoice) -> int:
        """
        Save invoice to database
        
        Args:
            invoice: Invoice to save
            
        Returns:
            Invoice ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, invoice_date, vendor_name, vendor_gstin,
                total_amount, total_tax, subtotal, currency, status,
                expense_category, raw_text, errors_json, items_json,
                file_path, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice.invoice_number,
            invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            invoice.vendor_name,
            invoice.vendor_gstin,
            invoice.total_amount,
            invoice.total_tax,
            invoice.subtotal,
            invoice.currency,
            invoice.status.value if invoice.status else "pending",
            invoice.expense_category,
            invoice.raw_text,
            json.dumps([e.model_dump() for e in invoice.errors]),
            json.dumps([i.model_dump() for i in invoice.items]),
            invoice.file_path,
            datetime.now().isoformat()
        ))
        
        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Saved invoice {invoice.invoice_number} with ID {invoice_id}")
        return invoice_id
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all invoices with pagination"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM invoices ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_invoices_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get invoices by status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM invoices WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_invoices_by_vendor(self, vendor_name: str) -> List[Dict[str, Any]]:
        """Get invoices by vendor name"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM invoices WHERE vendor_name LIKE ? ORDER BY created_at DESC",
            (f"%{vendor_name}%",)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def save_email(self, invoice_id: int, vendor_name: str, subject: str, body: str) -> int:
        """Save generated email to database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vendor_emails (invoice_id, vendor_name, subject, body)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, vendor_name, subject, body))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return email_id
    
    def get_emails(self, invoice_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get emails, optionally filtered by invoice"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if invoice_id:
            cursor.execute(
                "SELECT * FROM vendor_emails WHERE invoice_id = ? ORDER BY created_at DESC",
                (invoice_id,)
            )
        else:
            cursor.execute("SELECT * FROM vendor_emails ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total invoices
        cursor.execute("SELECT COUNT(*) as count FROM invoices")
        total_invoices = cursor.fetchone()["count"]
        
        # Total amount
        cursor.execute("SELECT SUM(total_amount) as total FROM invoices")
        row = cursor.fetchone()
        total_amount = row["total"] if row["total"] else 0
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM invoices 
            GROUP BY status
        """)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # By category
        cursor.execute("""
            SELECT expense_category, SUM(total_amount) as total 
            FROM invoices 
            WHERE expense_category IS NOT NULL
            GROUP BY expense_category
        """)
        category_totals = {row["expense_category"]: row["total"] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "by_status": status_counts,
            "by_category": category_totals
        }


# Singleton instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database singleton"""
    global _db
    if _db is None:
        _db = Database()
    return _db
