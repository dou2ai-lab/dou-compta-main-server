'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { anomalyAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import Link from 'next/link';

interface MerchantProfile {
  merchant_name: string;
  exists: boolean;
  statistics: {
    total_expenses: number;
    total_amount: number;
    average_amount: number;
    min_amount: number;
    max_amount: number;
    median_amount: number;
    unique_employees: number;
    unique_categories: number;
    date_range: {
      first_expense: string;
      last_expense: string;
    };
  };
  patterns: {
    weekday_distribution: Record<number, number>;
    month_distribution: Record<number, number>;
    category_distribution: Record<string, number>;
    most_common_category: string | null;
  };
  approval_metrics: {
    approved: number;
    rejected: number;
    pending: number;
    approval_rate: number;
    rejection_rate: number;
  };
  employees: Array<{
    id: string;
    email: string;
    name: string;
  }>;
  risk_indicators: {
    high_amount_variance: boolean;
    single_employee_usage: boolean;
    high_rejection_rate: boolean;
  };
}

function MerchantProfilePage() {
  const router = useRouter();
  const params = useParams();
  const merchantName = decodeURIComponent(params?.name as string);
  
  const [profile, setProfile] = useState<MerchantProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { isAuthenticated, loading: authLoading } = useAuth();

  useEffect(() => {
    if (merchantName && (isAuthenticated || !authLoading)) {
      loadProfile();
    }
  }, [merchantName, isAuthenticated, authLoading]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await anomalyAPI.merchantProfile(merchantName, 90);
      setProfile(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load merchant profile');
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

  if (!profile) {
    return (
      <>
        <div className="mb-6">
          <Link href="/merchants" className="text-blue-600 hover:text-blue-900">
            ← Back to Merchants
          </Link>
        </div>
        {loading ? (
          <div className="text-center py-12">Loading merchant profile...</div>
        ) : (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error || 'Merchant not found'}
          </div>
        )}
      </>
    );
  }

  const weekdayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  return (
    <>
      <div className="mb-6">
        <Link href="/merchants" className="text-blue-600 hover:text-blue-900 mb-4 inline-block">
          ← Back to Merchants
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{profile.merchant_name}</h1>
        <p className="text-gray-600 mt-2">Merchant Profile & Analysis</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Expenses</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{profile.statistics.total_expenses}</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Amount</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            €{profile.statistics.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-500">Average Amount</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">
            €{profile.statistics.average_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-500">Unique Employees</h3>
          <p className="text-2xl font-bold text-gray-900 mt-2">{profile.statistics.unique_employees}</p>
        </div>
      </div>

      {/* Risk Indicators */}
      {(profile.risk_indicators.high_amount_variance ||
        profile.risk_indicators.single_employee_usage ||
        profile.risk_indicators.high_rejection_rate) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-yellow-800 mb-2">Risk Indicators</h3>
          <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
            {profile.risk_indicators.high_amount_variance && (
              <li>High variance in expense amounts</li>
            )}
            {profile.risk_indicators.single_employee_usage && (
              <li>Only used by a single employee</li>
            )}
            {profile.risk_indicators.high_rejection_rate && (
              <li>High rejection rate ({profile.approval_metrics.rejection_rate.toFixed(1)}%)</li>
            )}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Approval Metrics */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Approval Metrics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Approved:</span>
              <span className="text-sm font-medium text-green-600">{profile.approval_metrics.approved}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Rejected:</span>
              <span className="text-sm font-medium text-red-600">{profile.approval_metrics.rejected}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Pending:</span>
              <span className="text-sm font-medium text-yellow-600">{profile.approval_metrics.pending}</span>
            </div>
            <div className="pt-3 border-t border-gray-200">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-900">Approval Rate:</span>
                <span className="text-sm font-bold text-gray-900">
                  {profile.approval_metrics.approval_rate.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Patterns */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending Patterns</h3>
          <div className="space-y-3">
            {profile.patterns.most_common_category && (
              <div>
                <span className="text-sm text-gray-600">Most Common Category:</span>
                <span className="ml-2 text-sm font-medium text-gray-900">
                  {profile.patterns.most_common_category}
                </span>
              </div>
            )}
            <div>
              <span className="text-sm text-gray-600">Unique Categories:</span>
              <span className="ml-2 text-sm font-medium text-gray-900">
                {profile.statistics.unique_categories}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600">Date Range:</span>
              <div className="mt-1 text-xs text-gray-500">
                {profile.statistics.date_range.first_expense && (
                  <div>First: {format(new Date(profile.statistics.date_range.first_expense), 'MMM dd, yyyy')}</div>
                )}
                {profile.statistics.date_range.last_expense && (
                  <div>Last: {format(new Date(profile.statistics.date_range.last_expense), 'MMM dd, yyyy')}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Employees */}
      {profile.employees.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Employees Using This Merchant</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {profile.employees.map((emp) => (
              <div key={emp.id} className="border border-gray-200 rounded p-3">
                <div className="text-sm font-medium text-gray-900">{emp.name}</div>
                <div className="text-xs text-gray-500">{emp.email}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

export default MerchantProfilePage;




