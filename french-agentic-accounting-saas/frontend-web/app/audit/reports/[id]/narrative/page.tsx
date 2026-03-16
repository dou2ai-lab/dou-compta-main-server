'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { auditAPI } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { format } from 'date-fns';
import Link from 'next/link';

interface Narrative {
  introduction: string;
  executive_summary: {
    overview: string;
    key_findings: string[];
    risk_assessment: string;
    recommendations_summary: string;
  };
  detailed_findings: {
    anomalies: string;
    policy_compliance: string;
    process_observations: string[];
    control_effectiveness: string;
  };
  trend_analysis: {
    spend_trend: string;
    vat_trend: string;
    compliance_trend: string;
  };
  conclusions: {
    overall_assessment: string;
    risk_level: string;
    compliance_status: string;
  };
}

function NarrativePage() {
  const router = useRouter();
  const params = useParams();
  const reportId = params?.id as string;
  
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [generating, setGenerating] = useState(false);
  const [narrative, setNarrative] = useState<Narrative | null>(null);
  const [error, setError] = useState('');
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    if (reportId && (isAuthenticated || !authLoading)) {
      loadReport();
    }
  }, [reportId, isAuthenticated, authLoading]);

  const loadReport = async () => {
    try {
      const data = await auditAPI.getReport(reportId);
      setReport(data);
    } catch (err: any) {
      console.error('Failed to load report:', err);
    }
  };

  const handleGenerate = async () => {
    if (!report) return;

    setGenerating(true);
    setError('');

    try {
      const data = await auditAPI.generateNarrative(
        report.audit_period_start,
        report.audit_period_end,
        reportId,
        {
          spend_summary: report.technical_data?.executive_summary,
          policy_violations: report.technical_data?.findings?.policy_violations || [],
          vat_summary: {}
        }
      );
      setNarrative(data.narratives);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate narrative');
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

  if (!report) {
    return (
      <>
        <div className="text-center py-12">Loading report...</div>
      </>
    );
  }

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <Link
              href={`/audit/reports/${reportId}`}
              className="text-blue-600 hover:text-blue-900 mb-2 inline-block"
            >
              ← Back to Report
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Generate Narrative</h1>
            <p className="text-gray-600 mt-2">Generate narrative text for audit report</p>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? 'Generating...' : 'Generate Narrative'}
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {generating && (
          <div className="mb-4 bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
            Generating narrative using LLM... This may take a moment.
          </div>
        )}

        {narrative && (
          <div className="space-y-6">
            {/* Introduction */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Introduction</h2>
              <p className="text-gray-700 whitespace-pre-wrap">{narrative.introduction}</p>
            </div>

            {/* Executive Summary */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Executive Summary</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Overview</h3>
                  <p className="text-gray-700">{narrative.executive_summary.overview}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Key Findings</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {narrative.executive_summary.key_findings.map((finding, idx) => (
                      <li key={idx}>{finding}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Risk Assessment</h3>
                  <p className="text-gray-700">{narrative.executive_summary.risk_assessment}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Recommendations Summary</h3>
                  <p className="text-gray-700">{narrative.executive_summary.recommendations_summary}</p>
                </div>
              </div>
            </div>

            {/* Detailed Findings */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Detailed Findings</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Anomalies</h3>
                  <p className="text-gray-700">{narrative.detailed_findings.anomalies}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Policy Compliance</h3>
                  <p className="text-gray-700">{narrative.detailed_findings.policy_compliance}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Process Observations</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {narrative.detailed_findings.process_observations.map((obs, idx) => (
                      <li key={idx}>{obs}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Control Effectiveness</h3>
                  <p className="text-gray-700">{narrative.detailed_findings.control_effectiveness}</p>
                </div>
              </div>
            </div>

            {/* Trend Analysis */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Trend Analysis</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Spend Trends</h3>
                  <p className="text-gray-700">{narrative.trend_analysis.spend_trend}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">VAT Recovery Changes</h3>
                  <p className="text-gray-700">{narrative.trend_analysis.vat_trend}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Policy Compliance Trends</h3>
                  <p className="text-gray-700">{narrative.trend_analysis.compliance_trend}</p>
                </div>
              </div>
            </div>

            {/* Conclusions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Conclusions</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Overall Assessment</h3>
                  <p className="text-gray-700">{narrative.conclusions.overall_assessment}</p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Risk Level</h3>
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                    narrative.conclusions.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                    narrative.conclusions.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {narrative.conclusions.risk_level.toUpperCase()}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Compliance Status</h3>
                  <p className="text-gray-700">{narrative.conclusions.compliance_status}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default NarrativePage;




