// -----------------------------------------------------------------------------
// File: api.ts
// Description: Frontend API client wrappers for Dou services
// -----------------------------------------------------------------------------

import axios, { AxiosError, AxiosInstance } from 'axios';

/**
 * Extract an error message from auth/API errors.
 */
export function getAuthErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const parts = detail.map((d: { loc?: string[]; msg?: string }) => {
        const msg = d?.msg ?? String(d);
        const loc = Array.isArray(d?.loc) ? d.loc.filter((x) => x !== 'body').join('.') : '';
        return loc ? `${loc}: ${msg}` : msg;
      });
      return parts.length ? parts.join('; ') : fallback;
    }
    if (detail && typeof detail === 'object') return (detail as { message?: string }).message ?? fallback;
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;

  // Use real JWT from login when present (required for RBAC: admin/approver/finance must be recognized).
  const stored = localStorage.getItem('token') || getCookie('token');
  if (stored) return stored;

  // In development only: when no token, use dev mock so unauthenticated dev still works.
  // The auth service's get_current_user() accepts tokens starting with "dev_mock_token".
  if (process.env.NODE_ENV === 'development') {
    return 'dev_mock_token_local';
  }

  return null;
}

function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

function createClient(baseURL: string, opts?: { enableRefresh?: boolean }): AxiosInstance {
  const client = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  });

  client.interceptors.request.use((config) => {
    const token = getAuthToken();
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Best-effort refresh flow: if we have a refresh token, try once on 401.
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest: any = error.config;
      const status = error.response?.status;

      const enableRefresh = opts?.enableRefresh !== false;
      const url = (originalRequest?.url || '') as string;

      if (!enableRefresh || status !== 401 || !originalRequest || originalRequest._retry) {
        throw error;
      }

      // Don't try to refresh for auth endpoints themselves.
      if (url.includes('/api/v1/auth/login') || url.includes('/api/v1/auth/signup') || url.includes('/api/v1/auth/refresh')) {
        throw error;
      }

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        throw error;
      }

      originalRequest._retry = true;

      try {
        const refreshed = await authAPI.refresh(refreshToken);
        const newAccessToken = refreshed?.access_token;
        if (newAccessToken && typeof window !== 'undefined') {
          localStorage.setItem('token', newAccessToken);
          document.cookie = `token=${encodeURIComponent(newAccessToken)}; path=/; max-age=${30 * 60}; SameSite=Lax`;
        }
        return client(originalRequest);
      } catch {
        // If refresh fails, fall back to original error.
        throw error;
      }
    }
  );

  return client;
}

// Default URLs (match docker-compose ports)
const AUTH_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
const EXPENSE_API_URL = process.env.NEXT_PUBLIC_EXPENSE_API_URL || 'http://localhost:8002';
const ADMIN_API_URL = process.env.NEXT_PUBLIC_ADMIN_API_URL || 'http://localhost:8003';
const AUDIT_API_URL = process.env.NEXT_PUBLIC_AUDIT_API_URL || 'http://localhost:8004';
const FILE_API_URL = process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8005';
const OCR_API_URL = process.env.NEXT_PUBLIC_OCR_API_URL || 'http://localhost:8006';
const LLM_API_URL = process.env.NEXT_PUBLIC_LLM_API_URL || 'http://localhost:8007';
const POLICY_API_URL = process.env.NEXT_PUBLIC_POLICY_API_URL || 'http://localhost:8008';
const REPORT_API_URL = process.env.NEXT_PUBLIC_REPORT_API_URL || 'http://localhost:8009';
// In browser, use Next.js proxy to avoid CORS and connection refused; server can hit backend directly
const reportBaseURL = typeof window !== 'undefined' ? '/api/reports' : REPORT_API_URL;
const ANOMALY_API_URL = process.env.NEXT_PUBLIC_ANOMALY_API_URL || 'http://localhost:8010';
const RAG_API_URL = process.env.NEXT_PUBLIC_RAG_API_URL || 'http://localhost:8018';
const ERP_API_URL = process.env.NEXT_PUBLIC_ERP_API_URL || 'http://localhost:8011';
const GDPR_API_URL = process.env.NEXT_PUBLIC_GDPR_API_URL || 'http://localhost:8012';
const PERFORMANCE_API_URL = process.env.NEXT_PUBLIC_PERFORMANCE_API_URL || 'http://localhost:8013';
const SECURITY_API_URL = process.env.NEXT_PUBLIC_SECURITY_API_URL || 'http://localhost:8014';
const MONITORING_API_URL = process.env.NEXT_PUBLIC_MONITORING_API_URL || 'http://localhost:8015';
const ACCOUNTING_API_URL = process.env.NEXT_PUBLIC_ACCOUNTING_API_URL || 'http://localhost:8019';
const DOSSIER_API_URL = process.env.NEXT_PUBLIC_DOSSIER_API_URL || 'http://localhost:8023';
const NOTIFICATION_API_URL = process.env.NEXT_PUBLIC_NOTIFICATION_API_URL || 'http://localhost:8024';
const BANKING_API_URL = process.env.NEXT_PUBLIC_BANKING_API_URL || 'http://localhost:8025';
const TAX_API_URL = process.env.NEXT_PUBLIC_TAX_API_URL || 'http://localhost:8026';
const ANALYSIS_API_URL = process.env.NEXT_PUBLIC_ANALYSIS_API_URL || 'http://localhost:8027';
const EINVOICE_API_URL = process.env.NEXT_PUBLIC_EINVOICE_API_URL || 'http://localhost:8028';
const PAYROLL_API_URL = process.env.NEXT_PUBLIC_PAYROLL_API_URL || 'http://localhost:8029';
const COLLECTION_API_URL = process.env.NEXT_PUBLIC_COLLECTION_API_URL || 'http://localhost:8030';
const AGENTS_API_URL = process.env.NEXT_PUBLIC_AGENTS_API_URL || 'http://localhost:8031';

