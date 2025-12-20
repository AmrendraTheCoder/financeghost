import { motion } from 'framer-motion';
import { UploadZone } from '../components/UploadZone';
import type { ProcessingResponse } from '../api';
import { useState } from 'react';
import { CheckCircle2, Sparkles } from 'lucide-react';

export function UploadPage() {
  const [processedCount, setProcessedCount] = useState(0);

  const handleUploadComplete = (_result: ProcessingResponse) => {
    setProcessedCount((c) => c + 1);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="mb-6">
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Upload Invoice</h1>
        <p className="text-muted">
          Upload invoices for AI-powered processing and automatic vendor communication
        </p>
      </div>

      {/* Main Upload Area */}
      <div className="grid-2">
        <div>
          <UploadZone onUploadComplete={handleUploadComplete} />

          {/* Processing Info */}
          {processedCount > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card mt-4"
              style={{ background: '#e6f4ea', border: '1px solid #34A853' }}
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 size={24} style={{ color: '#34A853' }} />
                <div>
                  <p className="font-medium" style={{ color: '#1e8e3e' }}>
                    {processedCount} invoice(s) processed this session
                  </p>
                  <p className="text-sm text-muted">
                    View results in the Invoices tab
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* How It Works */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-2">
              <Sparkles size={20} style={{ color: '#1a73e8' }} />
              <h3 className="card-title">How It Works</h3>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {[
              {
                step: 1,
                title: 'Upload Invoice',
                desc: 'Drop a PDF or image of your invoice',
              },
              {
                step: 2,
                title: 'AI Extraction',
                desc: 'Our Invoice Agent extracts all data using OCR + GPT-4',
              },
              {
                step: 3,
                title: 'Tax Validation',
                desc: 'Tax Agent validates GST calculations and GSTIN format',
              },
              {
                step: 4,
                title: 'Cash Flow Analysis',
                desc: 'Cash Flow Agent categorizes and predicts spending',
              },
              {
                step: 5,
                title: 'Auto Email',
                desc: 'If errors found, we generate a vendor email for you',
              },
            ].map(({ step, title, desc }) => (
              <div key={step} className="flex gap-4">
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: 'var(--primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    flexShrink: 0,
                  }}
                >
                  {step}
                </div>
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="text-sm text-muted">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Supported Formats */}
          <div
            style={{
              marginTop: 24,
              padding: 16,
              background: 'var(--bg-secondary)',
              borderRadius: 8,
            }}
          >
            <p className="text-xs text-muted mb-2">Supported Formats</p>
            <div className="flex gap-2">
              {['PDF', 'PNG', 'JPG', 'TIFF'].map((fmt) => (
                <span
                  key={fmt}
                  style={{
                    padding: '4px 12px',
                    background: 'var(--bg-primary)',
                    borderRadius: 4,
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    border: '1px solid var(--gray-200)',
                  }}
                >
                  {fmt}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid-3 mt-6">
        {[
          {
            title: 'GSTIN Validation',
            desc: 'Automatically validates vendor GSTIN format and state code',
            color: '#4285F4',
          },
          {
            title: 'Tax Verification',
            desc: 'Checks CGST/SGST/IGST calculations against standard slabs',
            color: '#34A853',
          },
          {
            title: 'Smart Emails',
            desc: 'AI-generated professional emails for vendor corrections',
            color: '#FBBC05',
          },
        ].map(({ title, desc, color }) => (
          <div key={title} className="card">
            <div
              style={{
                width: 40,
                height: 4,
                background: color,
                borderRadius: 2,
                marginBottom: 16,
              }}
            />
            <h4 className="font-medium mb-2">{title}</h4>
            <p className="text-sm text-muted">{desc}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
