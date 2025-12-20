import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  Users,
  DollarSign,
  AlertTriangle,
  Copy,
  CheckCircle,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { api } from '../api';

interface VendorAnalysis {
  total_spend: number;
  total_vendors: number;
  top_vendors: Array<{
    vendor_name: string;
    gstin: string | null;
    total_spend: number;
    percentage_of_total: number;
    invoice_count: number;
    average_invoice: number;
    primary_category: string;
  }>;
  concentration: {
    top_5_percentage: number;
    top_10_percentage: number;
    risk_level: string;
  };
}

interface NegotiationOpportunity {
  vendor_name: string;
  total_spend: number;
  invoice_count: number;
  tier: string;
  discount_range: [number, number];
  potential_savings: number;
  negotiation_points: string[];
  priority: string;
}

const COLORS = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#9334E9', '#00ACC1'];

export function VendorsPage() {
  const [analysis, setAnalysis] = useState<VendorAnalysis | null>(null);
  const [opportunities, setOpportunities] = useState<NegotiationOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [negotiationScript, setNegotiationScript] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [analysisRes, opportunitiesRes] = await Promise.all([
        api.get('/vendors/analysis'),
        api.get('/vendors/negotiations'),
      ]);
      setAnalysis(analysisRes.data);
      setOpportunities(opportunitiesRes.data.opportunities);
    } catch (error) {
      console.error('Failed to fetch vendor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNegotiationScript = async (vendorName: string) => {
    try {
      const res = await api.get(`/vendors/${encodeURIComponent(vendorName)}/negotiation-script`);
      setNegotiationScript(res.data);
      setSelectedVendor(vendorName);
    } catch (error) {
      console.error('Failed to fetch negotiation script:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const chartData = analysis?.top_vendors.slice(0, 8).map((v) => ({
    name: v.vendor_name.length > 15 ? v.vendor_name.slice(0, 15) + '...' : v.vendor_name,
    spend: v.total_spend,
    invoices: v.invoice_count,
  })) || [];

  const pieData = analysis?.top_vendors.slice(0, 6).map((v) => ({
    name: v.vendor_name,
    value: v.total_spend,
  })) || [];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Vendor Intelligence</h1>
        <p className="text-muted">
          Analyze vendor spending and discover negotiation opportunities
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner" />
        </div>
      ) : (
        <>
          {/* Stats */}
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <div className="stat-icon blue">
                <Users size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Total Vendors</p>
                <p className="stat-value">{analysis?.total_vendors || 0}</p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon green">
                <DollarSign size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Total Spend</p>
                <p className="stat-value">
                  ₹{(analysis?.total_spend || 0).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon yellow">
                <TrendingUp size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Top 5 Concentration</p>
                <p className="stat-value">{analysis?.concentration.top_5_percentage || 0}%</p>
              </div>
            </div>
            <div className="stat-card">
              <div className={`stat-icon ${analysis?.concentration.risk_level === 'high' ? 'red' : 'green'}`}>
                <AlertTriangle size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">Concentration Risk</p>
                <p className="stat-value" style={{ textTransform: 'capitalize' }}>
                  {analysis?.concentration.risk_level || 'Low'}
                </p>
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid-2 mb-6">
            <div className="card">
              <h3 className="card-title mb-4">Spend by Vendor</h3>
              <div style={{ height: 300 }}>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e8eaed" />
                      <XAxis dataKey="name" stroke="#5f6368" fontSize={11} />
                      <YAxis stroke="#5f6368" tickFormatter={(v) => `₹${v / 1000}k`} />
                      <Tooltip
                        formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Spend']}
                      />
                      <Bar dataKey="spend" fill="#4285F4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">No vendor data available</div>
                )}
              </div>
            </div>

            <div className="card">
              <h3 className="card-title mb-4">Spend Distribution</h3>
              <div style={{ height: 300 }}>
                {pieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {pieData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Spend']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-state">No data available</div>
                )}
              </div>
            </div>
          </div>

          {/* Negotiation Opportunities */}
          <div className="card mb-6">
            <div className="card-header">
              <div>
                <h3 className="card-title">💰 Negotiation Opportunities</h3>
                <p className="card-subtitle">AI-identified savings potential</p>
              </div>
              <span className="badge badge-success">
                <Sparkles size={12} style={{ marginRight: 4 }} />
                AI Powered
              </span>
            </div>

            {opportunities.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {opportunities.map((opp, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    style={{
                      padding: 16,
                      background: 'var(--bg-secondary)',
                      borderRadius: 12,
                      border: opp.priority === 'high' ? '1px solid var(--success)' : '1px solid var(--gray-200)',
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span
                          className={`badge ${
                            opp.tier === 'platinum'
                              ? 'badge-info'
                              : opp.tier === 'gold'
                              ? 'badge-warning'
                              : 'badge-success'
                          }`}
                        >
                          {opp.tier}
                        </span>
                        <span className="font-medium">{opp.vendor_name}</span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ color: 'var(--success)', fontWeight: 600 }}>
                          Save ₹{opp.potential_savings.toLocaleString('en-IN')}
                        </p>
                        <p className="text-xs text-muted">
                          {opp.discount_range[0]}-{opp.discount_range[1]}% discount
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="text-sm text-muted">
                        {opp.invoice_count} invoices • ₹{opp.total_spend.toLocaleString('en-IN')} total
                      </div>
                      <button
                        className="btn btn-secondary"
                        onClick={() => fetchNegotiationScript(opp.vendor_name)}
                      >
                        Get Script
                        <ChevronRight size={16} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted">
                No negotiation opportunities found. Process more invoices to discover savings.
              </div>
            )}
          </div>

          {/* Top Vendors Table */}
          <div className="card">
            <h3 className="card-title mb-4">Top Vendors</h3>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>GSTIN</th>
                    <th>Total Spend</th>
                    <th>% of Total</th>
                    <th>Invoices</th>
                    <th>Avg Invoice</th>
                    <th>Category</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis?.top_vendors.map((vendor, i) => (
                    <tr key={i}>
                      <td className="font-medium">{vendor.vendor_name}</td>
                      <td className="text-sm">{vendor.gstin || '-'}</td>
                      <td>₹{vendor.total_spend.toLocaleString('en-IN')}</td>
                      <td>{vendor.percentage_of_total}%</td>
                      <td>{vendor.invoice_count}</td>
                      <td>₹{vendor.average_invoice.toLocaleString('en-IN')}</td>
                      <td>
                        <span className="badge badge-info">{vendor.primary_category}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Negotiation Script Modal */}
      {selectedVendor && negotiationScript && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedVendor(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card"
            style={{ width: '90%', maxWidth: 600, maxHeight: '80vh', overflow: 'auto' }}
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="card-title">Negotiation Script: {selectedVendor}</h3>
              <button
                className="btn btn-secondary"
                onClick={() =>
                  copyToClipboard(
                    `Subject: ${negotiationScript.email_subject}\n\n${negotiationScript.email_body}`
                  )
                }
              >
                {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                {copied ? 'Copied!' : 'Copy Email'}
              </button>
            </div>

            <div style={{ marginBottom: 16 }}>
              <p className="text-xs text-muted mb-1">Subject:</p>
              <p className="font-medium">{negotiationScript.email_subject}</p>
            </div>

            <div style={{ marginBottom: 16 }}>
              <p className="text-xs text-muted mb-1">Email Body:</p>
              <div className="email-preview">{negotiationScript.email_body}</div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <p className="text-xs text-muted mb-2">Talking Points:</p>
              <ul style={{ paddingLeft: 20 }}>
                {negotiationScript.talking_points?.map((point: string, i: number) => (
                  <li key={i} style={{ marginBottom: 4, color: 'var(--text-secondary)' }}>
                    {point}
                  </li>
                ))}
              </ul>
            </div>

            <div
              style={{
                padding: 12,
                background: '#e6f4ea',
                borderRadius: 8,
                textAlign: 'center',
              }}
            >
              <p className="text-sm" style={{ color: 'var(--success)' }}>
                Suggested Discount: {negotiationScript.suggested_discount_percentage}%
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
