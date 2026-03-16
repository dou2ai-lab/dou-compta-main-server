'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { auditAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import Link from 'next/link';

interface AuditReport {
  id: string;
  report_number: string;
  title: string;
  description?: string;
  audit_period_start: string;
  audit_period_end: string;
  period_type: string;
  report_type: string;
  status: string;
  sample_size: number;
  total_expenses_in_scope: number;
  total_amount_in_scope: number;
  created_at: string;
  completed_at?: string;
}

interface PendingExpenseReport {
  id: string;
  report_number: string;
  title: string | null;
  period_start_date: string | null;
  period_end_date: string | null;
  total_amount: number;
  currency: string;
  expense_count: number;
  status: string;
  approval_status: string | null;
  submitted_at: string | null;
  created_at: string;
}

function AuditReportsPage() {
  const [reports, setReports] = useState<AuditReport[]>([]);
  const [pendingExpenseReports, setPendingExpenseReports] = useState<PendingExpenseReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingPending, setLoadingPending] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params: any = {};
      if (statusFilter) {
        params.status = statusFilter;
      }
      const data = await auditAPI.listReports(params);
      setReports(Array.isArray(data) ? data : (data.data || []));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit reports');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  const loadPendingExpenseReports = useCallback(async () => {
    try {
      setLoadingPending(true);
      const list = await auditAPI.pendingExpenseReports({ status: 'submitted', limit: 50 });
      setPendingExpenseReports(Array.isArray(list) ? list : []);
    } catch {
      setPendingExpenseReports([]);
    } finally {
      setLoadingPending(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) {
      return;
    }
    
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    if (!isAuthenticated && !token) {
      router.push('/login');
      return;
    }
    
    if (isAuthenticated || token) {
      loadReports();
      loadPendingExpenseReports();
    }
  }, [isAuthenticated, authLoading, router, loadReports, loadPendingExpenseReports]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'published':
        return 'bg-purple-100 text-purple-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (authLoading) {
    return (
      <>
        <div className="text-center py-12">Loading...</div>
      </>
    );
  }

  return (
    <>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Reports</h1>
          <p className="text-gray-600 mt-2">Create and manage audit reports</p>
        </div>
        <Link
          href="/audit/reports/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + New Report
        </Link>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Expense reports submitted for approval – for auditor to review */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-3">Expense reports pending audit</h2>
        <p className="text-sm text-gray-600 mb-4">
          Expense reports submitted for approval appear here. Open a report to review and approve or reject.
        </p>
        {loadingPending ? (
          <div className="text-center py-6 text-gray-500">Loading pending expense reports...</div>
        ) : pendingExpenseReports.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
            No expense reports submitted for approval.
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report #</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expenses</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {pendingExpenseReports.map((r) => (
                  <tr key={r.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{r.report_number}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{r.title ?? '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {r.period_start_date && r.period_end_date
                        ? `${format(new Date(r.period_start_date), 'MMM d, yyyy')} – ${format(new Date(r.period_end_date), 'MMM d, yyyy')}`
                        : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{r.expense_count}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {r.currency} {r.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {r.submitted_at ? format(new Date(r.submitted_at), 'MMM d, yyyy HH:mm') : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link href={`/reports/${r.id}`} className="text-blue-600 hover:text-blue-900">
                        Review & approve
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="mb-4 bg-white shadow rounded-lg p-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="published">Published</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading audit reports...</div>
      ) : reports.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No audit reports found. Create your first report to get started.
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Report Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sample Size</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {report.report_number}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {report.title}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(report.audit_period_start), 'MMM dd, yyyy')} - {format(new Date(report.audit_period_end), 'MMM dd, yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(report.status)}`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {report.sample_size}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    €{report.total_amount_in_scope.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <Link
                      href={`/audit/reports/${report.id}`}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export default AuditReportsPage;




