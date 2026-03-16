'use client';

import React, { useState } from 'react';

interface PolicyViolation {
  id?: string;
  policy_id: string;
  violation_type: string;
  violation_severity: 'info' | 'warning' | 'error';
  violation_message: string;
  policy_rule?: Record<string, any>;
  requires_comment: boolean;
  comment_provided?: string;
  is_resolved?: boolean;
}

interface PolicyViolationsProps {
  violations: PolicyViolation[];
  onCommentChange?: (violationId: string, comment: string) => void;
  showResolveButton?: boolean;
  onResolve?: (violationId: string) => void;
}

export default function PolicyViolations({
  violations,
  onCommentChange,
  showResolveButton = false,
  onResolve
}: PolicyViolationsProps) {
  const [comments, setComments] = useState<Record<string, string>>({});

  if (!violations || violations.length === 0) {
    return null;
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const handleCommentChange = (violationId: string, comment: string) => {
    setComments({ ...comments, [violationId]: comment });
    if (onCommentChange) {
      onCommentChange(violationId, comment);
    }
  };

  const errorCount = violations.filter(v => v.violation_severity === 'error').length;
  const warningCount = violations.filter(v => v.violation_severity === 'warning').length;
  const infoCount = violations.filter(v => v.violation_severity === 'info').length;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Policy Violations</h3>
        <div className="flex gap-2 text-sm">
          {errorCount > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-800 rounded">
              {errorCount} Error{errorCount !== 1 ? 's' : ''}
            </span>
          )}
          {warningCount > 0 && (
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
              {warningCount} Warning{warningCount !== 1 ? 's' : ''}
            </span>
          )}
          {infoCount > 0 && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
              {infoCount} Info
            </span>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {violations.map((violation, index) => {
          const violationId = violation.id || `violation-${index}`;
          const isResolved = violation.is_resolved || false;
          
          if (isResolved) {
            return null; // Don't show resolved violations
          }

          return (
            <div
              key={violationId}
              className={`border rounded-lg p-4 ${getSeverityColor(violation.violation_severity)}`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getSeverityIcon(violation.violation_severity)}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium mb-1">{violation.violation_message}</p>
                      <p className="text-xs opacity-75">
                        Type: {violation.violation_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                    </div>
                    {showResolveButton && onResolve && (
                      <button
                        onClick={() => onResolve(violationId)}
                        className="ml-4 px-3 py-1 text-xs bg-white bg-opacity-50 hover:bg-opacity-75 rounded transition-colors"
                      >
                        Resolve
                      </button>
                    )}
                  </div>

                  {violation.requires_comment && (
                    <div className="mt-3">
                      <label className="block text-sm font-medium mb-1">
                        Comment Required {violation.violation_severity === 'error' && <span className="text-red-600">*</span>}
                      </label>
                      <textarea
                        value={comments[violationId] || violation.comment_provided || ''}
                        onChange={(e) => handleCommentChange(violationId, e.target.value)}
                        placeholder="Please provide a comment explaining this violation..."
                        rows={3}
                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                          violation.violation_severity === 'error'
                            ? 'border-red-300 focus:ring-red-500'
                            : 'border-yellow-300 focus:ring-yellow-500'
                        }`}
                        required={violation.violation_severity === 'error'}
                      />
                      {violation.violation_severity === 'error' && !comments[violationId] && !violation.comment_provided && (
                        <p className="mt-1 text-xs text-red-600">
                          A comment is required to submit this expense
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {errorCount > 0 && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            <strong>Note:</strong> Expenses with error-level policy violations cannot be submitted until resolved.
          </p>
        </div>
      )}
    </div>
  );
}
