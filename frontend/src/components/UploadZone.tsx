import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  Mail,
  Loader2,
  Image,
} from 'lucide-react';
import { uploadInvoice } from '../api';
import type { ProcessingResponse } from '../api';

interface UploadZoneProps {
  onUploadComplete?: (result: ProcessingResponse) => void;
}

export function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ProcessingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      setSelectedFile(file);
      setError(null);
      setResult(null);

      // Generate preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        setPreview(null);
      }
    },
    []
  );

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);

    try {
      const response = await uploadInvoice(selectedFile);
      setResult(response);
      onUploadComplete?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  const clearAll = () => {
    setResult(null);
    setError(null);
    setSelectedFile(null);
    setPreview(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Upload Invoice</h3>
          <p className="card-subtitle">Upload PDF or image files for AI processing</p>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {!result && !error && (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <div
              {...getRootProps()}
              className={`dropzone ${isDragActive ? 'active' : ''} ${
                uploading ? 'opacity-50 pointer-events-none' : ''
              }`}
              style={{
                background: isDragActive
                  ? 'linear-gradient(135deg, var(--primary-light), #e8f5e9)'
                  : selectedFile
                  ? 'var(--bg-secondary)'
                  : undefined,
              }}
            >
              <input {...getInputProps()} />
              
              {selectedFile ? (
                <div style={{ width: '100%' }}>
                  {/* File Preview */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: 16,
                      background: 'var(--bg-primary)',
                      borderRadius: 12,
                      marginBottom: 16,
                      border: '1px solid var(--gray-200)',
                    }}
                  >
                    {/* Thumbnail */}
                    <div
                      style={{
                        width: 80,
                        height: 80,
                        borderRadius: 8,
                        overflow: 'hidden',
                        background: 'var(--gray-100)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {preview ? (
                        <img
                          src={preview}
                          alt={selectedFile.name}
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                          }}
                        />
                      ) : selectedFile.type === 'application/pdf' ? (
                        <FileText size={36} style={{ color: '#EA4335' }} />
                      ) : (
                        <Image size={36} style={{ color: 'var(--gray-400)' }} />
                      )}
                    </div>

                    {/* File Info */}
                    <div style={{ flex: 1, textAlign: 'left' }}>
                      <p
                        style={{
                          fontWeight: 500,
                          fontSize: 14,
                          marginBottom: 4,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {selectedFile.name}
                      </p>
                      <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        {formatFileSize(selectedFile.size)} •{' '}
                        {selectedFile.type.split('/')[1]?.toUpperCase() || 'File'}
                      </p>
                    </div>

                    {/* Remove Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        clearAll();
                      }}
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: '50%',
                        border: 'none',
                        background: 'var(--gray-100)',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <X size={16} />
                    </button>
                  </div>

                  {/* Upload Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUpload();
                    }}
                    disabled={uploading}
                    className="btn btn-primary"
                    style={{ width: '100%' }}
                  >
                    {uploading ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Processing with AI...
                      </>
                    ) : (
                      <>
                        <Upload size={18} />
                        Process Invoice
                      </>
                    )}
                  </button>
                </div>
              ) : (
                <>
                  <div
                    style={{
                      width: 80,
                      height: 80,
                      borderRadius: '50%',
                      background: isDragActive
                        ? 'var(--primary)'
                        : 'linear-gradient(135deg, var(--primary-light), #e8f5e9)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 16px',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <Upload
                      size={32}
                      style={{
                        color: isDragActive ? 'white' : 'var(--primary)',
                      }}
                    />
                  </div>
                  <p className="dropzone-title">
                    {isDragActive ? 'Drop file here' : 'Drag & drop invoice'}
                  </p>
                  <p className="dropzone-subtitle">
                    or click to browse • PDF, PNG, JPG supported
                  </p>
                  <div
                    style={{
                      display: 'flex',
                      gap: 8,
                      marginTop: 16,
                      justifyContent: 'center',
                    }}
                  >
                    {['PDF', 'PNG', 'JPG', 'TIFF'].map((fmt) => (
                      <span
                        key={fmt}
                        style={{
                          padding: '4px 12px',
                          background: 'var(--bg-primary)',
                          borderRadius: 4,
                          fontSize: '0.7rem',
                          fontWeight: 500,
                          border: '1px solid var(--gray-200)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {fmt}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>
          </motion.div>
        )}

        {result && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="result-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {result.errors_count > 0 ? (
                  <AlertCircle size={24} style={{ color: '#FBBC05' }} />
                ) : (
                  <CheckCircle size={24} style={{ color: '#34A853' }} />
                )}
                <span className="font-medium">
                  {result.errors_count > 0
                    ? `Processed with ${result.errors_count} issue(s)`
                    : 'Invoice processed successfully'}
                </span>
              </div>
              <button className="btn btn-ghost btn-icon" onClick={clearAll}>
                <X size={18} />
              </button>
            </div>

            <div className="grid-2 mb-4">
              <div>
                <p className="text-xs text-muted">Invoice Number</p>
                <p className="font-medium">{result.invoice_number || 'N/A'}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Vendor</p>
                <p className="font-medium">{result.vendor_name || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Amount</p>
                <p className="font-medium">
                  ₹{result.total_amount?.toLocaleString('en-IN') || '0'}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted">Processing Time</p>
                <p className="font-medium">{result.processing_time_ms.toFixed(0)}ms</p>
              </div>
            </div>

            <div className="flex gap-2">
              <span
                className={`badge ${
                  result.status === 'processed'
                    ? 'badge-success'
                    : result.status === 'needs_review'
                    ? 'badge-warning'
                    : 'badge-info'
                }`}
              >
                {result.status?.replace('_', ' ')}
              </span>
              {result.has_email && (
                <span className="badge badge-info">
                  <Mail size={12} style={{ marginRight: 4 }} />
                  Email generated
                </span>
              )}
            </div>

            {result.generated_email && (
              <div className="mt-4">
                <p className="text-xs text-muted mb-2">Generated Vendor Email</p>
                <div className="email-preview">{result.generated_email}</div>
              </div>
            )}

            <button className="btn btn-primary mt-4" onClick={clearAll}>
              <FileText size={18} />
              Upload Another
            </button>
          </motion.div>
        )}

        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <div className="flex items-center gap-3 p-4" style={{ background: '#fce8e6', borderRadius: 8 }}>
              <AlertCircle size={24} style={{ color: '#EA4335' }} />
              <div className="flex-1">
                <p className="font-medium" style={{ color: '#EA4335' }}>
                  Upload Failed
                </p>
                <p className="text-sm text-muted">{error}</p>
              </div>
              <button className="btn btn-ghost btn-icon" onClick={clearAll}>
                <X size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
