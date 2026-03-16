'use client';

import React, { useState, useRef } from 'react';
import { fileAPI } from '@/lib/api';

interface ReceiptUploadProps {
  redirectToReview?: boolean;
  onUploadComplete?: (receiptId: string) => void;
}

export default function ReceiptUpload({ redirectToReview = false, onUploadComplete }: ReceiptUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (file: File) => {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/heic', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type. Please upload JPG, PNG, HEIC, or PDF files.');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setError('File size exceeds 10MB limit. Please upload a smaller file.');
      return;
    }

    try {
      setUploading(true);
      setError('');
      setProgress(50); // Start progress

      // Upload file using fileAPI.upload
      // fileAPI.upload expects a File object and creates FormData internally
      const response = await fileAPI.upload(file);
      
      setProgress(100);
      
      // Call callback if provided
      // Response should have id, receipt_id, or file_id
      const receiptId = response.id || response.receipt_id || response.file_id || response.data?.id || response.data?.receipt_id || response.data?.file_id;
      if (onUploadComplete && receiptId) {
        onUploadComplete(receiptId);
      } else if (onUploadComplete && response) {
        // Fallback: try to extract any ID from response
        console.warn('ReceiptUpload: No receipt ID found in response', response);
        onUploadComplete(response.id || 'unknown');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload receipt. Please try again.');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/heic,application/pdf"
        onChange={handleFileInputChange}
        className="hidden"
        disabled={uploading}
      />

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${uploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}
        `}
      >
        {uploading ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Uploading receipt...</p>
              {progress > 0 && (
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center">
              <svg
                className="h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-gray-500 mt-1">
                JPG, PNG, HEIC, or PDF (max 10MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {!uploading && (
        <div className="mt-4 text-sm text-gray-600">
          <p className="font-medium mb-2">Supported formats:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>JPEG/JPG images</li>
            <li>PNG images</li>
            <li>HEIC images (iPhone photos)</li>
            <li>PDF documents</li>
          </ul>
        </div>
      )}
    </div>
  );
}
