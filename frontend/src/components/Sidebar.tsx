import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Mail,
  Settings,
  HelpCircle,
  Zap,
  Users,
  Shield,
  Activity,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Ops Intelligence', icon: Activity },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/upload', label: 'Upload Invoice', icon: Upload },
  { path: '/invoices', label: 'Invoices', icon: FileText },
  { path: '/emails', label: 'Vendor Emails', icon: Mail },
  { path: '/vendors', label: 'Vendor Intelligence', icon: Users },
  { path: '/audit', label: 'Audit Defense', icon: Shield },
];

const bottomItems = [
  { path: '/settings', label: 'Settings', icon: Settings },
  { path: '/help', label: 'Help', icon: HelpCircle },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--gray-200)' }}>
        <div className="flex items-center gap-3">
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              FinanceGhost
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Autonomous AI
            </p>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <nav style={{ flex: 1, padding: '16px 12px' }}>
        <ul style={{ listStyle: 'none' }}>
          {navItems.map((item) => (
            <li key={item.path} style={{ marginBottom: 4 }}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'active' : ''}`
                }
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 16px',
                  borderRadius: 8,
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  background: isActive ? 'var(--primary-light)' : 'transparent',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  transition: 'all 0.2s ease',
                })}
              >
                <item.icon size={20} />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Autonomous Agent Status */}
        <div
          style={{
            margin: '24px 0',
            padding: 16,
            background: 'linear-gradient(135deg, #e8f0fe, #f0f9ff)',
            borderRadius: 12,
            border: '1px solid #d2e3fc',
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Zap size={16} style={{ color: '#1a73e8' }} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1a73e8' }}>
              AI AGENTS
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: '#34A853',
                animation: 'pulse 2s infinite',
              }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              5 agents active
            </span>
          </div>
          <div style={{ marginTop: 8, fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
            Invoice • Tax • Cashflow • Risk • Workflow
          </div>
        </div>

        {/* Feature Highlights */}
        <div
          style={{
            padding: 12,
            background: 'var(--bg-secondary)',
            borderRadius: 8,
            fontSize: '0.7rem',
          }}
        >
          <p style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>
            ✨ New Features
          </p>
          <ul style={{ listStyle: 'none', color: 'var(--text-secondary)' }}>
            <li style={{ marginBottom: 4 }}>📊 Ops Intelligence</li>
            <li style={{ marginBottom: 4 }}>👻 Ghost Mode Terminal</li>
            <li style={{ marginBottom: 4 }}>🎙️ Voice Commands</li>
            <li>🛡️ Audit Defense Pack</li>
          </ul>
        </div>
      </nav>

      {/* Bottom Navigation */}
      <div style={{ padding: '16px 12px', borderTop: '1px solid var(--gray-200)' }}>
        <ul style={{ listStyle: 'none' }}>
          {bottomItems.map((item) => (
            <li key={item.path} style={{ marginBottom: 4 }}>
              <NavLink
                to={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '10px 16px',
                  borderRadius: 8,
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  transition: 'all 0.2s ease',
                }}
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
