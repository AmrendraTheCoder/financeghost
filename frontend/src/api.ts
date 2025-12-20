import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Invoice {
  id: number;
  invoice_number: string;
  invoice_date: string;
  vendor_name: string;
  vendor_gstin: string | null;
  total_amount: number;
  total_tax: number;
  subtotal: number;
  status: string;
  expense_category: string | null;
  errors_json: string;
  items_json: string;
  created_at: string;
}

export interface ProcessingResponse {
  success: boolean;
  invoice_id: number | null;
  invoice_number: string | null;
  vendor_name: string | null;
  total_amount: number | null;
  status: string | null;
  errors_count: number;
  has_email: boolean;
  generated_email: string | null;
  processing_time_ms: number;
  message: string;
}

export interface DashboardData {
  summary: {
    total_invoices: number;
    total_amount: number;
    by_status: Record<string, number>;
    by_category: Record<string, number>;
  };
  cashflow: {
    monthly_summary: {
      current_month: string;
      current_total: number;
      average_monthly: number;
      trend: string;
    };
    category_breakdown: {
      total: number;
      categories: Record<string, { amount: number; percentage: number }>;
    };
    predictions: {
      next_month_estimate: number;
      confidence: string;
    };
  };
  recent_invoices: Invoice[];
}

// API Functions
export const uploadInvoice = async (file: File, companyName?: string): Promise<ProcessingResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (companyName) {
    formData.append('company_name', companyName);
  }
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const processText = async (text: string, companyName?: string): Promise<ProcessingResponse> => {
  const response = await api.post('/process-text', {
    text,
    company_name: companyName || 'FinanceGhost User',
  });
  return response.data;
};

export const getInvoices = async (limit = 100, offset = 0): Promise<{ invoices: Invoice[]; count: number }> => {
  const response = await api.get('/invoices', {
    params: { limit, offset },
  });
  return response.data;
};

export const getInvoice = async (id: number): Promise<Invoice> => {
  const response = await api.get(`/invoices/${id}`);
  return response.data;
};

export const getDashboard = async (): Promise<DashboardData> => {
  const response = await api.get('/dashboard');
  return response.data;
};

export const getDemo = async () => {
  const response = await api.get('/demo');
  return response.data;
};

export const getEmails = async (invoiceId?: number) => {
  const response = await api.get('/emails', {
    params: invoiceId ? { invoice_id: invoiceId } : {},
  });
  return response.data;
};

// ============================================
// Firm Intelligence API Functions (NEW)
// ============================================

export interface RiskLevel {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  reasons: string[];
  suggested_actions: string[];
  affected_invoices: string[];
  deadline?: string;
}

export interface UrgentWorkItem {
  id: string;
  type: string;
  client_name: string;
  title: string;
  description: string;
  reason: string;
  priority_score: number;
  deadline?: string;
  suggested_action: string;
  invoice_ids: string[];
  created_at: string;
}

export interface ClientWorkflowStatus {
  client_id: string;
  client_name: string;
  phase: string;
  progress_percent: number;
  risk: RiskLevel;
  pending_items: string[];
  last_updated: string;
  assigned_to?: string;
  notes?: string;
}

export interface FirmRiskDashboard {
  total_clients: number;
  high_risk_clients: number;
  medium_risk_clients: number;
  low_risk_clients: number;
  urgent_items_count: number;
  upcoming_deadlines: number;
  overall_health_score: number;
  risk_trend: string;
  generated_at: string;
}

export interface MonthEndDashboard {
  current_month: string;
  overall_progress: number;
  clients_status: ClientWorkflowStatus[];
  urgent_items: UrgentWorkItem[];
  risk_summary: FirmRiskDashboard;
  ai_briefing: string;
  bottlenecks: string[];
  generated_at: string;
}

export interface DayBriefing {
  briefing_date: string;
  headline: string;
  key_points: string[];
  urgent_actions: string[];
  risks_to_watch: string[];
  positive_notes: string[];
  full_briefing: string;
}

export const getFirmIntelligence = async () => {
  const response = await api.get('/firm/intelligence');
  return response.data;
};

export const getMonthEndDashboard = async (): Promise<MonthEndDashboard> => {
  const response = await api.get('/firm/month-end');
  return response.data;
};

export const getUrgentItems = async (): Promise<{ items: UrgentWorkItem[]; count: number }> => {
  const response = await api.get('/firm/urgent');
  return response.data;
};

export const getDailyBriefing = async (): Promise<DayBriefing> => {
  const response = await api.get('/firm/briefing');
  return response.data;
};

export const getClientRisk = async (clientId: string): Promise<RiskLevel> => {
  const response = await api.get(`/clients/${clientId}/risk`);
  return response.data;
};