const authClient = createClient(AUTH_API_URL, { enableRefresh: false });
const expensesClient = createClient(EXPENSE_API_URL);
const auditClient = createClient(AUDIT_API_URL);
const policyClient = createClient(POLICY_API_URL);
const reportClient = createClient(reportBaseURL);
const anomalyClient = createClient(ANOMALY_API_URL);
const monitoringClient = createClient(MONITORING_API_URL);
const fileClient = createClient(FILE_API_URL);
const adminClient = createClient(ADMIN_API_URL);
const ragClient = createClient(RAG_API_URL);
const accountingClient = createClient(ACCOUNTING_API_URL);
const dossierClient = createClient(DOSSIER_API_URL);
const notificationClient = createClient(NOTIFICATION_API_URL);
const bankingClient = createClient(BANKING_API_URL);
const taxClient = createClient(TAX_API_URL);
const analysisClient = createClient(ANALYSIS_API_URL);
const einvoiceClient = createClient(EINVOICE_API_URL);
const payrollClient = createClient(PAYROLL_API_URL);
const collectionClient = createClient(COLLECTION_API_URL);
const agentsClient = createClient(AGENTS_API_URL);

export const authAPI = {
  login: async (email: string, password: string) => {
    const res = await authClient.post('/api/v1/auth/login', { email, password });
    return res.data?.data ?? res.data;
  },
  signup: async (email: string, password: string, first_name?: string, last_name?: string) => {
    const res = await authClient.post('/api/v1/auth/signup', { email, password, first_name, last_name });
    return res.data?.data ?? res.data;
  },
  logout: async () => {
    const res = await authClient.post('/api/v1/auth/logout');
    return res.data?.data ?? res.data;
  },
  me: async () => {
    const res = await authClient.get('/api/v1/auth/me');
    return res.data ?? res.data?.data;
  },
  refresh: async (refresh_token: string) => {
    const res = await authClient.post('/api/v1/auth/refresh', { refresh_token });
    return res.data;
  },
  forgotPassword: async (email: string) => {
    const res = await authClient.post('/api/v1/auth/forgot-password', { email });
    return res.data?.data ?? res.data;
  },
  resetPassword: async (token: string, new_password: string) => {
    const res = await authClient.post('/api/v1/auth/reset-password', { token, new_password });
    return res.data?.data ?? res.data;
  },
};

