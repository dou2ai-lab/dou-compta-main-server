'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { auditAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import Link from 'next/link';

interface BasicReport {
  report_period: {
    start: string;
    end: string;
  };
  generated_at: string;
  total_expenses: number;
  spend_summary: {
    total_amount: number;
    total_count: number;
    by_category: Record<string, { count: number; total: number }>;
    by_merchant: Record<string, { count: number; total: number }>;
    by_employee: Record<string, { count: number; total: number; email: string; name: string }>;
    by_status: Record<string, { count: number; total: number }>;
    average_amount: number;
  };
  policy_violations: {
    total_violations: number;
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
    by_employee: Record<string, { count: number; email: string; name: string }>;
  };
  vat_summary: {
    total_vat_amount: number;
    total_vatable_amount: number;
    by_rate: Record<string, { count: number; total_amount: number; total_vat: number }>;
    vat_compliance: {
      expenses_with_vat: number;
      expenses_without_vat: number;
      missing_vat_count: number;
      compliance_rate: number;
    };
  };
}

function GenerateReportPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [report, setReport] = useState<BasicReport | null>(null);
  const [formData, setFormData] = useState({
    period_start: '',
    period_end: '',
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setGenerating(true);
    setReport(null);

    try {
      const data = await auditAPI.generateBasicReport(
        formData.period_start,
        formData.period_end
      );
      setReport(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  if (authLoading) {
    return (
      <>
        <div className="text-center py-12">Loading...</div>
      </>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <div className="text-center py-12">Redirecting...</div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">Generate Basic Audit Report</h1>
          <Link
            href="/audit/reports"
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back to Reports
          </Link>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleGenerate} className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Period Start *
              </label>
              <input
                type="date"
                required
                value={formData.period_start}
                onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Period End *
              </label>
              <input
                type="date"
                required
                value={formData.period_end}
                onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={generating}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </form>

        {report && (
          <div className="space-y-6">
            {/* Spend Summary */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Spend Summary</h2>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Total Amount</p>
                  <p className="text-2xl font-bold text-gray-900">
                    €{report.spend_summary.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Expenses</p>
                  <p className="text-2xl font-bold text-gray-900">{report.spend_summary.total_count}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Average Amount</p>
                  <p className="text-2xl font-bold text-gray-900">
                    €{report.spend_summary.average_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {/* Top Categories */}
              <div className="mt-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Top Categories</h3>
                <div className="space-y-2">
                  {Object.entries(report.spend_summary.by_category)
                    .sort((a, b) => b[1].total - a[1].total)
                    .slice(0, 10)
                    .map(([category, data]) => (
                      <div key={category} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="font-medium">{category}</span>
                        <span>€{data.total.toFixed(2)} ({data.count} expenses)</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* Policy Violations */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Policy Violations</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Total Violations</p>
                  <p className="text-2xl font-bold text-red-600">{report.policy_violations.total_violations}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">By Severity</p>
                  <div className="mt-2 space-y-1">
                    {Object.entries(report.policy_violations.by_severity).map(([severity, count]) => (
                      <div key={severity} className="flex justify-between">
                        <span className="capitalize">{severity}:</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* VAT Summary */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">VAT Summary</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Total VAT Amount</p>
                  <p className="text-2xl font-bold text-gray-900">
                    €{(report.vat_summary?.total_vat_amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Compliance Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {report.vat_summary?.vat_compliance?.compliance_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">VAT by Rate</h3>
                <div className="space-y-2">
                  {Object.entries(report.vat_summary?.by_rate || {}).map(([rate, data]: [string, any]) => (
                    <div key={rate} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="font-medium">{rate}</span>
                      <span>€{(data?.total_vat || 0).toFixed(2)} ({data?.count || 0} expenses)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default GenerateReportPage;




