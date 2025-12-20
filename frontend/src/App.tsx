import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { InvoicesPage } from './pages/InvoicesPage';
import { EmailsPage } from './pages/EmailsPage';
import { VendorsPage } from './pages/VendorsPage';
import { AuditPage } from './pages/AuditPage';
import OpsIntelligencePage from './pages/OpsIntelligencePage';
import { GhostTerminal } from './components/GhostTerminal';
import { VoiceAssistant } from './components/VoiceAssistant';
import { ThemeToggle } from './components/ThemeToggle';
import { Ghost, Mic } from 'lucide-react';

function App() {
  const [showGhostTerminal, setShowGhostTerminal] = useState(false);
  const [showVoiceAssistant, setShowVoiceAssistant] = useState(false);

  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          {/* Top Bar */}
          <div
            style={{
              position: 'fixed',
              top: 16,
              right: 24,
              display: 'flex',
              gap: 8,
              zIndex: 100,
            }}
          >
            <ThemeToggle />
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => setShowVoiceAssistant(true)}
              title="Voice Assistant"
              style={{
                background: 'var(--bg-primary)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <Mic size={20} />
            </button>
            <button
              className="btn btn-ghost btn-icon"
              onClick={() => setShowGhostTerminal(!showGhostTerminal)}
              title="Ghost Mode Terminal"
              style={{
                background: showGhostTerminal ? 'var(--primary)' : 'var(--bg-primary)',
                color: showGhostTerminal ? 'white' : 'var(--text-secondary)',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <Ghost size={20} />
            </button>
          </div>

          <Routes>
            <Route path="/" element={<OpsIntelligencePage />} />
            <Route path="/ops" element={<OpsIntelligencePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/invoices" element={<InvoicesPage />} />
            <Route path="/emails" element={<EmailsPage />} />
            <Route path="/vendors" element={<VendorsPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/help" element={<HelpPage />} />
          </Routes>
        </main>

        {/* Ghost Mode Terminal */}
        <GhostTerminal
          isOpen={showGhostTerminal}
          onClose={() => setShowGhostTerminal(false)}
        />

        {/* Voice Assistant */}
        <VoiceAssistant
          isOpen={showVoiceAssistant}
          onClose={() => setShowVoiceAssistant(false)}
        />
      </div>
    </BrowserRouter>
  );
}

// Simple Settings Page
function SettingsPage() {
  return (
    <div className="page-content">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Settings</h1>
      <p className="text-muted mb-6">Configure your FinanceGhost preferences</p>

      <div className="card mb-4">
        <h3 className="card-title mb-4">API Configuration</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label className="text-sm text-muted block mb-2">Company Name</label>
            <input
              type="text"
              className="input"
              placeholder="Your Company Name"
              defaultValue="FinanceGhost User"
            />
          </div>
          <div>
            <label className="text-sm text-muted block mb-2">API Endpoint</label>
            <input
              type="text"
              className="input"
              placeholder="http://localhost:8000"
              defaultValue="http://localhost:8000"
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="card-title mb-4">AI Agent Settings</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[
            { name: 'Invoice Agent', desc: 'Extract data from invoices', enabled: true },
            { name: 'Tax Agent', desc: 'Validate GST calculations', enabled: true },
            { name: 'Cash Flow Agent', desc: 'Categorize and predict spending', enabled: true },
            { name: 'Email Generator', desc: 'Generate vendor emails', enabled: true },
          ].map((agent) => (
            <div
              key={agent.name}
              className="flex items-center justify-between"
              style={{ padding: 12, background: 'var(--bg-secondary)', borderRadius: 8 }}
            >
              <div>
                <p className="font-medium">{agent.name}</p>
                <p className="text-sm text-muted">{agent.desc}</p>
              </div>
              <div
                style={{
                  width: 44,
                  height: 24,
                  borderRadius: 12,
                  background: agent.enabled ? 'var(--success)' : 'var(--gray-300)',
                  position: 'relative',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    background: 'white',
                    position: 'absolute',
                    top: 2,
                    left: agent.enabled ? 22 : 2,
                    transition: 'left 0.2s ease',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Simple Help Page
function HelpPage() {
  return (
    <div className="page-content">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Help & Documentation</h1>
      <p className="text-muted mb-6">Learn how to use FinanceGhost Autonomous</p>

      <div className="grid-2">
        <div className="card">
          <h3 className="card-title mb-4">🚀 Quick Start</h3>
          <ol style={{ listStyle: 'decimal', paddingLeft: 20, color: 'var(--text-secondary)' }}>
            <li style={{ marginBottom: 8 }}>Upload an invoice (PDF or image)</li>
            <li style={{ marginBottom: 8 }}>Our AI agents extract and validate data</li>
            <li style={{ marginBottom: 8 }}>Review any errors or warnings</li>
            <li style={{ marginBottom: 8 }}>Copy/send generated vendor emails</li>
            <li>Track spending in the dashboard</li>
          </ol>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">🤖 AI Agents</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <p className="font-medium">Invoice Agent</p>
              <p className="text-sm text-muted">
                Uses OCR + GPT-4/Vertex AI to extract structured data from invoices
              </p>
            </div>
            <div>
              <p className="font-medium">Tax Agent</p>
              <p className="text-sm text-muted">
                Validates GSTIN format, GST calculations, and tax slabs
              </p>
            </div>
            <div>
              <p className="font-medium">Cash Flow Agent</p>
              <p className="text-sm text-muted">
                Categorizes expenses and predicts monthly spending
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">👻 Ghost Mode</h3>
          <p className="text-muted">
            Click the ghost icon in the top-right to see real-time AI agent activity.
            Watch as agents process invoices, validate taxes, and generate emails.
          </p>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">🎙️ Voice Commands</h3>
          <p className="text-muted">
            Click the microphone icon to use voice commands. Ask questions like
            "How much did we spend on IT?" or "Show invoices needing review".
          </p>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">💰 Vendor Intelligence</h3>
          <p className="text-muted">
            Analyze vendor spending patterns and get AI-powered negotiation scripts
            to save money on your top vendors.
          </p>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">🛡️ Audit Defense</h3>
          <p className="text-muted">
            Download audit-ready compliance packs with all invoices, tax summaries,
            and vendor reports in one ZIP file.
          </p>
        </div>
      </div>

      <div className="card mt-6">
        <h3 className="card-title mb-4">🔧 API Endpoints</h3>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Method</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>/upload</code></td>
                <td>POST</td>
                <td>Upload and process invoice file</td>
              </tr>
              <tr>
                <td><code>/cashflow/forecast</code></td>
                <td>GET</td>
                <td>Get predictive cash flow forecast</td>
              </tr>
              <tr>
                <td><code>/vendors/analysis</code></td>
                <td>GET</td>
                <td>Get vendor spend analysis</td>
              </tr>
              <tr>
                <td><code>/vendors/negotiations</code></td>
                <td>GET</td>
                <td>Get negotiation opportunities</td>
              </tr>
              <tr>
                <td><code>/audit/download</code></td>
                <td>GET</td>
                <td>Download audit compliance pack</td>
              </tr>
              <tr>
                <td><code>/voice/command</code></td>
                <td>POST</td>
                <td>Process voice command</td>
              </tr>
              <tr>
                <td><code>/ws/agent-logs</code></td>
                <td>WebSocket</td>
                <td>Real-time agent activity stream</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
