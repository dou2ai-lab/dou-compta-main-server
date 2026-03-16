'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import ReceiptUpload from '@/components/ReceiptUpload';

export default function UploadReceiptPage() {
  const router = useRouter();
  const [uploadedReceiptId, setUploadedReceiptId] = useState<string | null>(null);

  const handleUploadComplete = (receiptId: string) => {
    setUploadedReceiptId(receiptId);
    // Redirect to review page after a short delay to allow processing to start
    setTimeout(() => {
      router.push(`/expenses/review/${receiptId}`);
    }, 2000);
  };

  return (
    <>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Receipt</h1>
          <p className="text-gray-600">
            Upload a receipt image or PDF. Our AI will extract the details automatically.
          </p>
        </div>

        {uploadedReceiptId && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-800">
                  Receipt uploaded successfully! Processing...
                </p>
                <p className="text-sm text-blue-700 mt-1">
                  Redirecting to review page in a moment...
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white shadow rounded-lg p-6">
          <ReceiptUpload 
            redirectToReview={true}
            onUploadComplete={handleUploadComplete}
          />
        </div>

        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-2">How it works:</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-gray-600">
            <li>Upload your receipt (JPG, PNG, HEIC, or PDF)</li>
            <li>Our OCR service extracts text from the receipt</li>
            <li>AI processes the text to extract structured data (merchant, date, amount, VAT)</li>
            <li>Review and edit the extracted information</li>
            <li>Create the expense with one click</li>
          </ol>
        </div>
      </div>
    </>
  );
}