export const expensesAPI = {
  list: async (params?: { page?: number; page_size?: number; status?: string; start_date?: string; end_date?: string }) => {
    const res = await expensesClient.get('/api/v1/expenses', { params });
    return res.data;
  },
  pendingApprovals: async (params?: { page?: number; page_size?: number }) => {
    const res = await expensesClient.get('/api/v1/expenses/pending-approvals', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await expensesClient.get(`/api/v1/expenses/${id}`);
    return res.data;
  },
  create: async (payload: any) => {
    const res = await expensesClient.post('/api/v1/expenses', payload);
    return res.data?.data ?? res.data;
  },
  update: async (id: string, payload: any) => {
    const res = await expensesClient.put(`/api/v1/expenses/${id}`, payload);
    return res.data;
  },
  delete: async (id: string) => {
    const res = await expensesClient.delete(`/api/v1/expenses/${id}`);
    return res.data;
  },
  submit: async (id: string) => {
    const res = await expensesClient.post(`/api/v1/expenses/${id}/submit`);
    return res.data;
  },
  approve: async (id: string, notes?: string) => {
    const res = await expensesClient.post(`/api/v1/expenses/${id}/approve`, { notes });
    return res.data;
  },
  reject: async (id: string, reason: string) => {
    const res = await expensesClient.post(`/api/v1/expenses/${id}/reject`, { reason });
    return res.data;
  },
};

export const fileAPI = {
  upload: async (file: File, expense_id?: string) => {
    const form = new FormData();
    form.append('file', file);
    if (expense_id) {
      form.append('expense_id', expense_id);
    }

    // In browser: use Next.js proxy to avoid CORS (localhost:3000 → file service 8005).
    // Use /api/file/upload to avoid 404: /api/receipts/upload can be matched by
    // /api/receipts/[receiptId] with receiptId="upload" (GET-only) in some setups.
    if (typeof window !== 'undefined') {
      const axiosRes = await axios.post('/api/file/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return axiosRes.data;
    }

    // Fallback: direct call to file service (used only in server contexts)
    const res = await fileClient.post('/api/v1/receipts/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: expense_id ? { expense_id } : undefined,
    });
    return res.data;
  },
  getReceipt: async (receiptId: string) => {
    // In browser, use Next.js proxy to avoid CORS (frontend localhost:3000 → file service localhost:8005)
    if (typeof window !== 'undefined') {
      const axiosRes = await axios.get(`/api/receipts/${receiptId}`);
      return axiosRes.data;
    }
    const res = await fileClient.get(`/api/v1/receipts/${receiptId}`);
    return res.data;
  },
  getReceiptStatus: async (receiptId: string) => {
    // In browser, use Next.js proxy to avoid CORS
    if (typeof window !== 'undefined') {
      const axiosRes = await axios.get(`/api/receipts/${receiptId}/status`);
      return axiosRes.data;
    }
    const res = await fileClient.get(`/api/v1/receipts/${receiptId}/status`);
    return res.data;
  },
  getDownloadUrl: async (receiptId: string, expires_in = 3600) => {
    const res = await fileClient.get(`/api/v1/receipts/${receiptId}/download`, { params: { expires_in } });
    return res.data;
  },
  deleteReceipt: async (receiptId: string) => {
    const res = await fileClient.delete(`/api/v1/receipts/${receiptId}`);
    return res.data;
  },
};

export const policyAPI = {
  evaluate: async (expenseId: string) => {
    const res = await policyClient.post('/api/v1/policies/evaluate', null, { params: { expense_id: expenseId } });
    return res.data;
  },
};

export const anomalyAPI = {
  analyze: async (expenseId: string) => {
    const res = await anomalyClient.post(`/api/v1/anomaly/analyze/${expenseId}`);
    return res.data;
  },
  train: async () => {
    const res = await anomalyClient.post('/api/v1/anomaly/train');
    return res.data;
  },
  dashboard: async (params?: {
    limitEmployees?: number;
    limitMerchants?: number;
    limitTransactions?: number;
    minRiskScore?: number;
  }) => {
    const res = await anomalyClient.get('/api/v1/anomaly/dashboard', { params });
    return res.data;
  },
  topMerchants: async (params?: { limit?: number; days_back?: number; sort_by?: string }) => {
    const res = await anomalyClient.get('/api/v1/anomaly/merchants', { params });
    return res.data;
  },
  merchantProfile: async (merchantName: string, daysBack = 90) => {
    const res = await anomalyClient.get(`/api/v1/anomaly/merchants/${encodeURIComponent(merchantName)}`, {
      params: { days_back: daysBack },
    });
    return res.data;
  },
  merchantSpendAnalysis: async (daysBack = 90) => {
    const res = await anomalyClient.get('/api/v1/anomaly/merchants/analysis/spend', { params: { days_back: daysBack } });
    return res.data;
  },
};

export const auditAPI = {
  dashboard: async (params?: { start_date?: string; end_date?: string }) => {
    const res = await auditClient.get('/api/v1/audit/dashboard', { params });
    return res.data;
  },
  logs: async (params?: { page?: number; page_size?: number }) => {
    const res = await auditClient.get('/api/v1/audit/logs', { params });
    return res.data;
  },
  createReport: async (payload: any) => {
    const res = await auditClient.post('/api/v1/audit/reports', payload);
    return res.data;
  },
  listReports: async (params?: { limit?: number; offset?: number; status?: string; page?: number; page_size?: number }) => {
    // Frontend pages pass page/page_size sometimes; map to offset/limit for the backend endpoint.
    const mappedParams =
      params?.page && params?.page_size
        ? {
            limit: params.page_size,
            offset: (params.page - 1) * params.page_size,
            status: params.status,
          }
        : params;
    const res = await auditClient.get('/api/v1/audit/reports', { params: mappedParams });
    return res.data;
  },
  getReport: async (reportId: string) => {
    const res = await auditClient.get(`/api/v1/audit/reports/${reportId}`);
    return res.data;
  },
  /** Expense reports submitted for approval – for auditor review on Audit Reports page */
  pendingExpenseReports: async (params?: { status?: string; limit?: number; offset?: number }) => {
    const res = await auditClient.get('/api/v1/audit/pending-expense-reports', { params });
    return Array.isArray(res.data) ? res.data : [];
  },
  /**
   * Generate basic report. Supports both:
   * - generateBasicReport({ period_start, period_end, expense_ids })
   * - generateBasicReport(period_start, period_end, expense_ids?)
   */
  generateBasicReport: async (
    ...args:
      | [{ period_start: string; period_end: string; expense_ids?: string[] }]
      | [string, string, string[]?]
  ) => {
    const payload =
      typeof args[0] === 'string'
        ? { period_start: args[0], period_end: args[1], expense_ids: args[2] }
        : args[0];
    const res = await auditClient.post('/api/v1/audit/reports/generate-basic', payload);
    return res.data;
  },
  /**
   * Generate narrative. Supports both:
   * - generateNarrative({ report_id, report_data, period_start, period_end })
   * - generateNarrative(period_start, period_end, report_id, report_data)
   */
  generateNarrative: async (
    ...args:
      | [
          {
            report_id?: string;
            report_data?: any;
            period_start?: string;
            period_end?: string;
          }
        ]
      | [string, string, string, any]
  ) => {
    const payload =
      typeof args[0] === 'string'
        ? { period_start: args[0], period_end: args[1], report_id: args[2], report_data: args[3] }
        : args[0];
    const res = await auditClient.post('/api/v1/audit/reports/generate-narrative', payload);
    return res.data;
  },
};

export const reportAPI = {
  list: async (params?: { page?: number; page_size?: number; status?: string }) => {
    const res = await reportClient.get('/api/v1/reports', { params });
    const data = res.data?.data ?? res.data;
    const total = res.data?.total ?? (Array.isArray(data) ? data.length : 0);
    const page = res.data?.page ?? 1;
    const page_size = res.data?.page_size ?? 20;
    return { data: Array.isArray(data) ? data : [], total, page, page_size };
  },
  get: async (id: string) => {
    const res = await reportClient.get(`/api/v1/reports/${id}`);
    const raw = res.data?.data ?? res.data;
    return { data: raw, ...res.data };
  },
  /** Get expenses included in a report */
  getExpenses: async (reportId: string) => {
    const res = await reportClient.get(`/api/v1/reports/${reportId}/expenses`);
    const data = res.data?.data ?? res.data;
    return Array.isArray(data) ? data : [];
  },
  create: async (payload: any) => {
    const res = await reportClient.post('/api/v1/reports', payload);
    return res.data;
  },
  update: async (id: string, payload: any) => {
    const res = await reportClient.put(`/api/v1/reports/${id}`, payload);
    return res.data;
  },
  submit: async (id: string, notes = '') => {
    const res = await reportClient.post(`/api/v1/reports/${id}/submit`, { notes });
    return res.data;
  },
  approve: async (id: string, notes = '') => {
    const res = await reportClient.post(`/api/v1/reports/${id}/approve`, { notes });
    return res.data;
  },
  reject: async (id: string, reason: string) => {
    const res = await reportClient.post(`/api/v1/reports/${id}/reject`, { reason });
    return res.data;
  },
  /** Export report as CSV or Excel; returns blob URL for download */
  export: async (id: string, format: 'csv' | 'excel' = 'csv') => {
    const res = await reportClient.get(`/api/v1/reports/${id}/export`, {
      params: { format: format === 'excel' ? 'excel' : 'csv' },
      responseType: 'blob',
    });
    return res.data as Blob;
  },
};

export const monitoringAPI = {
  getServiceHealth: async () => {
    const res = await monitoringClient.get('/api/v1/monitoring/health');
    return res.data;
  },
  getActiveAlerts: async () => {
    const res = await monitoringClient.get('/api/v1/monitoring/alerts');
    return res.data;
  },
  getSLOs: async () => {
    const res = await monitoringClient.get('/api/v1/monitoring/slos');
    return res.data;
  },
  getSLOCompliance: async (sloId: string) => {
    const res = await monitoringClient.get(`/api/v1/monitoring/slos/${sloId}/compliance`);
    return res.data;
  },
};

// Export placeholders for services not yet used by the current UI.
/** User as returned by admin users/roles APIs */
export interface AdminUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  status: string;
  roles?: { id: string; name: string }[];
}

