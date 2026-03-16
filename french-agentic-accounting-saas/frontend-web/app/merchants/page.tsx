'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { anomalyAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface Merchant {
  merchant_name: string;
  expense_count: number;
  total_amount: number;
  average_amount: number;
  unique_employees: number;
}

interface SpendAnalysis {
  period_days: number;
  summary: {
    total_expenses: number;
    total_amount: number;
    unique_merchants: number;
    unique_employees: number;
    average_per_merchant: number;
    average_per_employee: number;
  };
  top_merchants: Merchant[];
  concentration: {
    top_10_percentage: number;
    is_concentrated: boolean;
  };
}

function MerchantsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [spendAnalysis, setSpendAnalysis] = useState<SpendAnalysis | null>(null);
  const [topMerchants, setTopMerchants] = useState<Merchant[]>([]);
  const [sortBy, setSortBy] = useState<'total_amount' | 'count' | 'avg_amount'>('total_amount');
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      const [analysis, merchants] = await Promise.all([
        anomalyAPI.merchantSpendAnalysis(90),
        anomalyAPI.topMerchants({ limit: 50, sort_by: sortBy, days_back: 90 })
      ]);
      
      setSpendAnalysis(analysis);
      setTopMerchants(merchants);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load merchant data');
    } finally {
      setLoading(false);
    }
  }, [sortBy]);

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
      loadData();
    }
  }, [isAuthenticated, authLoading, router, loadData]);

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
        <h1 className="text-3xl font-bold text-gray-900">Merchant Profiling & Spend Analysis</h1>
        <p className="text-gray-600 mt-2">Analyze merchant spending patterns and behavior</p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Loading merchant data...</div>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          {spendAnalysis && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">Total Merchants</h3>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {spendAnalysis.summary.unique_merchants}
                </p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">Total Spend</h3>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  €{spendAnalysis.summary.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">Avg per Merchant</h3>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  €{spendAnalysis.summary.average_per_merchant.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-sm font-medium text-gray-500">Concentration</h3>
                <p className="text-2xl font-bold text-gray-900 mt-2">
                  {spendAnalysis.concentration.top_10_percentage.toFixed(1)}%
                </p>
                {spendAnalysis.concentration.is_concentrated && (
                  <p className="text-xs text-yellow-600 mt-1">High concentration</p>
                )}
              </div>
            </div>
          )}

          {/* Sort Controls */}
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="total_amount">Total Amount</option>
                <option value="count">Transaction Count</option>
                <option value="avg_amount">Average Amount</option>
              </select>
            </div>
          </div>

          {/* Top Merchants Table */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Top Merchants</h2>
            </div>
            {topMerchants.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No merchant data available</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Merchant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transactions</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Average Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employees</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {topMerchants.map((merchant) => (
                      <tr key={merchant.merchant_name}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {merchant.merchant_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {merchant.expense_count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          €{merchant.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          €{merchant.average_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {merchant.unique_employees}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <Link
                            href={`/merchants/${encodeURIComponent(merchant.merchant_name)}`}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            View Profile
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default MerchantsPage;




