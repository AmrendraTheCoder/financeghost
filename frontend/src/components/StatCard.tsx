import type { ReactNode } from 'react';
import {
  FileText,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon: 'invoices' | 'amount' | 'errors' | 'success';
  prefix?: string;
}

const iconMap = {
  invoices: { icon: FileText, color: 'blue' },
  amount: { icon: DollarSign, color: 'green' },
  errors: { icon: AlertTriangle, color: 'yellow' },
  success: { icon: CheckCircle, color: 'green' },
};

export function StatCard({ label, value, change, icon, prefix }: StatCardProps) {
  const { icon: Icon, color } = iconMap[icon];

  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>
        <Icon size={24} />
      </div>
      <div className="stat-content">
        <p className="stat-label">{label}</p>
        <p className="stat-value">
          {prefix}
          {typeof value === 'number' ? value.toLocaleString('en-IN') : value}
        </p>
        {change !== undefined && (
          <p className={`stat-change ${change >= 0 ? 'positive' : 'negative'}`}>
            {change >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {' '}
            {Math.abs(change)}% from last month
          </p>
        )}
      </div>
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
}

export function DashboardCard({ title, subtitle, children, action }: DashboardCardProps) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">{title}</h3>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}
