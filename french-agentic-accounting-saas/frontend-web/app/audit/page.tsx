'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { auditAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';

interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user_id: string;
  user_email?: string;
  details?: any;
  ip_address?: string;
  created_at: string;
}

function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboard, setDashboard] = useState<any>(null);
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const loadAuditLogs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await auditAPI.logs();
      const logsList = Array.isArray(response) ? response : (response.data || []);
      setLogs(logsList);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const response = await auditAPI.dashboard();
      setDashboard(response.data || response);
    } catch (err: any) {
      console.error('Failed to load audit dashboard:', err);
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
      loadAuditLogs();
      loadDashboard();
    }
  }, [isAuthenticated, authLoading, router, loadAuditLogs, loadDashboard]);

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'create':
        return 'bg-green-100 text-green-800';
      case 'update':
        return 'bg-blue-100 text-blue-800';
      case 'delete':
        return 'bg-red-100 text-red-800';
      case 'approve':
        return 'bg-purple-100 text-purple-800';
      case 'reject':
        return 'bg-orange-100 text-orange-800';
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="text-gray-600 mt-2">View all system activity and audit trails</p>
      </div>

      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Actions</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {dashboard.total_actions || 0}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">Today's Actions</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {dashboard.today_actions || 0}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">Unique Users</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {dashboard.unique_users || 0}
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Loading audit logs...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No audit logs found.
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Array.isArray(logs) && logs.length > 0 ? logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(log.created_at), 'MMM dd, yyyy HH:mm:ss')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getActionColor(
                        log.action
                      )}`}
                    >
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {log.resource_type} ({log.resource_id?.slice(0, 8) || 'N/A'}...)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.user_email || log.user_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.ip_address || '-'}
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    No audit logs found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export default AuditPage;
