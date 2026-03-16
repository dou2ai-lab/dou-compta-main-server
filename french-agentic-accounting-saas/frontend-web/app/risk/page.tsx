'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { anomalyAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import Link from 'next/link';

interface HighRiskEmployee {
  user_id: string;
  email: string;
  name: string;
  avg_risk_score: number;
  expense_count: number;
  high_risk_count: number;
  anomaly_count: number;
  total_amount: number;
}

interface HighRiskMerchant {
  merchant_name: string;
  avg_risk_score: number;
  expense_count: number;
  high_risk_count: number;
  anomaly_count: number;
  total_amount: number;
  unique_employees: number;
}

interface SuspiciousTransaction {
  expense_id: string;
  amount: number;
  currency: string;
  merchant_name?: string;
  category?: string;
  expense_date: string;
  user_id: string;
  user_email: string;
  user_name: string;
  risk_score: number;
  risk_level: string;
  is_anomaly: boolean;
  anomaly_score: number;
}

interface RepeatedViolation {
  user_id: string;
  email: string;
  name: string;
  violation_count: number;
  last_violation?: string;
}

interface DashboardSummary {
  total_high_risk_employees: number;
  total_high_risk_merchants: number;
  total_suspicious_transactions: number;
  total_repeated_violations: number;
  total_high_risk_amount: number;
}

function RiskDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [highRiskEmployees, setHighRiskEmployees] = useState<HighRiskEmployee[]>([]);
  const [highRiskMerchants, setHighRiskMerchants] = useState<HighRiskMerchant[]>([]);
  const [suspiciousTransactions, setSuspiciousTransactions] = useState<SuspiciousTransaction[]>([]);
  const [repeatedViolations, setRepeatedViolations] = useState<RepeatedViolation[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [training, setTraining] = useState(false);
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await anomalyAPI.dashboard({
        limitEmployees: 10,
        limitMerchants: 10,
        limitTransactions: 50,
        minRiskScore: 0.7
      });
      
      setHighRiskEmployees(response.high_risk_employees || []);
      setHighRiskMerchants(response.high_risk_merchants || []);
      setSuspiciousTransactions(response.suspicious_transactions || []);
      setRepeatedViolations(response.repeated_violations || []);
      setSummary(response.summary || null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load risk dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleTrainModel = async () => {
    try {
      setTraining(true);
      const response = await anomalyAPI.train();
      if (response?.success) {
        alert('Model training initiated successfully!');
        await loadDashboard();
      } else {
        alert(response?.message || 'Model training failed. Please check if you have sufficient data.');
      }
    } catch (err: any) {
      let errorMessage = 'Failed to train model';
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
      alert(errorMessage);
    } finally {
      setTraining(false);
    }
  };

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
      loadDashboard();
    }
  }, [isAuthenticated, authLoading, router, loadDashboard]);

  const getRiskColor = (score: number) => {
    if (score >= 0.7) return 'bg-red-100 text-red-800';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getRiskLevel = (score: number) => {
    if (score >= 0.7) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
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
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Risk Dashboard</h1>
          <p className="text-gray-600 mt-2">Anomaly detection and risk analysis for expenses</p>
        </div>
        <button
          onClick={handleTrainModel}
          disabled={training}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {training ? 'Training...' : 'Train Model'}
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">High-Risk Employees</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {summary.total_high_risk_employees}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">High-Risk Merchants</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {summary.total_high_risk_merchants}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">Suspicious Transactions</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {summary.total_suspicious_transactions}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">Repeated Violations</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {summary.total_repeated_violations}
            </p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-500">High-Risk Amount</h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              €{summary.total_high_risk_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">Loading risk dashboard...</div>
      ) : (
        <div className="space-y-6">
          {/* High-Risk Employees */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">High-Risk Employees</h2>
            </div>
            {highRiskEmployees.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No high-risk employees found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expenses</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">High-Risk</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Anomalies</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {highRiskEmployees.map((emp) => (
                      <tr key={emp.user_id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{emp.name}</div>
                            <div className="text-sm text-gray-500">{emp.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(emp.avg_risk_score)}`}>
                            {(emp.avg_risk_score * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{emp.expense_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{emp.high_risk_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{emp.anomaly_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          €{emp.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* High-Risk Merchants */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">High-Risk Merchants</h2>
            </div>
            {highRiskMerchants.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No high-risk merchants found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Merchant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transactions</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">High-Risk</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employees</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Amount</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {highRiskMerchants.map((merch) => (
                      <tr key={merch.merchant_name}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {merch.merchant_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(merch.avg_risk_score)}`}>
                            {(merch.avg_risk_score * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{merch.expense_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{merch.high_risk_count}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{merch.unique_employees}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          €{merch.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Suspicious Transactions */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Suspicious Transactions</h2>
            </div>
            {suspiciousTransactions.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No suspicious transactions found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Merchant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Anomaly</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {suspiciousTransactions.map((tx) => (
                      <tr key={tx.expense_id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {format(new Date(tx.expense_date), 'MMM dd, yyyy')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{tx.user_name}</div>
                            <div className="text-sm text-gray-500">{tx.user_email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {tx.merchant_name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {tx.currency} {tx.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(tx.risk_score)}`}>
                            {getRiskLevel(tx.risk_score)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {tx.is_anomaly ? (
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              Yes ({(tx.anomaly_score * 100).toFixed(1)}%)
                            </span>
                          ) : (
                            <span className="text-sm text-gray-500">No</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <Link
                            href={`/expenses/${tx.expense_id}`}
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
          </div>

          {/* Repeated Violations */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Repeated Violations</h2>
            </div>
            {repeatedViolations.length === 0 ? (
              <div className="p-6 text-center text-gray-500">No repeated violations found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Violations</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Violation</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {repeatedViolations.map((viol) => (
                      <tr key={viol.user_id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{viol.name}</div>
                            <div className="text-sm text-gray-500">{viol.email}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                            {viol.violation_count}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {viol.last_violation ? format(new Date(viol.last_violation), 'MMM dd, yyyy') : '-'}
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

export default RiskDashboardPage;




