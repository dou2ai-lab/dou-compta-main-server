'use client';

import React from 'react';

interface AnomalyExplanation {
  behavioural_patterns: {
    patterns: Array<{
      type: string;
      description: string;
      severity: string;
      risk_score: number;
    }>;
    severity: string;
    count: number;
  };
  vat_errors: {
    errors: Array<{
      type: string;
      description: string;
      severity: string;
      suggestion?: string;
      difference?: number;
    }>;
    severity: string;
    count: number;
  };
  policy_inconsistencies: {
    inconsistencies: Array<{
      type: string;
      description: string;
      severity: string;
      violations?: Array<{
        type: string;
        severity: string;
        message: string;
      }>;
      count?: number;
      suggestion?: string;
      risk_score?: number;
    }>;
    severity: string;
    count: number;
  };
  summary: string;
}

interface AnomalyExplanationsProps {
  explanations: AnomalyExplanation;
  riskScore: number;
  riskLevel: string;
  isAnomaly: boolean;
}

export default function AnomalyExplanations({
  explanations,
  riskScore,
  riskLevel,
  isAnomaly
}: AnomalyExplanationsProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h3 className="text-lg font-semibold text-gray-900">Anomaly Analysis</h3>
        <div className="mt-2 flex items-center gap-4">
          <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
            riskLevel === 'high' ? 'bg-red-100 text-red-800' :
            riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            Risk: {riskLevel.toUpperCase()} ({(riskScore * 100).toFixed(1)}%)
          </span>
          {isAnomaly && (
            <span className="px-3 py-1 text-sm font-semibold rounded-full bg-red-100 text-red-800">
              Anomaly Detected
            </span>
          )}
        </div>
        <p className="mt-3 text-sm text-gray-600">{explanations.summary}</p>
      </div>

      {/* Behavioural Patterns */}
      {explanations.behavioural_patterns.patterns.length > 0 && (
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">
            Behavioural Patterns
            <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getSeverityColor(explanations.behavioural_patterns.severity)}`}>
              {explanations.behavioural_patterns.severity}
            </span>
          </h4>
          <div className="space-y-2">
            {explanations.behavioural_patterns.patterns.map((pattern, idx) => (
              <div key={idx} className="border-l-4 border-yellow-400 pl-4 py-2 bg-yellow-50 rounded">
                <p className="text-sm font-medium text-gray-900">{pattern.description}</p>
                <p className="text-xs text-gray-600 mt-1">Risk Score: {(pattern.risk_score * 100).toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VAT Errors */}
      {explanations.vat_errors.errors.length > 0 && (
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">
            VAT Errors
            <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getSeverityColor(explanations.vat_errors.severity)}`}>
              {explanations.vat_errors.severity}
            </span>
          </h4>
          <div className="space-y-2">
            {explanations.vat_errors.errors.map((error, idx) => (
              <div key={idx} className="border-l-4 border-red-400 pl-4 py-2 bg-red-50 rounded">
                <p className="text-sm font-medium text-gray-900">{error.description}</p>
                {error.suggestion && (
                  <p className="text-xs text-blue-600 mt-1">💡 {error.suggestion}</p>
                )}
                {error.difference && (
                  <p className="text-xs text-gray-600 mt-1">Difference: €{error.difference.toFixed(2)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Policy Inconsistencies */}
      {explanations.policy_inconsistencies.inconsistencies.length > 0 && (
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">
            Policy Inconsistencies
            <span className={`ml-2 px-2 py-1 text-xs rounded-full ${getSeverityColor(explanations.policy_inconsistencies.severity)}`}>
              {explanations.policy_inconsistencies.severity}
            </span>
          </h4>
          <div className="space-y-2">
            {explanations.policy_inconsistencies.inconsistencies.map((inconsistency, idx) => (
              <div key={idx} className="border-l-4 border-red-400 pl-4 py-2 bg-red-50 rounded">
                <p className="text-sm font-medium text-gray-900">{inconsistency.description}</p>
                {inconsistency.violations && inconsistency.violations.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {inconsistency.violations.map((viol, vIdx) => (
                      <div key={vIdx} className="text-xs text-gray-700 pl-2 border-l-2 border-gray-300">
                        <span className="font-medium">{viol.type}:</span> {viol.message}
                      </div>
                    ))}
                  </div>
                )}
                {inconsistency.suggestion && (
                  <p className="text-xs text-blue-600 mt-1">💡 {inconsistency.suggestion}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {explanations.behavioural_patterns.patterns.length === 0 &&
       explanations.vat_errors.errors.length === 0 &&
       explanations.policy_inconsistencies.inconsistencies.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          No specific issues detected. This expense appears normal.
        </div>
      )}
    </div>
  );
}