/** Role as returned by admin roles API */
export interface AdminRole {
  id: string;
  name: string;
  description?: string;
  is_system_role?: boolean;
  user_count?: number;
  permission_ids?: string[];
}

/** Permission as returned by admin permissions API */
export interface AdminPermission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
}

/** Activity item as returned by admin activity API */
export interface AdminActivityItem {
  id: string;
  action: string;
  action_label: string;
  performed_by_id: string;
  performed_by_email: string;
  performed_by_name: string;
  target_user_id: string | null;
  target_user_email: string | null;
  target_user_name: string | null;
  target_role_name: string;
  details: Record<string, unknown>;
  created_at: string | null;
}

/** Expense category as returned by admin categories API */
export interface AdminCategory {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  description: string | null;
  gl_account_id: string | null;
  is_active: boolean;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

/** GL account as returned by admin gl-accounts API */
export interface AdminGLAccount {
  id: string;
  tenant_id: string;
  account_code: string;
  account_name: string;
  account_type: string;
  description: string | null;
  is_active: boolean;
  parent_account_id: string | null;
  created_at: string;
  updated_at: string;
}

/** Expense policy as returned by admin policies API */
export interface AdminPolicy {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  policy_type: string;
  policy_rules: Record<string, unknown>;
  applies_to_roles: string[];
  is_active: boolean;
  effective_from: string | null;
  effective_until: string | null;
  created_at: string;
  updated_at: string;
}

export const adminAPI = {
  /**
   * Admin service: users
   * Backend returns: { success: true, data: { users, total, page, page_size } }
   * Supports optional search, role_id, status query params.
   */
  users: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    role_id?: string;
    status?: string;
  }) => {
    const res = await adminClient.get('/api/v1/admin/users', { params });
    return { data: res.data?.data ?? res.data };
  },
  /** Get a single user with roles (for edit form). */
  getUser: async (userId: string) => {
    const res = await adminClient.get(`/api/v1/admin/users/${userId}`);
    return res.data?.data ?? res.data;
  },
  /** List roles for the tenant (includes permission_ids for matrix). */
  roles: async () => {
    const res = await adminClient.get('/api/v1/admin/roles');
    return res.data?.data ?? res.data;
  },
  /** List all permissions (for Roles & Permissions matrix). */
  permissions: async () => {
    const res = await adminClient.get('/api/v1/admin/permissions');
    return res.data?.data ?? res.data;
  },
  /** Set permissions for a role (replaces existing). */
  updateRolePermissions: async (roleId: string, permissionIds: string[]) => {
    const res = await adminClient.put(`/api/v1/admin/roles/${roleId}/permissions`, { permission_ids: permissionIds });
    return res.data;
  },
  /** List user management activity (Activity Log tab). */
  activity: async (params?: { page?: number; page_size?: number }) => {
    const res = await adminClient.get('/api/v1/admin/activity', { params });
    const data = res.data?.data ?? res.data;
    return {
      activities: data?.activities ?? [],
      total: data?.total ?? 0,
      page: data?.page ?? 1,
      page_size: data?.page_size ?? 20,
    };
  },
  createUser: async (payload: {
    email: string;
    first_name: string;
    last_name: string;
    password?: string;
    status?: string;
    role_ids?: string[];
  }) => {
    const res = await adminClient.post('/api/v1/admin/users', payload);
    return res.data;
  },
  updateUser: async (
    userId: string,
    payload: {
      email?: string;
      first_name?: string;
      last_name?: string;
      password?: string;
      status?: string;
      role_ids?: string[];
    }
  ) => {
    const res = await adminClient.put(`/api/v1/admin/users/${userId}`, payload);
    return res.data;
  },
  deleteUser: async (userId: string) => {
    const res = await adminClient.delete(`/api/v1/admin/users/${userId}`);
    return res.data;
  },
  listPolicies: async (): Promise<AdminPolicy[]> => {
    const res = await adminClient.get('/api/v1/admin/policies');
    const data = res.data?.data ?? res.data;
    return Array.isArray(data) ? data : [];
  },
  getPolicyStats: async (): Promise<{
    total_expenses: number;
    compliant_count: number;
    violations_count: number;
    compliant_percent: number;
    violations_percent: number;
  }> => {
    const res = await adminClient.get('/api/v1/admin/policy-stats');
    return res.data;
  },
  getPolicyViolations: async (limit?: number): Promise<{
    id: string;
    expense_id: string;
    date: string | null;
    employee: string;
    policy: string;
    violation: string;
    amount: number;
    severity: string;
  }[]> => {
    const res = await adminClient.get('/api/v1/admin/policy-violations', { params: { limit: limit ?? 20 } });
    return Array.isArray(res.data) ? res.data : [];
  },
  createPolicy: async (payload: {
    name: string;
    description?: string;
    policy_type: string;
    policy_rules: Record<string, unknown>;
    applies_to_roles?: string[];
    effective_from?: string;
    effective_until?: string;
  }) => {
    const res = await adminClient.post('/api/v1/admin/policies', {
      ...payload,
      applies_to_roles: payload.applies_to_roles ?? [],
    });
    return res.data;
  },
  updatePolicy: async (
    policyId: string,
    payload: {
      name?: string;
      description?: string;
      policy_type?: string;
      policy_rules?: Record<string, unknown>;
      applies_to_roles?: string[];
      is_active?: boolean;
      effective_from?: string;
      effective_until?: string;
    }
  ) => {
    const res = await adminClient.put(`/api/v1/admin/policies/${policyId}`, payload);
    return res.data;
  },
  deletePolicy: async (policyId: string) => {
    await adminClient.delete(`/api/v1/admin/policies/${policyId}`);
  },
  listCategories: async (): Promise<AdminCategory[]> => {
    const res = await adminClient.get('/api/v1/admin/categories');
    return Array.isArray(res.data) ? res.data : [];
  },
  createCategory: async (payload: {
    name: string;
    code: string;
    description?: string | null;
    gl_account_id?: string | null;
    parent_id?: string | null;
  }) => {
    const res = await adminClient.post('/api/v1/admin/categories', payload);
    return res.data as AdminCategory;
  },
  updateCategory: async (
    categoryId: string,
    payload: {
      name?: string;
      code?: string;
      description?: string | null;
      gl_account_id?: string | null;
      parent_id?: string | null;
      is_active?: boolean;
    }
  ) => {
    const res = await adminClient.put(`/api/v1/admin/categories/${categoryId}`, payload);
    return res.data as AdminCategory;
  },
  deleteCategory: async (categoryId: string) => {
    await adminClient.delete(`/api/v1/admin/categories/${categoryId}`);
  },
  /** Suggest category from merchant, description, amount (rule-based + semantic per PRD). */
  suggestCategory: async (payload: {
    merchant_name?: string | null;
    description?: string | null;
    amount?: number | null;
  }) => {
    const res = await adminClient.post('/api/v1/admin/categories/suggest', payload);
    return res.data as {
      suggested_category: AdminCategory | null;
      confidence: number;
      reasoning: string | null;
      alternatives: AdminCategory[];
    };
  },
  listGLAccounts: async (): Promise<AdminGLAccount[]> => {
    const res = await adminClient.get('/api/v1/admin/gl-accounts');
    return Array.isArray(res.data) ? res.data : [];
  },
  createGLAccount: async (payload: {
    account_code: string;
    account_name: string;
    account_type: string;
    description?: string | null;
    parent_account_id?: string | null;
  }) => {
    const res = await adminClient.post('/api/v1/admin/gl-accounts', payload);
    return res.data as AdminGLAccount;
  },
  listVatRules: async () => {
    const res = await adminClient.get('/api/v1/admin/vat-rules');
    return res.data;
  },

  /** Company settings (Settings page) */
  getSettings: async () => {
    const res = await adminClient.get('/api/v1/admin/settings');
    return res.data?.settings != null ? res.data : { settings: res.data, updated_at: res.data?.updated_at };
  },
  updateSettings: async (payload: {
    general?: Record<string, unknown>;
    users?: Record<string, unknown>;
    security?: Record<string, unknown>;
    notifications?: Record<string, unknown>;
    billing?: Record<string, unknown>;
  }) => {
    const res = await adminClient.put('/api/v1/admin/settings', payload);
    return res.data?.settings != null ? res.data : { settings: res.data, updated_at: res.data?.updated_at };
  },
  getSettingsChangelog: async (params?: { page?: number; page_size?: number }) => {
    const res = await adminClient.get('/api/v1/admin/settings/changelog', { params });
    return Array.isArray(res.data) ? res.data : [];
  },
};
export const ocrAPI = { baseURL: OCR_API_URL };
export const llmAPI = { baseURL: LLM_API_URL };
export const ragAPI = {
  /**
   * RAG Q&A (non-agentic): POST /api/v1/rag/qa
   * query_type must be one of: sql | rag | hybrid
   */
  askQuestion: async (question: string, query_type: 'sql' | 'rag' | 'hybrid' | string = 'hybrid') => {
    const safeType = query_type === 'sql' || query_type === 'rag' || query_type === 'hybrid' ? query_type : 'hybrid';
    const res = await ragClient.post('/api/v1/rag/qa', { question, query_type: safeType });
    return res.data;
  },
  /**
   * Agentic Copilot: POST /api/v1/rag/copilot
   */
  copilotQuery: async (query: string, context?: Record<string, any>) => {
    const res = await ragClient.post('/api/v1/rag/copilot', { query, context: context ?? null });
    return res.data;
  },
  /**
   * Index expense policies into RAG so "RAG Only" can answer policy questions.
   */
  embedPolicies: async () => {
    const res = await ragClient.post('/api/v1/rag/embed/policies');
    return res.data;
  },
  /**
   * Index VAT rules into RAG so "RAG Only" can answer VAT questions.
   */
  embedVatRules: async () => {
    const res = await ragClient.post('/api/v1/rag/embed/vat-rules');
    return res.data;
  },
  /**
   * Index all existing receipt_documents into RAG (backfill). Use when you have receipts but document_embeddings is empty.
   */
  embedReceipts: async () => {
    const res = await ragClient.post('/api/v1/rag/embed/receipts');
    return res.data;
  },
};
export const accountingAPI = {
  listEntries: async (params?: {
    page?: number;
    page_size?: number;
    journal_code?: string;
    status?: string;
    fiscal_year?: number;
    start_date?: string;
    end_date?: string;
  }) => {
    const res = await accountingClient.get('/api/v1/accounting', { params });
    return res.data;
  },
  getEntry: async (id: string) => {
    const res = await accountingClient.get(`/api/v1/accounting/${id}`);
    return res.data;
  },
  generateFromExpense: async (expenseId: string) => {
    const res = await accountingClient.post('/api/v1/accounting/generate', { expense_id: expenseId });
    return res.data;
  },
  validateEntry: async (id: string) => {
    const res = await accountingClient.post(`/api/v1/accounting/${id}/validate`);
    return res.data;
  },
  getJournal: async (journalCode: string, params?: { fiscal_year?: number; page?: number; page_size?: number }) => {
    const res = await accountingClient.get(`/api/v1/accounting/journal/${journalCode}`, { params });
    return res.data;
  },
  getTrialBalance: async (fiscalYear: number, periodStart?: number, periodEnd?: number) => {
    const res = await accountingClient.get('/api/v1/accounting/trial-balance', {
      params: { fiscal_year: fiscalYear, period_start: periodStart, period_end: periodEnd },
    });
    return res.data;
  },
  exportFEC: async (fiscalYear: number, siren: string) => {
    const res = await accountingClient.get('/api/v1/accounting/fec/export', {
      params: { fiscal_year: fiscalYear, siren },
      responseType: 'blob',
    });
    return res.data as Blob;
  },
  autoLetter: async (accountCode: string) => {
    const res = await accountingClient.post(`/api/v1/accounting/letter/${accountCode}`);
    return res.data;
  },
  listPCGAccounts: async () => {
    const res = await accountingClient.get('/api/v1/accounting/pcg-accounts');
    return res.data;
  },
  seedPCGAccounts: async () => {
    const res = await accountingClient.post('/api/v1/accounting/pcg-accounts/seed');
    return res.data;
  },
  listThirdParties: async () => {
    const res = await accountingClient.get('/api/v1/accounting/third-parties');
    return res.data;
  },
  createThirdParty: async (payload: { type: string; name: string; siren?: string; siret?: string; vat_number?: string; default_account_code?: string }) => {
    const res = await accountingClient.post('/api/v1/accounting/third-parties', payload);
    return res.data;
  },
  listPeriods: async (fiscalYear?: number) => {
    const res = await accountingClient.get('/api/v1/accounting/periods', { params: { fiscal_year: fiscalYear } });
    return res.data;
  },
  createPeriod: async (payload: { fiscal_year: number; period_number: number; start_date: string; end_date: string }) => {
    const res = await accountingClient.post('/api/v1/accounting/periods', payload);
    return res.data;
  },
  closePeriod: async (periodId: string) => {
    const res = await accountingClient.post(`/api/v1/accounting/periods/${periodId}/close`);
    return res.data;
  },
};

