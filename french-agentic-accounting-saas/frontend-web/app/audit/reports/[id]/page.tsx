'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
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
  template_version: string;
  sample_size: number;
  total_expenses_in_scope: number;
  total_amount_in_scope: number;
  technical_data?: any;
  narrative_sections?: any;
  metadata?: any;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  published_at?: string;
}

function AuditReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reportId = params?.id as string;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (!reportId || authLoading) {
      return;
    }

    const loadReport = async () => {
      try {
        setLoading(true);
        setError('');
        const data = await auditAPI.getReport(reportId);
        setReport(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load audit report');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      loadReport();
    }
  }, [reportId, isAuthenticated, authLoading]);

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

  if (authLoading || loading) {
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

  if (error) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
          <Link
            href="/audit/reports"
            className="text-blue-600 hover:text-blue-900"
          >
            ← Back to Reports
          </Link>
        </div>
      </>
    );
  }

  if (!report) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12 text-gray-500">
            Report not found
          </div>
          <Link
            href="/audit/reports"
            className="text-blue-600 hover:text-blue-900"
          >
            ← Back to Reports
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-6xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <Link
              href="/audit/reports"
              className="text-gray-600 hover:text-gray-900 mb-2 inline-block"
            >
              ← Back to Reports
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">{report.title}</h1>
            <p className="text-gray-600 mt-2">{report.report_number}</p>
          </div>
          <div className="flex gap-3">
            <Link
              href={`/audit/reports/${report.id}/narrative`}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Narrative
            </Link>
          </div>
        </div>

        {/* Status Badge */}
        <div className="mb-6">
          <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getStatusColor(report.status)}`}>
            {report.status}
          </span>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {report.description && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Description</h2>
                <p className="text-gray-700">{report.description}</p>
              </div>
            )}

            {/* Period Information */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Audit Period</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Start Date</label>
                  <p className="text-gray-900">
                    {format(new Date(report.audit_period_start), 'MMMM dd, yyyy')}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">End Date</label>
                  <p className="text-gray-900">
                    {format(new Date(report.audit_period_end), 'MMMM dd, yyyy')}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Period Type</label>
                  <p className="text-gray-900 capitalize">{report.period_type}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Report Type</label>
                  <p className="text-gray-900 capitalize">{report.report_type}</p>
                </div>
              </div>
            </div>

            {/* Technical Data */}
            {report.technical_data && Object.keys(report.technical_data).length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Technical Data</h2>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                  {JSON.stringify(report.technical_data, null, 2)}
                </pre>
              </div>
            )}

            {/* Narrative Sections */}
            {report.narrative_sections && Object.keys(report.narrative_sections).length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Narrative Sections</h2>
                <div className="space-y-4">
                  {Object.entries(report.narrative_sections).map(([key, value]: [string, any]) => (
                    <div key={key} className="border-b border-gray-200 pb-4 last:border-b-0">
                      <h3 className="font-medium text-gray-900 mb-2 capitalize">{key.replace(/_/g, ' ')}</h3>
                      <p className="text-gray-700 text-sm">{typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Statistics */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Sample Size</label>
                  <p className="text-2xl font-bold text-gray-900">{report.sample_size}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Total Expenses</label>
                  <p className="text-2xl font-bold text-gray-900">{report.total_expenses_in_scope}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Total Amount</label>
                  <p className="text-2xl font-bold text-gray-900">
                    €{report.total_amount_in_scope.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Metadata</h2>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="font-medium text-gray-500">Template Version</label>
                  <p className="text-gray-900">{report.template_version}</p>
                </div>
                <div>
                  <label className="font-medium text-gray-500">Created At</label>
                  <p className="text-gray-900">
                    {format(new Date(report.created_at), 'MMM dd, yyyy HH:mm')}
                  </p>
                </div>
                {report.updated_at && (
                  <div>
                    <label className="font-medium text-gray-500">Updated At</label>
                    <p className="text-gray-900">
                      {format(new Date(report.updated_at), 'MMM dd, yyyy HH:mm')}
                    </p>
                  </div>
                )}
                {report.completed_at && (
                  <div>
                    <label className="font-medium text-gray-500">Completed At</label>
                    <p className="text-gray-900">
                      {format(new Date(report.completed_at), 'MMM dd, yyyy HH:mm')}
                    </p>
                  </div>
                )}
                {report.published_at && (
                  <div>
                    <label className="font-medium text-gray-500">Published At</label>
                    <p className="text-gray-900">
                      {format(new Date(report.published_at), 'MMM dd, yyyy HH:mm')}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Additional Metadata */}
            {report.metadata && Object.keys(report.metadata).length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Additional Metadata</h2>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs">
                  {JSON.stringify(report.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default AuditReportDetailPage;





