import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { getEmails } from '../api';
import { Mail, Copy, CheckCircle, Send, Clock } from 'lucide-react';

interface Email {
  id: number;
  invoice_id: number;
  vendor_name: string;
  subject: string;
  body: string;
  status: string;
  created_at: string;
  sent_at: string | null;
}

export function EmailsPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchEmails();
  }, []);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const result = await getEmails();
      setEmails(result.emails);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="page-content"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Vendor Emails</h1>
          <p className="text-muted">AI-generated emails for vendor communication</p>
        </div>
      </div>

      <div className="grid-2">
        {/* Email List */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Generated Emails</h3>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="spinner" />
            </div>
          ) : emails.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {emails.map((email) => (
                <div
                  key={email.id}
                  onClick={() => setSelectedEmail(email)}
                  style={{
                    padding: 16,
                    borderRadius: 8,
                    background:
                      selectedEmail?.id === email.id
                        ? 'var(--primary-light)'
                        : 'var(--bg-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    border:
                      selectedEmail?.id === email.id
                        ? '1px solid var(--primary)'
                        : '1px solid transparent',
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 8,
                        background: 'var(--primary-light)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Mail size={20} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <p className="font-medium">{email.vendor_name}</p>
                      <p
                        className="text-sm text-muted"
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {email.subject}
                      </p>
                    </div>
                    <span
                      className={`badge ${
                        email.status === 'sent'
                          ? 'badge-success'
                          : email.status === 'draft'
                          ? 'badge-info'
                          : 'badge-warning'
                      }`}
                    >
                      {email.status === 'sent' ? (
                        <Send size={12} style={{ marginRight: 4 }} />
                      ) : (
                        <Clock size={12} style={{ marginRight: 4 }} />
                      )}
                      {email.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted">
              <Mail size={48} style={{ marginBottom: 8, opacity: 0.3 }} />
              <p className="mb-2">No emails generated yet</p>
              <p className="text-sm">
                Upload invoices with errors to generate vendor emails
              </p>
            </div>
          )}
        </div>

        {/* Email Preview */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Email Preview</h3>
            {selectedEmail && (
              <button
                className="btn btn-secondary"
                onClick={() =>
                  copyToClipboard(`Subject: ${selectedEmail.subject}\n\n${selectedEmail.body}`)
                }
              >
                {copied ? (
                  <>
                    <CheckCircle size={16} />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    Copy
                  </>
                )}
              </button>
            )}
          </div>

          {selectedEmail ? (
            <div>
              <div
                style={{
                  padding: 16,
                  background: 'var(--bg-secondary)',
                  borderRadius: 8,
                  marginBottom: 16,
                }}
              >
                <div className="mb-2">
                  <span className="text-xs text-muted">To: </span>
                  <span className="text-sm font-medium">{selectedEmail.vendor_name}</span>
                </div>
                <div>
                  <span className="text-xs text-muted">Subject: </span>
                  <span className="text-sm font-medium">{selectedEmail.subject}</span>
                </div>
              </div>

              <div className="email-preview">{selectedEmail.body}</div>

              <div className="flex gap-2 mt-4">
                <button className="btn btn-primary">
                  <Send size={16} />
                  Send Email
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() =>
                    copyToClipboard(`Subject: ${selectedEmail.subject}\n\n${selectedEmail.body}`)
                  }
                >
                  <Copy size={16} />
                  Copy to Clipboard
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted">
              Select an email to preview
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