export const dossierAPI = {
  list: async (params?: { page?: number; page_size?: number; status?: string; search?: string; accountant_id?: string }) => {
    const res = await dossierClient.get('/api/v1/dossiers', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await dossierClient.get(`/api/v1/dossiers/${id}`);
    return res.data;
  },
  create: async (payload: any) => {
    const res = await dossierClient.post('/api/v1/dossiers', payload);
    return res.data;
  },
  update: async (id: string, payload: any) => {
    const res = await dossierClient.put(`/api/v1/dossiers/${id}`, payload);
    return res.data;
  },
  getSummary: async (id: string) => {
    const res = await dossierClient.get(`/api/v1/dossiers/${id}/summary`);
    return res.data;
  },
  getTimeline: async (id: string, params?: { page?: number; page_size?: number }) => {
    const res = await dossierClient.get(`/api/v1/dossiers/${id}/timeline`, { params });
    return res.data;
  },
  listDocuments: async (id: string) => {
    const res = await dossierClient.get(`/api/v1/dossiers/${id}/documents`);
    return res.data;
  },
  addDocument: async (id: string, payload: { document_type: string; title: string; description?: string }) => {
    const res = await dossierClient.post(`/api/v1/dossiers/${id}/documents`, payload);
    return res.data;
  },
};

export const notificationAPI = {
  list: async (params?: { status?: string; page?: number; page_size?: number }) => {
    const res = await notificationClient.get('/api/v1/notifications', { params });
    return res.data;
  },
  markRead: async (id: string) => {
    const res = await notificationClient.post(`/api/v1/notifications/${id}/read`);
    return res.data;
  },
  markAllRead: async () => {
    const res = await notificationClient.post('/api/v1/notifications/read-all');
    return res.data;
  },
  getUnreadCount: async () => {
    const res = await notificationClient.get('/api/v1/notifications/unread-count');
    return res.data;
  },
  listRules: async () => {
    const res = await notificationClient.get('/api/v1/notifications/rules');
    return res.data;
  },
  createRule: async (payload: any) => {
    const res = await notificationClient.post('/api/v1/notifications/rules', payload);
    return res.data;
  },
};

export const bankingAPI = {
  listAccounts: async () => {
    const res = await bankingClient.get('/api/v1/banking/accounts');
    return res.data;
  },
  createAccount: async (payload: any) => {
    const res = await bankingClient.post('/api/v1/banking/accounts', payload);
    return res.data;
  },
  getAccount: async (id: string) => {
    const res = await bankingClient.get(`/api/v1/banking/accounts/${id}`);
    return res.data;
  },
  updateAccount: async (id: string, payload: any) => {
    const res = await bankingClient.put(`/api/v1/banking/accounts/${id}`, payload);
    return res.data;
  },
  listTransactions: async (accountId: string, params?: any) => {
    const res = await bankingClient.get(`/api/v1/banking/accounts/${accountId}/transactions`, { params });
    return res.data;
  },
  createTransaction: async (accountId: string, payload: any) => {
    const res = await bankingClient.post(`/api/v1/banking/accounts/${accountId}/transactions`, payload);
    return res.data;
  },
  uploadStatement: async (accountId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await bankingClient.post(`/api/v1/banking/accounts/${accountId}/upload-statement`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  matchTransaction: async (transactionId: string, entryId: string) => {
    const res = await bankingClient.post(`/api/v1/banking/transactions/${transactionId}/match`, { entry_id: entryId });
    return res.data;
  },
  unmatchTransaction: async (transactionId: string) => {
    const res = await bankingClient.post(`/api/v1/banking/transactions/${transactionId}/unmatch`);
    return res.data;
  },
  reconcile: async (accountId: string) => {
    const res = await bankingClient.post(`/api/v1/banking/accounts/${accountId}/reconcile`);
    return res.data;
  },
  getReconciliationSummary: async (accountId: string) => {
    const res = await bankingClient.get(`/api/v1/banking/accounts/${accountId}/reconciliation-summary`);
    return res.data;
  },
  listStatements: async (accountId: string) => {
    const res = await bankingClient.get(`/api/v1/banking/accounts/${accountId}/statements`);
    return res.data;
  },
  listRules: async () => {
    const res = await bankingClient.get('/api/v1/banking/rules');
    return res.data;
  },
  createRule: async (payload: any) => {
    const res = await bankingClient.post('/api/v1/banking/rules', payload);
    return res.data;
  },
};

export const taxAPI = {
  listDeclarations: async (params?: any) => {
    const res = await taxClient.get('/api/v1/tax/declarations', { params });
    return res.data;
  },
  getDeclaration: async (id: string) => {
    const res = await taxClient.get(`/api/v1/tax/declarations/${id}`);
    return res.data;
  },
  computeDeclaration: async (payload: { type: string; period_start: string; period_end: string; dossier_id?: string }) => {
    const res = await taxClient.post('/api/v1/tax/declarations/compute', payload);
    return res.data;
  },
  validateDeclaration: async (id: string) => {
    const res = await taxClient.post(`/api/v1/tax/declarations/${id}/validate`);
    return res.data;
  },
  getCalendar: async (year?: number) => {
    const res = await taxClient.get('/api/v1/tax/calendar', { params: { year } });
    return res.data;
  },
  getPenalties: async () => {
    const res = await taxClient.get('/api/v1/tax/penalties');
    return res.data;
  },
  getUpcoming: async (days?: number) => {
    const res = await taxClient.get('/api/v1/tax/upcoming', { params: { days } });
    return res.data;
  },
};

export const analysisAPI = {
  getSIG: async (fiscalYear: number) => {
    const res = await analysisClient.get('/api/v1/analysis/sig', { params: { fiscal_year: fiscalYear } });
    return res.data;
  },
  getRatios: async (fiscalYear: number) => {
    const res = await analysisClient.get('/api/v1/analysis/ratios', { params: { fiscal_year: fiscalYear } });
    return res.data;
  },
  getScoring: async (fiscalYear: number) => {
    const res = await analysisClient.get('/api/v1/analysis/scoring', { params: { fiscal_year: fiscalYear } });
    return res.data;
  },
  createSnapshot: async (fiscalYear: number) => {
    const res = await analysisClient.post('/api/v1/analysis/snapshot', null, { params: { fiscal_year: fiscalYear } });
    return res.data;
  },
  createForecast: async (horizonDays: number = 30) => {
    const res = await analysisClient.post('/api/v1/analysis/forecast', null, { params: { horizon_days: horizonDays } });
    return res.data;
  },
  listScenarios: async () => {
    const res = await analysisClient.get('/api/v1/analysis/scenarios');
    return res.data;
  },
  createScenario: async (payload: { name: string; description?: string; parameters: any }) => {
    const res = await analysisClient.post('/api/v1/analysis/scenarios', payload);
    return res.data;
  },
};

export const einvoiceAPI = {
  list: async (params?: any) => {
    const res = await einvoiceClient.get('/api/v1/invoices', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await einvoiceClient.get(`/api/v1/invoices/${id}`);
    return res.data;
  },
  create: async (payload: any) => {
    const res = await einvoiceClient.post('/api/v1/invoices', payload);
    return res.data;
  },
};

export const payrollAPI = {
  allocateCharges: async (payload: any) => {
    const res = await payrollClient.post('/api/v1/payroll/allocate-charges', payload);
    return res.data;
  },
  getAccounts: async () => {
    const res = await payrollClient.get('/api/v1/payroll/accounts');
    return res.data;
  },
};

export const collectionAPI = {
  classify: async (payload: { text_content: string; filename?: string }) => {
    const res = await collectionClient.post('/api/v1/collection/classify', payload);
    return res.data;
  },
  getDocumentTypes: async () => {
    const res = await collectionClient.get('/api/v1/collection/document-types');
    return res.data;
  },
};

export const agentsAPI = {
  listTasks: async () => {
    const res = await agentsClient.get('/api/v1/agents/tasks');
    return res.data;
  },
  toggleTask: async (agentCode: string) => {
    const res = await agentsClient.post(`/api/v1/agents/tasks/${agentCode}/toggle`);
    return res.data;
  },
  getStatus: async () => {
    const res = await agentsClient.get('/api/v1/agents/status');
    return res.data;
  },
};

export const erpAPI = { baseURL: ERP_API_URL };
export const gdprAPI = { baseURL: GDPR_API_URL };
export const performanceAPI = { baseURL: PERFORMANCE_API_URL };
export const securityAPI = { baseURL: SECURITY_API_URL };


