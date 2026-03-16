'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ragAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface QAResponse {
  success: boolean;
  answer: string;
  explanation?: string;
  query_type: string;
  sql_query?: string;
  sql_results?: any[];
  retrieved_documents?: any[];
  citations?: any[];
  reasoning_steps?: any[];
  confidence_score: string;
  session_id: string;
  error?: string;
}

function QAPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [question, setQuestion] = useState('');
  const [queryType, setQueryType] = useState('agentic');
  const [useCopilot, setUseCopilot] = useState(true);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QAResponse | null>(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QAResponse[]>([]);
  const [indexing, setIndexing] = useState<{ policies: boolean; vatRules: boolean; receipts: boolean }>({ policies: false, vatRules: false, receipts: false });
  const [indexMessage, setIndexMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError('');
    setResponse(null);

    try {
      let data;
      if (useCopilot && queryType === 'agentic') {
        data = await ragAPI.copilotQuery(question);
      } else {
        data = await ragAPI.askQuestion(question, queryType);
      }
      setResponse(data);
      if (data.success) {
        setHistory(prev => [data, ...prev].slice(0, 10)); // Keep last 10
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const handleIndexPolicies = async () => {
    setIndexMessage(null);
    setIndexing((prev) => ({ ...prev, policies: true }));
    try {
      const data = await ragAPI.embedPolicies();
      const count = (data as any)?.policies_embedded ?? 0;
      setIndexMessage({ type: 'success', text: `Indexed ${count} policy document(s). You can now ask "What is the expense policy?" in RAG Only.` });
    } catch (err: any) {
      setIndexMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to index policies' });
    } finally {
      setIndexing((prev) => ({ ...prev, policies: false }));
    }
  };

  const handleIndexVatRules = async () => {
    setIndexMessage(null);
    setIndexing((prev) => ({ ...prev, vatRules: true }));
    try {
      const data = await ragAPI.embedVatRules();
      const count = (data as any)?.vat_rules_embedded ?? 0;
      setIndexMessage({ type: 'success', text: `Indexed ${count} VAT rule(s). You can now ask VAT questions in RAG Only.` });
    } catch (err: any) {
      setIndexMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to index VAT rules' });
    } finally {
      setIndexing((prev) => ({ ...prev, vatRules: false }));
    }
  };

  const handleIndexReceipts = async () => {
    setIndexMessage(null);
    setIndexing((prev) => ({ ...prev, receipts: true }));
    try {
      const data = await ragAPI.embedReceipts();
      const count = (data as any)?.receipts_embedded ?? 0;
      setIndexMessage({ type: 'success', text: `Indexed ${count} receipt(s). RAG can now answer questions about your receipts.` });
    } catch (err: any) {
      setIndexMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to index receipts' });
    } finally {
      setIndexing((prev) => ({ ...prev, receipts: false }));
    }
  };

  const getConfidenceColor = (score: string) => {
    switch (score.toLowerCase()) {
      case 'high':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-red-100 text-red-800';
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

  if (!isAuthenticated) {
    return (
      <>
        <div className="text-center py-12">Redirecting...</div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Audit Q&A</h1>
          <p className="text-gray-600 mt-2">Ask questions about expenses, policies, VAT rules, and more</p>
        </div>

        {(queryType === 'rag' || queryType === 'hybrid') && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-amber-800 mb-2">Index documents for RAG</h3>
            <p className="text-sm text-amber-700 mb-3">
              For RAG to answer, index documents first: policies and VAT rules (add rows in Admin if empty), and receipts (backfill from <code>receipt_documents</code>). Then ask with <strong>RAG Only</strong>.
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleIndexPolicies}
                disabled={indexing.policies}
                className="px-4 py-2 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 disabled:opacity-50"
              >
                {indexing.policies ? 'Indexing…' : 'Index policies'}
              </button>
              <button
                type="button"
                onClick={handleIndexVatRules}
                disabled={indexing.vatRules}
                className="px-4 py-2 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 disabled:opacity-50"
              >
                {indexing.vatRules ? 'Indexing…' : 'Index VAT rules'}
              </button>
              <button
                type="button"
                onClick={handleIndexReceipts}
                disabled={indexing.receipts}
                className="px-4 py-2 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 disabled:opacity-50"
              >
                {indexing.receipts ? 'Indexing…' : 'Index receipts'}
              </button>
            </div>
            {indexMessage && (
              <p className={`mt-2 text-sm ${indexMessage.type === 'success' ? 'text-green-700' : 'text-red-700'}`}>
                {indexMessage.text}
              </p>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Query Type
            </label>
            <select
              value={queryType}
              onChange={(e) => {
                setQueryType(e.target.value);
                setUseCopilot(e.target.value === 'agentic');
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="agentic">Agentic Co-Pilot (Recommended)</option>
              <option value="hybrid">Hybrid (SQL + RAG)</option>
              <option value="sql">SQL Only</option>
              <option value="rag">RAG Only</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., What is the total expense amount this month? What are the VAT rules for restaurants?"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Ask Question'}
          </button>
        </form>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {response && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Answer</h2>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs rounded-full ${getConfidenceColor(response.confidence_score)}`}>
                  {response.confidence_score} confidence
                </span>
                <span className="text-xs text-gray-500">{response.query_type}</span>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-gray-900 whitespace-pre-wrap">{response.answer}</p>
            </div>

            {response.explanation && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Explanation</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{response.explanation}</p>
              </div>
            )}

            {response.sql_query && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">SQL Query</h3>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">
                  {response.sql_query}
                </pre>
              </div>
            )}

            {response.sql_results && response.sql_results.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">SQL Results</h3>
                <div className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">
                  <pre>{JSON.stringify(response.sql_results, null, 2)}</pre>
                </div>
              </div>
            )}

            {response.retrieved_documents && response.retrieved_documents.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Retrieved Documents ({response.retrieved_documents.length})
                </h3>
                <div className="space-y-2">
                  {response.retrieved_documents.map((doc, idx) => (
                    <div key={idx} className="bg-gray-50 p-3 rounded text-sm">
                      <div className="font-medium text-gray-900">{doc.document_title}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Similarity: {(doc.similarity * 100).toFixed(1)}%
                      </div>
                      <div className="text-gray-600 mt-2 text-xs">{doc.chunk_text.substring(0, 200)}...</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {history.length > 0 && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Questions</h2>
            <div className="space-y-3">
              {history.map((item, idx) => (
                <div key={idx} className="border-b border-gray-200 pb-3 last:border-0">
                  <div className="font-medium text-gray-900 mb-1">{item.answer?.substring(0, 100)}...</div>
                  <div className="text-xs text-gray-500">
                    {item.query_type} • {item.confidence_score} confidence
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default QAPage;

