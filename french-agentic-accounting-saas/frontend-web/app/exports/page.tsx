'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { expensesAPI, auditAPI } from '@/lib/api'; // Changed: expenseAPI -> expensesAPI
import { format } from 'date-fns';

interface ExportOption {
  id: string;
  name: string;
  description: string;
  type: 'expenses' | 'reports' | 'receipts';
}

function ExportsPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [exportDateRange, setExportDateRange] = useState({
    start: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, authLoading, router]);

  const exportOptions: ExportOption[] = [
    {
      id: 'expenses',
      name: 'Export Expenses',
      description: 'Export all expenses in CSV or Excel format',
      type: 'expenses'
    },
    {
      id: 'reports',
      name: 'Export Audit Reports',
      description: 'Export audit reports and evidence',
      type: 'reports'
    },
    {
      id: 'receipts',
      name: 'Export Receipts',
      description: 'Download receipt files as ZIP archive',
      type: 'receipts'
    }
  ];

  const handleExport = async (option: ExportOption) => {
    try {
      setLoading(true);
      setError('');

      if (option.type === 'expenses') {
        // Export expenses - Validate date range
        if (!exportDateRange.start || !exportDateRange.end) {
          setError('Please select both start and end dates');
          setLoading(false);
          return;
        }

        // Export expenses - Changed: expenseAPI.listExpenses -> expensesAPI.list
        const response = await expensesAPI.list({
          page: 1,
          page_size: 1000,
          start_date: exportDateRange.start,
          end_date: exportDateRange.end
        });

        // Validate response has data
        if (!response || !response.data || !Array.isArray(response.data) || response.data.length === 0) {
          setError('No expenses found for the selected date range');
          setLoading(false);
          return;
        }

        // Convert to CSV
        const headers = ['ID', 'Date', 'Merchant', 'Amount', 'Currency', 'Category', 'Status'];
        const rows = response.data.map((exp: any) => [
          exp.id || '',
          exp.expense_date || '',
          exp.merchant_name || '',
          exp.amount || 0,
          exp.currency || 'EUR',
          exp.category || '',
          exp.status || ''
        ]);

        const csvContent = [
          headers.join(','),
          ...rows.map((row: any[]) => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `expenses_${exportDateRange.start}_${exportDateRange.end}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else if (option.type === 'reports') {
        // Export audit reports
        const response = await auditAPI.listReports({ page: 1, page_size: 100 });

        // Validate response has data
        if (!response || !response.data || !Array.isArray(response.data) || response.data.length === 0) {
          setError('No audit reports found to export');
          setLoading(false);
          return;
        }

        const headers = ['Report Number', 'Title', 'Period Start', 'Period End', 'Status'];
        const rows = response.data.map((report: any) => [
          report.report_number || '',
          report.title || '',
          report.audit_period_start || '',
          report.audit_period_end || '',
          report.status || ''
        ]);

        const csvContent = [
          headers.join(','),
          ...rows.map((row: any[]) => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_reports_${format(new Date(), 'yyyy-MM-dd')}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        setError('Receipt export functionality coming soon');
      }
    } catch (err: any) {
      // Ensure error is always a string
      let errorMessage = 'Failed to export data';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
        } else {
          errorMessage = JSON.stringify(err.response.data.detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
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
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Data Exports</h1>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Date Range</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={exportDateRange.start}
                onChange={(e) => setExportDateRange({ ...exportDateRange, start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={exportDateRange.end}
                onChange={(e) => setExportDateRange({ ...exportDateRange, end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {exportOptions.map((option) => (
            <div key={option.id} className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{option.name}</h3>
              <p className="text-sm text-gray-600 mb-4">{option.description}</p>
              <button
                onClick={() => handleExport(option)}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Exporting...' : 'Export'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export default ExportsPage;
