import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getInvoices, getEmails } from '../api';
import type { Invoice } from '../api';
import {
  Search,
  Filter,
  Eye,
  Mail,
  RefreshCw,
  X,
  FileText,
  Building2,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Copy,
  Tag,
  Receipt,
  ArrowRight,
} from 'lucide-react';

interface InvoiceError {
  field: string;
  error_type: string;
  message: string;
  severity: string;
  suggested_action?: string;
}

interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  hsn_code?: string;
}

export function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [invoiceEmail, setInvoiceEmail] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const result = await getInvoices(100, 0);
      setInvoices(result.invoices);
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoiceEmail = async (invoiceId: number) => {
    try {
      const result = await getEmails(invoiceId);
      if (result.emails && result.emails.length > 0) {
        setInvoiceEmail(result.emails[0]);
      }
    } catch (error) {
      console.error('Failed to fetch email:', error);
    }
  };

  const handleSelectInvoice = (inv: Invoice) => {
    setSelectedInvoice(inv);
    setInvoiceEmail(null);
    if (inv.status === 'needs_review') {
      fetchInvoiceEmail(inv.id);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredInvoices = invoices.filter((inv) => {
    const matchesSearch =
      inv.invoice_number?.toLowerCase().includes(search.toLowerCase()) ||
      inv.vendor_name?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || inv.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const parseErrors = (errorsJson: string): InvoiceError[] => {
    try {
      const parsed = JSON.parse(errorsJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  };

  const parseItems = (itemsJson: string): InvoiceItem[] => {
    try {
      const parsed = JSON.parse(itemsJson);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Invoices</h1>
          <p className="text-muted">{invoices.length} invoices processed</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchInvoices}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <div style={{ flex: 1, position: 'relative' }}>
            <Search
              size={18}
              style={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-tertiary)',
              }}
            />
            <input
              type="text"
              className="input"
              placeholder="Search invoices..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 40 }}
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} style={{ color: 'var(--text-tertiary)' }} />
            <select
              className="input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ width: 'auto', minWidth: 150 }}
            >
              <option value="all">All Status</option>
              <option value="processed">Processed</option>
              <option value="needs_review">Needs Review</option>
              <option value="pending">Pending</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>
      </div>

      {/* Invoice Table */}
      <div className="card">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="spinner" />
          </div>
        ) : filteredInvoices.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Invoice Number</th>
                  <th>Vendor</th>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="font-medium">{inv.invoice_number || 'N/A'}</td>
                    <td>{inv.vendor_name || 'Unknown'}</td>
                    <td>{inv.invoice_date || '-'}</td>
                    <td>₹{(inv.total_amount || 0).toLocaleString('en-IN')}</td>
                    <td>
                      <span className="badge badge-info">
                        {inv.expense_category || 'Uncategorized'}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          inv.status === 'processed'
                            ? 'badge-success'
                            : inv.status === 'needs_review'
                            ? 'badge-warning'
                            : inv.status === 'error'
                            ? 'badge-error'
                            : 'badge-info'
                        }`}
                      >
                        {inv.status?.replace('_', ' ') || 'pending'}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-1">
                        <button
                          className="btn btn-ghost btn-icon"
                          onClick={() => handleSelectInvoice(inv)}
                          title="View Details"
                        >
                          <Eye size={16} />
                        </button>
                        {inv.status === 'needs_review' && (
                          <button
                            className="btn btn-ghost btn-icon"
                            title="View Email"
                            onClick={() => handleSelectInvoice(inv)}
                          >
                            <Mail size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-muted">
            <p className="mb-2">No invoices found</p>
            <p className="text-sm">
              {search || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Upload your first invoice to get started'}
            </p>
          </div>
        )}
      </div>

      {/* Enhanced Invoice Detail Modal */}
      <AnimatePresence>
        {selectedInvoice && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.6)',
              backdropFilter: 'blur(4px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: 24,
            }}
            onClick={() => setSelectedInvoice(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              style={{
                background: 'var(--bg-primary)',
                borderRadius: 20,
                width: '100%',
                maxWidth: 800,
                maxHeight: '90vh',
                overflow: 'hidden',
                boxShadow: '0 24px 80px rgba(0, 0, 0, 0.3)',
              }}
              onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div
                style={{
                  padding: '20px 24px',
                  borderBottom: '1px solid var(--gray-200)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background:
                    selectedInvoice.status === 'needs_review'
                      ? 'linear-gradient(135deg, #fef7e0 0%, #fff 100%)'
                      : selectedInvoice.status === 'processed'
                      ? 'linear-gradient(135deg, #e6f4ea 0%, #fff 100%)'
                      : 'var(--bg-primary)',
                }}
              >
                <div className="flex items-center gap-4">
                  <div
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 12,
                      background:
                        selectedInvoice.status === 'needs_review'
                          ? '#fef7e0'
                          : selectedInvoice.status === 'processed'
                          ? '#e6f4ea'
                          : 'var(--primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {selectedInvoice.status === 'needs_review' ? (
                      <AlertTriangle size={24} style={{ color: '#b06000' }} />
                    ) : selectedInvoice.status === 'processed' ? (
                      <CheckCircle size={24} style={{ color: 'var(--success)' }} />
                    ) : (
                      <FileText size={24} style={{ color: 'var(--primary)' }} />
                    )}
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: 2 }}>
                      Invoice Details
                    </h2>
                    <p className="text-sm text-muted">
                      {selectedInvoice.invoice_number || 'No Invoice Number'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedInvoice(null)}
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    border: 'none',
                    background: 'var(--gray-100)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Modal Content */}
              <div style={{ padding: 24, maxHeight: 'calc(90vh - 80px)', overflow: 'auto' }}>
                {/* Status Badge */}
                <div className="flex items-center gap-3 mb-6">
                  <span
                    className={`badge ${
                      selectedInvoice.status === 'processed'
                        ? 'badge-success'
                        : selectedInvoice.status === 'needs_review'
                        ? 'badge-warning'
                        : 'badge-info'
                    }`}
                    style={{ padding: '6px 14px', fontSize: 13 }}
                  >
                    {selectedInvoice.status === 'processed' && <CheckCircle size={14} style={{ marginRight: 6 }} />}
                    {selectedInvoice.status === 'needs_review' && <AlertTriangle size={14} style={{ marginRight: 6 }} />}
                    {selectedInvoice.status?.replace('_', ' ') || 'pending'}
                  </span>
                  {selectedInvoice.expense_category && (
                    <span className="badge badge-info" style={{ padding: '6px 14px', fontSize: 13 }}>
                      <Tag size={14} style={{ marginRight: 6 }} />
                      {selectedInvoice.expense_category}
                    </span>
                  )}
                </div>

                {/* Main Info Grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(2, 1fr)',
                    gap: 20,
                    marginBottom: 24,
                  }}
                >
                  {/* Vendor Info */}
                  <div
                    style={{
                      padding: 20,
                      background: 'var(--bg-secondary)',
                      borderRadius: 16,
                      border: '1px solid var(--gray-200)',
                    }}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <Building2 size={20} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        Vendor Information
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div>
                        <p className="text-xs text-muted mb-1">Vendor Name</p>
                        <p className="font-medium">{selectedInvoice.vendor_name || 'Unknown'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted mb-1">GSTIN</p>
                        <div className="flex items-center gap-2">
                          <code
                            style={{
                              padding: '4px 8px',
                              background: selectedInvoice.vendor_gstin ? '#e6f4ea' : '#fce8e6',
                              borderRadius: 6,
                              fontSize: 13,
                              fontFamily: 'monospace',
                              color: selectedInvoice.vendor_gstin ? 'var(--success)' : 'var(--error)',
                            }}
                          >
                            {selectedInvoice.vendor_gstin || 'Not Provided'}
                          </code>
                          {selectedInvoice.vendor_gstin && (
                            <button
                              onClick={() => copyToClipboard(selectedInvoice.vendor_gstin!)}
                              style={{
                                background: 'transparent',
                                border: 'none',
                                cursor: 'pointer',
                                color: 'var(--text-tertiary)',
                              }}
                            >
                              <Copy size={14} />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Invoice Info */}
                  <div
                    style={{
                      padding: 20,
                      background: 'var(--bg-secondary)',
                      borderRadius: 16,
                      border: '1px solid var(--gray-200)',
                    }}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <Receipt size={20} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        Invoice Information
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div>
                        <p className="text-xs text-muted mb-1">Invoice Number</p>
                        <p className="font-medium">{selectedInvoice.invoice_number || 'N/A'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted mb-1">Invoice Date</p>
                        <div className="flex items-center gap-2">
                          <Calendar size={14} style={{ color: 'var(--text-tertiary)' }} />
                          <span>{selectedInvoice.invoice_date || 'Not specified'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Financial Summary */}
                <div
                  style={{
                    padding: 24,
                    background: 'linear-gradient(135deg, var(--primary-light) 0%, #f0f9ff 100%)',
                    borderRadius: 16,
                    marginBottom: 24,
                    border: '1px solid #d2e3fc',
                  }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <DollarSign size={20} style={{ color: 'var(--primary)' }} />
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      Financial Summary
                    </span>
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: 24,
                    }}
                  >
                    <div style={{ textAlign: 'center' }}>
                      <p className="text-xs text-muted mb-2">Subtotal</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        ₹{(selectedInvoice.subtotal || 0).toLocaleString('en-IN')}
                      </p>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <p className="text-xs text-muted mb-2">Tax (GST)</p>
                      <p style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        ₹{(selectedInvoice.total_tax || 0).toLocaleString('en-IN')}
                      </p>
                      {selectedInvoice.subtotal > 0 && (
                        <p className="text-xs text-muted mt-1">
                          ({((selectedInvoice.total_tax / selectedInvoice.subtotal) * 100).toFixed(1)}%)
                        </p>
                      )}
                    </div>
                    <div
                      style={{
                        textAlign: 'center',
                        padding: 16,
                        background: 'white',
                        borderRadius: 12,
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                      }}
                    >
                      <p className="text-xs text-muted mb-2">Total Amount</p>
                      <p style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary)' }}>
                        ₹{(selectedInvoice.total_amount || 0).toLocaleString('en-IN')}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Line Items */}
                {selectedInvoice.items_json && parseItems(selectedInvoice.items_json).length > 0 && (
                  <div style={{ marginBottom: 24 }}>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <FileText size={18} style={{ color: 'var(--primary)' }} />
                      Line Items
                    </h4>
                    <div className="table-container" style={{ borderRadius: 12, overflow: 'hidden' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Description</th>
                            <th>Qty</th>
                            <th>Unit Price</th>
                            <th>Tax</th>
                            <th>Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parseItems(selectedInvoice.items_json).map((item, i) => (
                            <tr key={i}>
                              <td>
                                <div>
                                  <p className="font-medium">{item.description}</p>
                                  {item.hsn_code && (
                                    <p className="text-xs text-muted">HSN: {item.hsn_code}</p>
                                  )}
                                </div>
                              </td>
                              <td>{item.quantity}</td>
                              <td>₹{item.unit_price.toLocaleString('en-IN')}</td>
                              <td>
                                <span className="badge badge-info">
                                  {item.tax_rate}%
                                </span>
                              </td>
                              <td className="font-medium">₹{item.total.toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Errors/Warnings */}
                {selectedInvoice.errors_json && parseErrors(selectedInvoice.errors_json).length > 0 && (
                  <div style={{ marginBottom: 24 }}>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <AlertTriangle size={18} style={{ color: '#b06000' }} />
                      Issues Found ({parseErrors(selectedInvoice.errors_json).length})
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      {parseErrors(selectedInvoice.errors_json).map((error, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.1 }}
                          style={{
                            padding: 16,
                            background:
                              error.severity === 'error' ? '#fce8e6' : '#fef7e0',
                            borderRadius: 12,
                            borderLeft: `4px solid ${
                              error.severity === 'error' ? 'var(--error)' : '#b06000'
                            }`,
                          }}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {error.severity === 'error' ? (
                                <AlertTriangle size={16} style={{ color: 'var(--error)' }} />
                              ) : (
                                <AlertTriangle size={16} style={{ color: '#b06000' }} />
                              )}
                              <span
                                className="font-medium"
                                style={{
                                  color: error.severity === 'error' ? 'var(--error)' : '#b06000',
                                }}
                              >
                                {error.error_type.replace('_', ' ')}
                              </span>
                            </div>
                            <span
                              className="badge"
                              style={{
                                background: 'rgba(0,0,0,0.1)',
                                color: error.severity === 'error' ? 'var(--error)' : '#b06000',
                              }}
                            >
                              {error.field}
                            </span>
                          </div>
                          <p style={{ color: 'var(--text-primary)', marginBottom: 8 }}>
                            {error.message}
                          </p>
                          {error.suggested_action && (
                            <div
                              className="flex items-center gap-2"
                              style={{
                                padding: '8px 12px',
                                background: 'rgba(255,255,255,0.5)',
                                borderRadius: 8,
                              }}
                            >
                              <ArrowRight size={14} style={{ color: 'var(--primary)' }} />
                              <span className="text-sm" style={{ color: 'var(--primary)' }}>
                                {error.suggested_action}
                              </span>
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Generated Email */}
                {invoiceEmail && (
                  <div>
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Mail size={18} style={{ color: 'var(--primary)' }} />
                      Generated Vendor Email
                    </h4>
                    <div
                      style={{
                        padding: 20,
                        background: 'var(--bg-secondary)',
                        borderRadius: 16,
                        border: '1px solid var(--gray-200)',
                      }}
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-xs text-muted mb-1">To</p>
                          <p className="font-medium">{invoiceEmail.vendor_name}</p>
                        </div>
                        <button
                          className="btn btn-secondary"
                          onClick={() =>
                            copyToClipboard(
                              `Subject: ${invoiceEmail.subject}\n\n${invoiceEmail.body}`
                            )
                          }
                        >
                          {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                          {copied ? 'Copied!' : 'Copy Email'}
                        </button>
                      </div>
                      <div style={{ marginBottom: 12 }}>
                        <p className="text-xs text-muted mb-1">Subject</p>
                        <p className="font-medium">{invoiceEmail.subject}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted mb-2">Body</p>
                        <div
                          style={{
                            padding: 16,
                            background: 'var(--bg-primary)',
                            borderRadius: 12,
                            fontFamily: 'var(--font-mono)',
                            fontSize: 13,
                            lineHeight: 1.6,
                            whiteSpace: 'pre-wrap',
                            maxHeight: 300,
                            overflow: 'auto',
                          }}
                        >
                          {invoiceEmail.body}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
