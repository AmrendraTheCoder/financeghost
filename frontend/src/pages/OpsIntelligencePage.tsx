import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import {
  AlertTriangle,
  Clock,
  CheckCircle,
  RefreshCw,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatCard, DashboardCard } from '../components/StatCard';
import {
  getMonthEndDashboard,
  getUrgentItems,
  getDailyBriefing,
} from '../api';
import type {
  MonthEndDashboard,
  UrgentWorkItem,
  DayBriefing,
  ClientWorkflowStatus,
} from '../api';

// Phase labels
const PHASE_CONFIG: Record<string, { label: string; color: string }> = {
  'not_started': { label: 'Not Started', color: 'var(--gray-400)' },
  'data_collection': { label: 'Data Collection', color: 'var(--google-blue)' },
  'reconciliation': { label: 'Reconciliation', color: 'var(--google-yellow)' },
  'review': { label: 'Review', color: 'var(--primary)' },
  'filing_ready': { label: 'Filing Ready', color: 'var(--google-green)' },
  'complete': { label: 'Complete', color: 'var(--success)' },
};

// Urgent Item Card Component with One-Click Actions
const UrgentActionCard = ({ item, onResolve }: { item: UrgentWorkItem; onResolve?: (id: string) => void }) => {
  const handleAction = (action: string) => {
    if (action === 'resolve' && onResolve) {
      onResolve(item.id);
    } else if (action === 'email') {
      window.open(`/emails?client=${encodeURIComponent(item.client_name)}`, '_blank');
    } else if (action === 'fix') {
      window.open(`/invoices?client=${encodeURIComponent(item.client_name)}`, '_blank');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className="card"
      style={{
        padding: '16px',
        marginBottom: '12px',
        borderLeft: `4px solid ${item.priority_score >= 80 ? 'var(--error)' : item.priority_score >= 60 ? 'var(--warning)' : 'var(--info)'}`,
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium" style={{ fontSize: '0.9rem' }}>
          {item.title}
        </h4>
        <span className={`badge ${item.priority_score >= 80 ? 'badge-error' : 'badge-warning'}`}>
          P{item.priority_score}
        </span>
      </div>
      <p className="text-sm text-muted mb-3" style={{ lineHeight: 1.4 }}>
        {item.description}
      </p>
      <div className="flex gap-2 flex-wrap mb-3">
        <span className="badge badge-info">{item.client_name}</span>
        {item.deadline && (
          <span className="badge badge-error">
            <Clock size={12} style={{ marginRight: 4 }} />
            {new Date(item.deadline).toLocaleDateString()}
          </span>
        )}
      </div>
      <div
        style={{
          padding: '10px 12px',
          background: 'var(--primary-light)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.85rem',
          color: 'var(--primary)',
          fontWeight: 500,
          marginBottom: '12px',
        }}
      >
        → {item.suggested_action}
      </div>
      {/* One-Click Action Buttons */}
      <div className="flex gap-2">
        <button
          className="btn btn-primary"
          style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          onClick={() => handleAction('fix')}
        >
          Fix Now
        </button>
        <button
          className="btn btn-secondary"
          style={{ padding: '6px 12px', fontSize: '0.75rem' }}
          onClick={() => handleAction('email')}
        >
          Email Vendor
        </button>
        <button
          className="btn btn-ghost"
          style={{ padding: '6px 12px', fontSize: '0.75rem', marginLeft: 'auto' }}
          onClick={() => handleAction('resolve')}
        >
          ✓ Resolved
        </button>
      </div>
    </motion.div>
  );
};

// Client Card Component
const ClientCard = ({ client }: { client: ClientWorkflowStatus }) => (
  <motion.div
    whileHover={{ y: -2, boxShadow: 'var(--shadow-md)' }}
    className="card"
    style={{ 
      padding: '12px', 
      marginBottom: '8px', 
      cursor: 'pointer',
      border: '1px solid var(--gray-200)',
    }}
  >
    <div className="flex items-center justify-between mb-2">
      <h4 style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)' }}>
        {client.client_name}
      </h4>
      <span 
        style={{ 
          fontSize: '0.6rem', 
          fontWeight: 600,
          padding: '2px 6px',
          borderRadius: 'var(--radius-sm)',
          background: client.risk.risk_level === 'low' ? '#e6f4ea' : client.risk.risk_level === 'medium' ? '#fef7e0' : '#fce8e6',
          color: client.risk.risk_level === 'low' ? 'var(--success)' : client.risk.risk_level === 'medium' ? '#b06000' : 'var(--error)',
        }}
      >
        {client.risk.risk_level.toUpperCase()}
      </span>
    </div>
    <div
      style={{
        background: 'var(--gray-200)',
        borderRadius: '2px',
        height: '4px',
        overflow: 'hidden',
        marginBottom: '6px',
      }}
    >
      <div
        style={{
          background: client.progress_percent >= 80 ? 'var(--success)' : client.progress_percent >= 50 ? 'var(--warning)' : 'var(--error)',
          height: '100%',
          width: `${client.progress_percent}%`,
          borderRadius: '2px',
        }}
      />
    </div>
    <div className="flex justify-between" style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
      <span>{client.progress_percent}%</span>
      <span>{client.pending_items.length} pending</span>
    </div>
  </motion.div>
);

// Kanban Column Component
const KanbanColumn = ({ phase, clients }: { phase: string; clients: ClientWorkflowStatus[] }) => {
  const config = PHASE_CONFIG[phase] || { label: phase, color: 'var(--gray-500)' };
  
  return (
    <div
      style={{
        background: 'var(--bg-primary)',
        borderRadius: 'var(--radius-md)',
        padding: '12px',
        minWidth: '160px',
        border: '1px solid var(--gray-200)',
      }}
    >
      <div 
        className="flex items-center justify-between mb-3 pb-2" 
        style={{ borderBottom: `2px solid ${config.color}` }}
      >
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {config.label}
        </span>
        <span
          style={{ 
            fontSize: '0.65rem', 
            fontWeight: 600,
            padding: '2px 6px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--gray-100)',
            color: 'var(--text-secondary)',
          }}
        >
          {clients.length}
        </span>
      </div>
      {clients.length === 0 ? (
        <p style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', textAlign: 'center', padding: '20px 0' }}>
          No clients
        </p>
      ) : (
        clients.map(client => <ClientCard key={client.client_id} client={client} />)
      )}
    </div>
  );
};

// Main Page Component
export default function OpsIntelligencePage() {
  const [dashboard, setDashboard] = useState<MonthEndDashboard | null>(null);
  const [briefing, setBriefing] = useState<DayBriefing | null>(null);
  const [urgentItems, setUrgentItems] = useState<UrgentWorkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  // Trigger confetti when all urgent items are resolved
  const triggerCelebration = () => {
    setShowCelebration(true);
    const duration = 3000;
    const end = Date.now() + duration;
    
    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#4285F4', '#34A853', '#FBBC05', '#EA4335']
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#4285F4', '#34A853', '#FBBC05', '#EA4335']
      });
      
      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };
    frame();
    
    setTimeout(() => setShowCelebration(false), 5000);
  };

  // Handle resolving an urgent item
  const handleResolveItem = (id: string) => {
    setUrgentItems(prev => {
      const newItems = prev.filter(item => item.id !== id);
      // Trigger celebration if all items are now resolved
      if (newItems.length === 0 && prev.length > 0) {
        triggerCelebration();
      }
      return newItems;
    });
  };

  // Speak the briefing using Web Speech API
  const speakBriefing = (text: string) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.volume = 0.8;
      
      // Try to use a good English voice
      const voices = window.speechSynthesis.getVoices();
      const englishVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'));
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
      
      window.speechSynthesis.speak(utterance);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardData, briefingData, urgentData] = await Promise.all([
        getMonthEndDashboard(),
        getDailyBriefing(),
        getUrgentItems()
      ]);
      setDashboard(dashboardData);
      setBriefing(briefingData);
      setUrgentItems(urgentData.items);
      
      // Speak the briefing headline after data loads
      if (briefingData?.headline) {
        // Small delay to ensure page is rendered
        setTimeout(() => {
          const briefingText = `Good morning. ${briefingData.headline}. You have ${urgentData.items.length} urgent items needing attention.`;
          speakBriefing(briefingText);
        }, 1000);
      }
    } catch (err) {
      console.error('Failed to load ops intelligence:', err);
      setError('Failed to load data. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // Group clients by phase
  const phases = ['not_started', 'data_collection', 'reconciliation', 'review', 'filing_ready', 'complete'];
  const groupedClients = phases.reduce((acc, phase) => {
    acc[phase] = dashboard?.clients_status.filter(c => c.phase === phase) || [];
    return acc;
  }, {} as Record<string, ClientWorkflowStatus[]>);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="page-content flex items-center justify-center"
        style={{ minHeight: '400px' }}
      >
        <div className="text-center">
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <p className="text-muted">Loading Ops Intelligence...</p>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="page-content flex items-center justify-center flex-col gap-4"
        style={{ minHeight: '400px' }}
      >
        <AlertTriangle size={48} style={{ color: 'var(--warning)' }} />
        <p className="text-muted">{error}</p>
        <button className="btn btn-primary" onClick={loadData}>
          <RefreshCw size={16} />
          Retry
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Ops Intelligence</h1>
          <p className="text-muted">Month-End Close Autopilot • {dashboard?.current_month}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={loadData}>
            <RefreshCw size={16} />
            Refresh
          </button>
          <Link to="/dashboard" className="btn btn-primary">
            Dashboard
            <ChevronRight size={16} />
          </Link>
        </div>
      </div>

      {/* AI Briefing Banner */}
      {briefing && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card mb-6"
          style={{
            background: 'linear-gradient(135deg, var(--primary) 0%, #edf2f9ff 100%)',
            color: 'white',
            border: 'none',
          }}
        >
          <div className="flex items-center gap-4">
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255,255,255,0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={24} />
            </div>
            <div style={{ flex: 1, color: 'white' }}>
              <p className="text-xs" style={{ color: 'white', opacity: 0.75, marginBottom: 4 }}>AI Daily Briefing</p>
              <p style={{ color: 'white', fontSize: '1.1rem', fontWeight: 500, lineHeight: 1.3 }}>{briefing.headline}</p>
            </div>
          </div>
          {briefing.key_points.length > 0 && (
            <div className="flex gap-3 flex-wrap mt-4 pt-4" style={{ borderTop: '1px solid rgba(255,255,255,0.2)' }}>
              {briefing.key_points.map((point, i) => (
                <span
                  key={i}
                  style={{
                    background: 'rgba(255,255,255,0.15)',
                    padding: '6px 12px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.8rem',
                  }}
                >
                  {point}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Stats Row */}
      <div className="stats-grid mb-6" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        <StatCard
          label="Overall Progress"
          value={`${dashboard?.overall_progress || 0}%`}
          icon="invoices"
        />
        <StatCard
          label="Health Score"
          value={dashboard?.risk_summary.overall_health_score || 0}
          icon="success"
        />
        <StatCard
          label="Total Clients"
          value={dashboard?.risk_summary.total_clients || 0}
          icon="amount"
        />
        <StatCard
          label="Urgent Items"
          value={urgentItems.length}
          icon="errors"
        />
        <StatCard
          label="High Risk"
          value={dashboard?.risk_summary.high_risk_clients || 0}
          icon="errors"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid-2" style={{ gridTemplateColumns: '1fr 380px' }}>
        {/* Kanban View */}
        <DashboardCard
          title="Month-End Progress"
          subtitle="Client workflow status by phase"
        >
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${phases.length}, 1fr)`,
              gap: '12px',
              overflowX: 'auto',
              paddingBottom: '8px',
            }}
          >
            {phases.map(phase => (
              <KanbanColumn key={phase} phase={phase} clients={groupedClients[phase]} />
            ))}
          </div>
        </DashboardCard>

        {/* Urgent Actions */}
        <div>
          <DashboardCard
            title="Attention Needed Now"
            subtitle="Items requiring immediate action"
            action={
              <span className="badge badge-error">{urgentItems.length}</span>
            }
          >
            {urgentItems.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle size={48} style={{ color: 'var(--success)', margin: '0 auto 12px' }} />
                <p className="text-muted">All clear! No urgent items.</p>
                {showCelebration && (
                  <motion.p
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{ marginTop: '12px', color: 'var(--success)', fontWeight: 600 }}
                  >
                    Great job! You've resolved all urgent items.
                  </motion.p>
                )}
              </div>
            ) : (
              <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {urgentItems.map(item => (
                  <UrgentActionCard key={item.id} item={item} onResolve={handleResolveItem} />
                ))}
              </div>
            )}
          </DashboardCard>

          {/* Bottlenecks */}
          {dashboard && dashboard.bottlenecks.length > 0 && (
            <div className="card mt-4" style={{ padding: '16px' }}>
              <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
                Bottlenecks
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {dashboard.bottlenecks.map((bottleneck, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '10px 12px',
                      background: 'var(--gray-50)',
                      borderRadius: 'var(--radius-sm)',
                      borderLeft: '3px solid var(--warning)',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {bottleneck}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
