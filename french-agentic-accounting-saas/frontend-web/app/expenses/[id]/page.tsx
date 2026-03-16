'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { expensesAPI, policyAPI, anomalyAPI, getAuthErrorMessage } from '@/lib/api';
import PolicyViolations from '@/components/PolicyViolations';
import AnomalyExplanations from '@/components/AnomalyExplanations';
import { format } from 'date-fns';
import Link from 'next/link';

interface Expense {
  id: string;
  amount: number;
  currency: string;
  expense_date: string;
  category?: string;
  description?: string;
  merchant_name?: string;
  status: string;
  approval_status?: string;
  approved_by?: string;
  approved_at?: string;
  rejection_reason?: string;
  vat_amount?: number;
  vat_rate?: number;
  created_at: string;
  updated_at: string;
}

export default function ExpenseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const expenseId = params?.id as string;

  const [expense, setExpense] = useState<Expense | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedExpense, setEditedExpense] = useState<Partial<Expense>>({});
  const [violations, setViolations] = useState<any[]>([]);
  const [loadingViolations, setLoadingViolations] = useState(false);
  const [anomalyAnalysis, setAnomalyAnalysis] = useState<any>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    if (expenseId) {
      loadExpense();
    }
  }, [expenseId]);

  const loadExpense = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await expensesAPI.get(expenseId);
      const expenseData = response.data || response;
      setExpense(expenseData);
      setEditedExpense(expenseData);
      
      // Load policy violations
      await loadViolations();
      // Load anomaly analysis
      await loadAnomalyAnalysis();
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'Failed to load expense'));
    } finally {
      setLoading(false);
    }
  };

  const loadViolations = async () => {
    try {
      setLoadingViolations(true);
      const response = await policyAPI.evaluate(expenseId);
      if (response.violations) {
        setViolations(response.violations);
      }
    } catch (err: any) {
      console.error('Failed to load policy violations:', err);
      // Don't show error - violations are optional
    } finally {
      setLoadingViolations(false);
    }
  };

  const loadAnomalyAnalysis = async () => {
    try {
      setLoadingAnalysis(true);
      const analysis = await anomalyAPI.analyze(expenseId);
      setAnomalyAnalysis(analysis);
    } catch (err: any) {
      console.error('Failed to load anomaly analysis:', err);
      // Don't show error - analysis is optional
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      await expensesAPI.submit(expenseId);
      await loadExpense();
      alert('Expense submitted for approval!');
    } catch (err: any) {
      alert(getAuthErrorMessage(err, 'Failed to submit expense'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSaveEdit = async () => {
    try {
      setIsSubmitting(true);
      await expensesAPI.update(expenseId, {
        amount: editedExpense.amount,
        currency: editedExpense.currency,
        expense_date: editedExpense.expense_date,
        category: editedExpense.category,
        description: editedExpense.description,
        merchant_name: editedExpense.merchant_name,
        vat_amount: editedExpense.vat_amount,
        vat_rate: editedExpense.vat_rate,
      });
      setIsEditing(false);
      await loadExpense();
      alert('Expense updated successfully!');
    } catch (err: any) {
      alert(getAuthErrorMessage(err, 'Failed to update expense'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this expense?')) {
      return;
    }
    
    try {
      setIsSubmitting(true);
      await expensesAPI.delete(expenseId);
      router.push('/expenses');
    } catch (err: any) {
      alert(getAuthErrorMessage(err, 'Failed to delete expense'));
      setIsSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'submitted':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading expense...</p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
          <Link href="/expenses" className="text-blue-600 hover:text-blue-800">
            ← Back to Expenses
          </Link>
        </div>
      </>
    );
  }

  if (!expense) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12 text-gray-500">
            Expense not found
          </div>
          <Link href="/expenses" className="text-blue-600 hover:text-blue-800">
            ← Back to Expenses
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <Link href="/expenses" className="text-blue-600 hover:text-blue-800 mb-2 inline-block">
              ← Back to Expenses
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Expense Details</h1>
          </div>
          <div className="flex gap-3">
            {expense.status === 'draft' && !isEditing && (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Edit
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit for Approval'}
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  Delete
                </button>
              </>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleSaveEdit}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditedExpense(expense);
                  }}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div className="mb-6">
          <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(expense.status)}`}>
            {expense.status}
          </span>
          {expense.approval_status && (
            <span className="ml-2 text-sm text-gray-600">
              Approval: {expense.approval_status}
            </span>
          )}
        </div>

        {/* Policy Violations */}
        {violations.length > 0 && (
          <div className="mb-6">
            <PolicyViolations
              violations={violations}
              showResolveButton={false}
            />
          </div>
        )}

        {/* Anomaly Analysis */}
        {loadingAnalysis ? (
          <div className="mb-6 text-center py-4">Loading anomaly analysis...</div>
        ) : anomalyAnalysis && (
          <div className="mb-6">
            <AnomalyExplanations
              explanations={anomalyAnalysis.explanations}
              riskScore={anomalyAnalysis.risk_score}
              riskLevel={anomalyAnalysis.risk_level}
              isAnomaly={anomalyAnalysis.is_anomaly}
            />
          </div>
        )}

        <div className="bg-white shadow rounded-lg p-6 space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount
              </label>
              {isEditing ? (
                <input
                  type="number"
                  step="0.01"
                  value={editedExpense.amount || ''}
                  onChange={(e) => setEditedExpense({...editedExpense, amount: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="text-lg font-semibold text-gray-900">
                  {expense.amount} {expense.currency}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date
              </label>
              {isEditing ? (
                <input
                  type="date"
                  value={editedExpense.expense_date || ''}
                  onChange={(e) => setEditedExpense({...editedExpense, expense_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="text-lg text-gray-900">
                  {format(new Date(expense.expense_date), 'MMMM dd, yyyy')}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Merchant
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editedExpense.merchant_name || ''}
                onChange={(e) => setEditedExpense({...editedExpense, merchant_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <p className="text-gray-900">{expense.merchant_name || '-'}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editedExpense.category || ''}
                onChange={(e) => setEditedExpense({...editedExpense, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <p className="text-gray-900">{expense.category || '-'}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            {isEditing ? (
              <textarea
                value={editedExpense.description || ''}
                onChange={(e) => setEditedExpense({...editedExpense, description: e.target.value})}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            ) : (
              <p className="text-gray-900">{expense.description || '-'}</p>
            )}
          </div>

          {/* VAT Information */}
          <div className="border-t pt-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">VAT Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  VAT Amount
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editedExpense.vat_amount || ''}
                    onChange={(e) => setEditedExpense({...editedExpense, vat_amount: parseFloat(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {expense.vat_amount ? `${expense.vat_amount} ${expense.currency}` : '-'}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  VAT Rate
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.1"
                    value={editedExpense.vat_rate || ''}
                    onChange={(e) => setEditedExpense({...editedExpense, vat_rate: parseFloat(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {expense.vat_rate ? `${expense.vat_rate}%` : '-'}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Approval Information */}
          {(expense.approval_status === 'approved' || expense.approval_status === 'rejected') && (
            <div className="border-t pt-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Approval Information</h3>
              {expense.approved_at && (
                <div className="mb-2">
                  <label className="block text-sm font-medium text-gray-700">Approved At</label>
                  <p className="text-gray-900">{format(new Date(expense.approved_at), 'MMMM dd, yyyy HH:mm')}</p>
                </div>
              )}
              {expense.rejection_reason && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Rejection Reason</label>
                  <p className="text-gray-900">{expense.rejection_reason}</p>
                </div>
              )}
            </div>
          )}

          {/* Metadata */}
          <div className="border-t pt-4 text-sm text-gray-500">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-medium">Created:</span> {format(new Date(expense.created_at), 'MMM dd, yyyy HH:mm')}
              </div>
              <div>
                <span className="font-medium">Updated:</span> {format(new Date(expense.updated_at), 'MMM dd, yyyy HH:mm')}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

