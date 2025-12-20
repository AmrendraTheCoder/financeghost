import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  LineChart,
  Line,
} from 'recharts';
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Zap,
  RefreshCw,
  Calendar,
  AlertTriangle,
  DollarSign,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { StatCard, DashboardCard } from '../components/StatCard';
import { getDashboard, getDemo, api } from '../api';
import type { DashboardData } from '../api';

const COLORS = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#9334E9', '#00ACC1'];

interface CashForecast {
  next_7_days: number;
  next_14_days: number;
  next_30_days: number;
  critical_payments: number;
  trend: string;
  confidence: string;
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [cashForecast, setCashForecast] = useState<CashForecast | null>(null);
  const [_loading, setLoading] = useState(true);
  const [runningDemo, setRunningDemo] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboard, forecast] = await Promise.all([
        getDashboard(),
        api.get('/cashflow/summary').then((r) => r.data).catch(() => null),
      ]);
      setData(dashboard);
      setCashForecast(forecast);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const runDemoInvoice = async () => {
    setRunningDemo(true);
    try {
      await getDemo();
      await fetchData();
    } catch (error) {
      console.error('Demo failed:', error);
    } finally {
      setRunningDemo(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Transform data for charts
  const categoryData = data?.cashflow.category_breakdown?.categories
    ? Object.entries(data.cashflow.category_breakdown.categories).map(([name, info]) => ({
        name: name.length > 12 ? name.slice(0, 12) + '...' : name,
        fullName: name,
        value: info.amount,
        percentage: info.percentage,
      }))
    : [];

  const statusData = data?.summary?.by_status
    ? Object.entries(data.summary.by_status).map(([status, count]) => ({
        name: status.replace('_', ' '),
        value: count,
      }))
    : [];

  // Handle chart click for interactive exploration
  const handleCategoryClick = (data: any) => {
    if (data && data.fullName) {
      setSelectedCategory(data.fullName);
      // Navigate to invoices filtered by category
      navigate(`/invoices?category=${encodeURIComponent(data.fullName)}`);
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
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Dashboard</h1>
          <p className="text-muted">Overview of your invoice processing</p>
        </div>
        <div className="flex gap-2">
          <button
            className="btn btn-secondary"
            onClick={runDemoInvoice}
            disabled={runningDemo}
          >
            {runningDemo ? (
              <RefreshCw size={16} className="animate-spin" />
            ) : (
              <Zap size={16} />
            )}
            {runningDemo ? 'Processing...' : 'Run Demo'}
          </button>
          <Link to="/upload" className="btn btn-primary">
            Upload Invoice
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid mb-6">
        <StatCard
          label="Total Invoices"
          value={data?.summary?.total_invoices || 0}
          icon="invoices"
        />
        <StatCard
          label="Total Amount"
          value={data?.summary?.total_amount || 0}
          prefix="₹"
          icon="amount"
        />
        <StatCard
          label="Needs Review"
          value={data?.summary?.by_status?.needs_review || 0}
          icon="errors"
        />
        <StatCard
          label="Processed"
          value={data?.summary?.by_status?.processed || 0}
          icon="success"
        />
      </div>

      {/* Cash Flow Forecast Banner */}
      {cashForecast && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card mb-6"
          style={{
            background: 'linear-gradient(135deg, #e8f0fe 0%, #f0f9ff 50%, #e6f4ea 100%)',
            border: '1px solid #d2e3fc',
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 12,
                  background: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <Calendar size={28} style={{ color: 'var(--primary)' }} />
              </div>
              <div>
                <p className="text-sm text-muted">Predicted Cash Requirement (30 days)</p>
                <p style={{ fontSize: '1.75rem', fontWeight: 600, color: 'var(--primary)' }}>
                  ₹{cashForecast.next_30_days.toLocaleString('en-IN')}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div style={{ textAlign: 'center' }}>
                <p className="text-xs text-muted">7 Days</p>
                <p className="font-medium">₹{cashForecast.next_7_days.toLocaleString('en-IN')}</p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <p className="text-xs text-muted">14 Days</p>
                <p className="font-medium">₹{cashForecast.next_14_days.toLocaleString('en-IN')}</p>
              </div>
              <div
                style={{
                  padding: '8px 16px',
                  background: 'white',
                  borderRadius: 8,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                {cashForecast.trend === 'increasing' ? (
                  <TrendingUp size={18} style={{ color: 'var(--error)' }} />
                ) : cashForecast.trend === 'decreasing' ? (
                  <TrendingDown size={18} style={{ color: 'var(--success)' }} />
                ) : (
                  <DollarSign size={18} style={{ color: 'var(--info)' }} />
                )}
                <span className="text-sm font-medium" style={{ textTransform: 'capitalize' }}>
                  {cashForecast.trend}
                </span>
              </div>
              {cashForecast.critical_payments > 0 && (
                <div
                  style={{
                    padding: '8px 16px',
                    background: '#fef7e0',
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <AlertTriangle size={18} style={{ color: '#b06000' }} />
                  <span className="text-sm font-medium" style={{ color: '#b06000' }}>
                    {cashForecast.critical_payments} critical
                  </span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Charts Row */}
      <div className="grid-2 mb-6">
        {/* Spending by Category - Interactive */}
        <DashboardCard
          title="Spending by Category"
          subtitle="Click a segment to view invoices"
        >
          <div style={{ width: '100%', height: 300, minHeight: 300 }}>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    onClick={handleCategoryClick}
                    style={{ cursor: 'pointer' }}
                  >
                    {categoryData.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                        style={{
                          filter:
                            selectedCategory === categoryData[index].fullName
                              ? 'brightness(1.2)'
                              : 'none',
                          transition: 'all 0.2s ease',
                        }}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => [`₹${Number(value).toLocaleString('en-IN')}`, 'Amount']}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{ height: 300 }}>
                No data yet. Upload invoices to see breakdown.
              </div>
            )}
          </div>
        </DashboardCard>

        <DashboardCard
          title="Invoice Status"
          subtitle="Processing status breakdown"
        >
          <div style={{ width: '100%', height: 300, minHeight: 300 }}>
            {statusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    <Cell fill="#34A853" />
                    <Cell fill="#FBBC05" />
                    <Cell fill="#EA4335" />
                    <Cell fill="#4285F4" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{ height: 300 }}>
                No invoices processed yet.
              </div>
            )}
          </div>
        </DashboardCard>
      </div>

      {/* Quick Actions */}
      <div className="grid-3 mb-6">
        <Link to="/vendors" style={{ textDecoration: 'none' }}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="card"
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #4285F4, #34A853)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 12,
              }}
            >
              <span style={{ fontSize: 24 }}>💰</span>
            </div>
            <h4 className="font-medium mb-1">Vendor Negotiations</h4>
            <p className="text-sm text-muted">
              Discover savings opportunities with AI-powered negotiation scripts
            </p>
          </motion.div>
        </Link>

        <Link to="/audit" style={{ textDecoration: 'none' }}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="card"
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #FBBC05, #EA4335)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 12,
              }}
            >
              <span style={{ fontSize: 24 }}>🛡️</span>
            </div>
            <h4 className="font-medium mb-1">Audit Defense</h4>
            <p className="text-sm text-muted">
              Download compliance reports and audit-ready documentation
            </p>
          </motion.div>
        </Link>

        <Link to="/emails" style={{ textDecoration: 'none' }}>
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="card"
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: 'linear-gradient(135deg, #9334E9, #4285F4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 12,
              }}
            >
              <span style={{ fontSize: 24 }}>📧</span>
            </div>
            <h4 className="font-medium mb-1">Vendor Emails</h4>
            <p className="text-sm text-muted">
              View and send AI-generated correction emails to vendors
            </p>
          </motion.div>
        </Link>
      </div>

      {/* Recent Invoices */}
      <DashboardCard
        title="Recent Invoices"
        subtitle="Latest processed invoices"
        action={
          <Link to="/invoices" className="btn btn-ghost text-sm">
            View All
            <ArrowRight size={14} />
          </Link>
        }
      >
        {data?.recent_invoices && data.recent_invoices.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_invoices.slice(0, 5).map((inv: any, i: number) => (
                  <tr key={i} style={{ cursor: 'pointer' }} onClick={() => navigate('/invoices')}>
                    <td className="font-medium">{inv.invoice_number || 'N/A'}</td>
                    <td>{inv.vendor_name || 'Unknown'}</td>
                    <td>₹{(inv.total_amount || 0).toLocaleString('en-IN')}</td>
                    <td>
                      <span
                        className={`badge ${
                          inv.status === 'processed'
                            ? 'badge-success'
                            : inv.status === 'needs_review'
                            ? 'badge-warning'
                            : 'badge-info'
                        }`}
                      >
                        {inv.status?.replace('_', ' ') || 'pending'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-muted py-8">
            No invoices yet. Upload your first invoice to get started.
          </div>
        )}
      </DashboardCard>

      {/* Cash Flow Prediction */}
      {data?.cashflow?.predictions && (
        <DashboardCard
          title="Cash Flow Prediction"
          subtitle="AI-powered expense forecast"
        >
          <div className="flex items-center gap-8 py-4">
            <div>
              <p className="text-sm text-muted">Next Month Estimate</p>
              <p style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--primary)' }}>
                ₹{data.cashflow.predictions.next_month_estimate.toLocaleString('en-IN')}
              </p>
            </div>
            <div
              style={{
                padding: '8px 16px',
                background: data.cashflow.predictions.confidence === 'high' 
                  ? '#e6f4ea' 
                  : data.cashflow.predictions.confidence === 'medium'
                  ? '#fef7e0'
                  : '#f1f3f4',
                borderRadius: 8,
              }}
            >
              <p className="text-xs text-muted">Confidence</p>
              <p className="font-medium" style={{ textTransform: 'capitalize' }}>
                {data.cashflow.predictions.confidence}
              </p>
            </div>
          </div>
        </DashboardCard>
      )}
    </motion.div>
  );
}
