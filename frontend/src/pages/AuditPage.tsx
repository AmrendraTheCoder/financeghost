import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  Download,
  FileText,
  CheckCircle,
  AlertTriangle,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api';

interface AuditReport {
  report_generated: string;
  period: { start: string; end: string };
  summary: {
    total_invoices: number;
    total_amount: number;
    total_tax: number;
    average_invoice_value: number;
  };
  vendor_summary: Record<string, { count: number; total_amount: number; gstin: string | null }>;
  category_summary: Record<string, { count: number; total_amount: number }>;
  status_summary: Record<string, number>;
  compliance: {
    invoices_with_gstin: number;
    invoices_without_gstin: number;
    issues_found: number;
    compliance_rate: number;
  };
  issues: Array<{
    invoice_number: string;
    vendor: string;
    errors: any[];
  }>;
}

export function AuditPage() {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const res = await api.get('/audit/report', { params });
      setReport(res.data);
    } catch (error) {
      console.error('Failed to fetch audit report:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadAuditPack = async () => {
    setDownloading(true);
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const res = await api.get('/audit/download', {
        params,
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_pack_${new Date().toISOString().split('T')[0]}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download audit pack:', error);
    } finally {
      setDownloading(false);
    }
  };

  const complianceColor =
    (report?.compliance.compliance_rate || 0) >= 90
      ? 'var(--success)'
      : (report?.compliance.compliance_rate || 0) >= 70
      ? 'var(--warning)'
      : 'var(--error)';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>
            🛡️ Audit Defense Shield
          </h1>
          <p className="text-muted">
            Tax compliance reports and audit-ready documentation
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={downloadAuditPack}
          disabled={downloading}
        >
          {downloading ? (
            <RefreshCw size={16} className="animate-spin" />
          ) : (
            <Download size={16} />
          )}
          Download Audit Pack
        </button>
      </div>

      {/* Date Filters */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar size={18} style={{ color: 'var(--text-tertiary)' }} />
            <span className="text-sm text-muted">Period:</span>
          </div>
          <input
            type="date"
            className="input"
            style={{ width: 'auto' }}
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            placeholder="Start Date"
          />
          <span className="text-muted">to</span>
          <input
            type="date"
            className="input"
            style={{ width: 'auto' }}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            placeholder="End Date"
          />
          <button className="btn btn-secondary" onClick={fetchReport}>
            <RefreshCw size={16} />
            Update Report
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner" />
        </div>
      ) : report ? (
        <>
          {/* Compliance Score */}
          <div className="card mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="card-title mb-2">Compliance Score</h3>
                <p className="text-muted">
                  Based on GSTIN validation and tax calculation accuracy
                </p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    background: `conic-gradient(${complianceColor} ${report.compliance.compliance_rate}%, var(--gray-200) 0)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      width: 100,
                      height: 100,
                      borderRadius: '50%',
                      background: 'var(--bg-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexDirection: 'column',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem', fontWeight: 600, color: complianceColor }}>
                      {report.compliance.compliance_rate.toFixed(0)}%
                    </span>
                    <span className="text-xs text-muted">Compliant</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <div className="stat-icon blue">
                <FileText size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Total Invoices</p>
                <p className="stat-value">{report.summary.total_invoices}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon green">
                <CheckCircle size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">With GSTIN</p>
                <p className="stat-value">{report.compliance.invoices_with_gstin}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon yellow">
                <AlertTriangle size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Issues Found</p>
                <p className="stat-value">{report.compliance.issues_found}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon green">
                <Shield size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Total Tax</p>
                <p className="stat-value">₹{report.summary.total_tax.toLocaleString('en-IN')}</p>
              </div>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid-2 mb-6">
            {/* Financial Summary */}
            <div className="card">
              <h3 className="card-title mb-4">Financial Summary</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="flex items-center justify-between">
                  <span className="text-muted">Total Amount</span>
                  <span className="font-medium">
                    ₹{report.summary.total_amount.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted">Total Tax</span>
                  <span className="font-medium">
                    ₹{report.summary.total_tax.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted">Average Invoice</span>
                  <span className="font-medium">
                    ₹{report.summary.average_invoice_value.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted">Period</span>
                  <span className="font-medium">
                    {report.period.start} - {report.period.end}
                  </span>
                </div>
              </div>
            </div>

            {/* Status Breakdown */}
            <div className="card">
              <h3 className="card-title mb-4">Status Breakdown</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {Object.entries(report.status_summary).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <span className="text-muted" style={{ textTransform: 'capitalize' }}>
                      {status.replace('_', ' ')}
                    </span>
                    <span
                      className={`badge ${
                        status === 'processed'
                          ? 'badge-success'
                          : status === 'needs_review'
                          ? 'badge-warning'
                          : 'badge-info'
                      }`}
                    >
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="card mb-6">
            <h3 className="card-title mb-4">Expense Categories</h3>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Invoices</th>
                    <th>Total Amount</th>
                    <th>% of Total</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.category_summary)
                    .sort((a, b) => b[1].total_amount - a[1].total_amount)
                    .map(([category, data]) => (
                      <tr key={category}>
                        <td className="font-medium">{category}</td>
                        <td>{data.count}</td>
                        <td>₹{data.total_amount.toLocaleString('en-IN')}</td>
                        <td>
                          {((data.total_amount / report.summary.total_amount) * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Issues */}
          {report.issues.length > 0 && (
            <div className="card">
              <h3 className="card-title mb-4">⚠️ Issues Requiring Attention</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {report.issues.map((issue, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 12,
                      background: '#fef7e0',
                      borderRadius: 8,
                      border: '1px solid #fde68a',
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{issue.invoice_number}</span>
                      <span className="text-sm text-muted">{issue.vendor}</span>
                    </div>
                    <ul style={{ paddingLeft: 20, margin: 0 }}>
                      {issue.errors.slice(0, 3).map((err, j) => (
                        <li key={j} className="text-sm" style={{ color: '#b06000' }}>
                          {typeof err === 'object' ? err.message : err}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audit Pack Contents */}
          <div className="card mt-6">
            <h3 className="card-title mb-4">📦 Audit Pack Contents</h3>
            <p className="text-muted mb-4">
              Download includes the following files for audit compliance:
            </p>
            <div className="grid-2">
              {[
                { name: 'compliance_report.json', desc: 'Machine-readable compliance data' },
                { name: 'compliance_report.txt', desc: 'Human-readable summary report' },
                { name: 'invoices.csv', desc: 'Complete invoice listing' },
                { name: 'vendor_summary.txt', desc: 'Vendor-wise spending breakdown' },
                { name: 'gst_summary.txt', desc: 'GST filing summary' },
              ].map((file) => (
                <div
                  key={file.name}
                  style={{
                    padding: 12,
                    background: 'var(--bg-secondary)',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <FileText size={20} style={{ color: 'var(--primary)' }} />
                  <div>
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-xs text-muted">{file.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="card text-center py-12">
          <Shield size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
          <p className="text-muted">No audit data available</p>
          <p className="text-sm text-muted">Process invoices to generate compliance reports</p>
        </div>
      )}
    </motion.div>
  );
}
