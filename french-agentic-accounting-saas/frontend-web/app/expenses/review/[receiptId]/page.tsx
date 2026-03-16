'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { fileAPI } from '@/lib/api';
import { expensesAPI } from '@/lib/api';

export default function ReviewExpensePage() {
  const router = useRouter();
  const params = useParams();
  const receiptId = params?.receiptId as string;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [extractedData, setExtractedData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    currency: 'EUR',
    expense_date: '',
    merchant_name: '',
    category: '',
    description: '',
    vat_rate: '',
  });

  useEffect(() => {
    if (receiptId) {
      loadReceiptData();
    }
  }, [receiptId]);

  const loadReceiptData = async () => {
    try {
      setLoading(true);
      const receipt = await fileAPI.getReceipt(receiptId);
      setExtractedData(receipt.extracted_data || null);
      
      if (receipt.extracted_data) {
        setFormData({
          amount: receipt.extracted_data.total_amount?.toString() || '',
          currency: receipt.extracted_data.currency || 'EUR',
          expense_date: receipt.extracted_data.expense_date || '',
          merchant_name: receipt.extracted_data.merchant_name || '',
          category: receipt.extracted_data.category || '',
          description: receipt.extracted_data.description || '',
          vat_rate: receipt.extracted_data.vat_rate?.toString() || '',
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load receipt data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      await expensesAPI.create({
        ...formData,
        amount: parseFloat(formData.amount),
        vat_rate: formData.vat_rate ? parseFloat(formData.vat_rate) : undefined,
      });
      router.push('/expenses');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create expense');
    } finally {
      setSaving(false);
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (confidence?: number) => {
    if (!confidence) return 'unknown';
    return `${Math.round(confidence * 100)}%`;
  };

  if (loading) {
    return (
      <>
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading extracted data...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Review Extracted Data</h1>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {extractedData && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-blue-900 mb-3">Extracted Information</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {extractedData.merchant_name && (
                <div>
                  <span className="font-medium">Merchant: </span>
                  <span className={getConfidenceColor(extractedData.confidence_scores?.merchant_name)}>
                    {extractedData.merchant_name}
                  </span>
                </div>
              )}
              {extractedData.expense_date && (
                <div>
                  <span className="font-medium">Date: </span>
                  <span className={getConfidenceColor(extractedData.confidence_scores?.expense_date)}>
                    {extractedData.expense_date}
                  </span>
                </div>
              )}
              {extractedData.total_amount && (
                <div>
                  <span className="font-medium">Total: </span>
                  <span>
                    {Number(extractedData.total_amount).toFixed(2)} {extractedData.currency}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency
              </label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="EUR">EUR</option>
                <option value="USD">USD</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date *
            </label>
            <input
              type="date"
              required
              value={formData.expense_date}
              onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Merchant Name
            </label>
            <input
              type="text"
              value={formData.merchant_name}
              onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <input
                type="text"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                VAT Rate (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.vat_rate}
                onChange={(e) => setFormData({ ...formData, vat_rate: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Creating...' : 'Create Expense'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
