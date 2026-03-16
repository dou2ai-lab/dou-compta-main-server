'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { reportAPI, getAuthErrorMessage } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';

interface ReportExpenseItem {
  id: string;
  amount: string | number;
  currency: string;
  expense_date?: string;
  merchant_name?: string;
  category?: string;
  description?: string;
  vat_amount?: string | number;
  vat_rate?: string | number;
  status?: string;
  approval_status?: string;
}

interface ExpenseReport {
  id: string;
  report_number: string;
  report_type: string;
  title: string;
  description?: string;
  period_start_date?: string;
  period_end_date?: string;
  total_amount: string;
  currency: string;
  expense_count: number;
  status: string;
  approval_status?: string;
  created_at: string;
}

type ToastType = 'error' | 'success';

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated, loading: authLoading, user } = useAuth();

  const [report, setReport] = useState<ExpenseReport | null>(null);
  const [expenses, setExpenses] = useState<ReportExpenseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  // ✏️ Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({ title: '', description: '' });

  // 🔔 Toast state
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

  // ✅ FIX: roles is an array
  const isManager = user?.roles?.includes('manager');

  const showToast = (message: string, type: ToastType = 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (id) loadReport();
  }, [authLoading, isAuthenticated, id]);

  const loadReport = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError('');
      const response = await reportAPI.get(id);
      const data = response.data ?? response;
      setReport(data);
      setEditForm({ title: data.title ?? '', description: data.description ?? '' });
      const expenseList = await reportAPI.getExpenses(id);
      setExpenses(expenseList);
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'Failed to load report'));
    } finally {
      setLoading(false);
    }
  };

  // 🟦 SUBMIT
  const handleSubmitReport = async () => {
    if (!report) return;

    if (report.expense_count === 0) {
      showToast('You must add at least one expense before submitting the report.');
      return;
    }

    try {
      setActionLoading(true);
      // ✅ FIX: submit expects string, not object
      await reportAPI.submit(report.id, '');
      showToast('Report submitted for approval', 'success');
      await loadReport();
    } catch (err: any) {
      showToast(getAuthErrorMessage(err, 'Failed to submit report'));
    } finally {
      setActionLoading(false);
    }
  };

  // ✏️ UPDATE
  const handleUpdateReport = async () => {
    if (!report) return;
    try {
      setActionLoading(true);
      await reportAPI.update(report.id, editForm);
      setIsEditing(false);
      showToast('Report updated successfully', 'success');
      await loadReport();
    } catch (err: any) {
      showToast(getAuthErrorMessage(err, 'Failed to update report'));
    } finally {
      setActionLoading(false);
    }
  };

  // ✅ APPROVE
  const handleApprove = async () => {
    try {
      setActionLoading(true);
      await reportAPI.approve(report!.id, '');
      showToast('Report approved', 'success');
      await loadReport();
    } catch (err: any) {
      showToast(getAuthErrorMessage(err, 'Approval failed'));
    } finally {
      setActionLoading(false);
    }
  };

  // ❌ REJECT
  const handleReject = async () => {
    const reason = prompt('Enter rejection reason');
    if (!reason) return;

    try {
      setActionLoading(true);
      await reportAPI.reject(report!.id, reason);
      showToast('Report rejected');
      await loadReport();
    } catch (err: any) {
      showToast(getAuthErrorMessage(err, 'Rejection failed'));
    } finally {
      setActionLoading(false);
    }
  };

  // 📥 EXPORT (CSV / Excel)
  const handleExport = async (format: 'csv' | 'excel') => {
    if (!report) return;
    try {
      setActionLoading(true);
      const blob = await reportAPI.export(report.id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${report.report_number}.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Report exported as ${format.toUpperCase()}`, 'success');
    } catch (err: any) {
      showToast(getAuthErrorMessage(err, `Export ${format} failed`));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading || authLoading) {
    return (
      <>
        <div className="text-center py-12">Loading report…</div>
      </>
    );
  }

  if (!report) {
    return (
      <>
        <div className="text-center py-12 text-red-600">{error || 'Report not found'}</div>
        <div className="text-center">
          <button onClick={() => router.push('/reports')} className="text-blue-600 hover:underline">Back to Reports</button>
        </div>
      </>
    );
  }

  const displayTitle = report.title || report.report_number;

  return (
    <>
      {/* 🔔 TOAST */}
      {toast && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded shadow text-white
          ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}
        >
          {toast.message}
        </div>
      )}

      <div className="max-w-5xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">{displayTitle}</h1>
        {report.report_number && (
          <p className="text-sm text-gray-500">Report #{report.report_number}</p>
        )}

        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-sm text-gray-500">Total Amount</p>
          <p className="font-medium">
            {Number(report.total_amount).toFixed(2)} {report.currency}
          </p>
          <p className="text-sm text-gray-500 mt-1">{report.expense_count} expense(s)</p>
        </div>

        {expenses.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Expenses in this report</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="py-2 pr-4">Date</th>
                    <th className="py-2 pr-4">Merchant</th>
                    <th className="py-2 pr-4">Category</th>
                    <th className="py-2 pr-4">Description</th>
                    <th className="py-2 pr-4 text-right">Amount</th>
                    <th className="py-2 pr-4 text-right">VAT</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.map((exp) => (
                    <tr key={exp.id} className="border-b border-gray-100 last:border-0">
                      <td className="py-3 pr-4 text-gray-700">
                        {exp.expense_date ? format(new Date(exp.expense_date), 'dd MMM yyyy') : '—'}
                      </td>
                      <td className="py-3 pr-4 text-gray-700">{exp.merchant_name || '—'}</td>
                      <td className="py-3 pr-4 text-gray-700">{exp.category || '—'}</td>
                      <td className="py-3 pr-4 text-gray-600 max-w-xs truncate" title={exp.description}>{exp.description || '—'}</td>
                      <td className="py-3 pr-4 text-right font-medium">
                        {Number(exp.amount).toFixed(2)} {exp.currency}
                      </td>
                      <td className="py-3 pr-4 text-right text-gray-600">
                        {exp.vat_amount != null ? `${Number(exp.vat_amount).toFixed(2)}` : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 flex-wrap">
          <button onClick={() => router.push('/reports')} className="px-4 py-2 border rounded-md">
            Back
          </button>

          <button
            onClick={() => handleExport('csv')}
            disabled={actionLoading || report.expense_count === 0}
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('excel')}
            disabled={actionLoading || report.expense_count === 0}
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Export Excel
          </button>

          {report.status === 'draft' && (
            <>
              <button onClick={() => setIsEditing(!isEditing)} className="px-4 py-2 border rounded-md">
                {isEditing ? 'Cancel Edit' : 'Edit'}
              </button>

              {isEditing && (
                <button
                  onClick={handleUpdateReport}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md"
                >
                  Save Changes
                </button>
              )}

              {!isEditing && (
                <button
                  onClick={handleSubmitReport}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md"
                >
                  Submit for Approval
                </button>
              )}
            </>
          )}

          {report.status === 'submitted' && isManager && (
            <>
              <button onClick={handleApprove} className="px-4 py-2 bg-green-600 text-white rounded-md">
                Approve
              </button>
              <button onClick={handleReject} className="px-4 py-2 bg-red-600 text-white rounded-md">
                Reject
              </button>
            </>
          )}
        </div>
      </div>
    </>
  );
}
