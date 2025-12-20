import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Minimize2,
  Maximize2,
  Ghost,
  Cpu,
  Zap,
  CheckCircle,
  AlertTriangle,
  Clock,
  Activity,
} from 'lucide-react';

interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
  level: string;
}

interface GhostTerminalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AGENT_CONFIG: Record<string, { color: string; icon: string; name: string; gradient: string }> = {
  ORCHESTRATOR: {
    color: '#58a6ff',
    icon: '🎯',
    name: 'Orchestrator',
    gradient: 'linear-gradient(135deg, #58a6ff, #1f6feb)',
  },
  invoice_agent: {
    color: '#3fb950',
    icon: '📄',
    name: 'Invoice Agent',
    gradient: 'linear-gradient(135deg, #3fb950, #238636)',
  },
  tax_agent: {
    color: '#d29922',
    icon: '💰',
    name: 'Tax Agent',
    gradient: 'linear-gradient(135deg, #d29922, #9e6a03)',
  },
  cashflow_agent: {
    color: '#f85149',
    icon: '📊',
    name: 'Cash Flow Agent',
    gradient: 'linear-gradient(135deg, #f85149, #da3633)',
  },
  SYSTEM: {
    color: '#8b949e',
    icon: '⚙️',
    name: 'System',
    gradient: 'linear-gradient(135deg, #8b949e, #6e7681)',
  },
  default: {
    color: '#a371f7',
    icon: '🤖',
    name: 'Agent',
    gradient: 'linear-gradient(135deg, #a371f7, #8957e5)',
  },
};

export function GhostTerminal({ isOpen, onClose }: GhostTerminalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [activeAgents, setActiveAgents] = useState<Set<string>>(new Set());
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const processingStartRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws/agent-logs`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          addSystemLog('Connected to FinanceGhost Neural Network', 'success');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'history') {
              setLogs(data.logs || []);
            } else if (data.type === 'log') {
              const log = data.data;
              setLogs((prev) => [...prev.slice(-199), log]);

              // Track active agents
              if (log.message.includes('Starting')) {
                setActiveAgents((prev) => new Set([...prev, log.agent]));
                if (log.agent === 'ORCHESTRATOR') {
                  processingStartRef.current = Date.now();
                  setProcessingTime(null);
                }
              } else if (log.message.includes('complete') || log.message.includes('Complete')) {
                setActiveAgents((prev) => {
                  const next = new Set(prev);
                  next.delete(log.agent);
                  return next;
                });
                if (log.agent === 'ORCHESTRATOR' && processingStartRef.current) {
                  setProcessingTime(Date.now() - processingStartRef.current);
                }
              }
            } else if (data.type === 'processing_start') {
              addSystemLog(`📥 Processing: ${data.filename}`, 'info');
              processingStartRef.current = Date.now();
            } else if (data.type === 'processing_complete') {
              addSystemLog('✅ Processing complete', 'success');
              if (processingStartRef.current) {
                setProcessingTime(Date.now() - processingStartRef.current);
              }
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          addSystemLog('Connection lost. Reconnecting...', 'warning');
          setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (e) {
        console.error('WebSocket connection failed:', e);
      }
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isOpen]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const addSystemLog = (message: string, level: string = 'info') => {
    setLogs((prev) => [
      ...prev.slice(-199),
      {
        timestamp: new Date().toISOString(),
        agent: 'SYSTEM',
        message,
        level,
      },
    ]);
  };

  const getAgentConfig = (agent: string) => AGENT_CONFIG[agent] || AGENT_CONFIG.default;

  const getWidth = () => {
    if (isMinimized) return 320;
    if (isExpanded) return 700;
    return 520;
  };

  const getHeight = () => {
    if (isMinimized) return 56;
    if (isExpanded) return 600;
    return 420;
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: getWidth(),
          height: getHeight(),
          background: 'linear-gradient(180deg, #0d1117 0%, #010409 100%)',
          borderRadius: 16,
          boxShadow: '0 0 0 1px rgba(48, 54, 61, 0.5), 0 16px 64px rgba(0, 0, 0, 0.6), 0 0 80px rgba(88, 166, 255, 0.1)',
          zIndex: 1000,
          overflow: 'hidden',
          fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace",
          transition: 'width 0.3s ease, height 0.3s ease',
        }}
      >
        {/* Animated border glow */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: 16,
            padding: 1,
            background: isConnected
              ? 'linear-gradient(135deg, rgba(63, 185, 80, 0.3), rgba(88, 166, 255, 0.3), rgba(163, 113, 247, 0.3))'
              : 'linear-gradient(135deg, rgba(248, 81, 73, 0.3), rgba(210, 153, 34, 0.3))',
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'xor',
            maskComposite: 'exclude',
            animation: 'borderGlow 3s linear infinite',
            pointerEvents: 'none',
          }}
        />

        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            background: 'rgba(22, 27, 34, 0.8)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(48, 54, 61, 0.5)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <motion.div
              animate={{ rotate: isConnected ? [0, 360] : 0 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Ghost size={20} style={{ color: '#58a6ff' }} />
            </motion.div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#f0f6fc', fontSize: 13, fontWeight: 600 }}>
                  Ghost Mode
                </span>
                <motion.span
                  animate={{ opacity: [1, 0.5, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: isConnected ? '#3fb950' : '#f85149',
                    boxShadow: isConnected ? '0 0 8px #3fb950' : '0 0 8px #f85149',
                  }}
                />
              </div>
              {!isMinimized && (
                <span style={{ color: '#8b949e', fontSize: 10 }}>
                  {isConnected ? 'Neural link active' : 'Reconnecting...'}
                </span>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            {/* Processing time indicator */}
            {processingTime && !isMinimized && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '4px 8px',
                  background: 'rgba(63, 185, 80, 0.1)',
                  borderRadius: 6,
                  marginRight: 8,
                }}
              >
                <Clock size={12} style={{ color: '#3fb950' }} />
                <span style={{ color: '#3fb950', fontSize: 10 }}>{processingTime}ms</span>
              </div>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#8b949e',
                cursor: 'pointer',
                padding: 6,
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#8b949e',
                cursor: 'pointer',
                padding: 6,
                borderRadius: 6,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Agent Status Bar */}
        {!isMinimized && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 16px',
              background: 'rgba(22, 27, 34, 0.5)',
              borderBottom: '1px solid rgba(48, 54, 61, 0.3)',
              overflowX: 'auto',
            }}
          >
            {['ORCHESTRATOR', 'invoice_agent', 'tax_agent', 'cashflow_agent'].map((agent) => {
              const config = getAgentConfig(agent);
              const isActive = activeAgents.has(agent);
              return (
                <motion.div
                  key={agent}
                  animate={{ scale: isActive ? [1, 1.05, 1] : 1 }}
                  transition={{ duration: 0.5, repeat: isActive ? Infinity : 0 }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '4px 10px',
                    background: isActive ? config.gradient : 'rgba(48, 54, 61, 0.3)',
                    borderRadius: 20,
                    fontSize: 10,
                    color: isActive ? '#fff' : '#8b949e',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.3s ease',
                  }}
                >
                  <span>{config.icon}</span>
                  <span>{config.name}</span>
                  {isActive && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    >
                      <Activity size={10} />
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Terminal Content */}
        {!isMinimized && (
          <div
            ref={terminalRef}
            style={{
              height: 'calc(100% - 100px)',
              overflow: 'auto',
              padding: 16,
              fontSize: 12,
              lineHeight: 1.8,
            }}
          >
            {logs.length === 0 ? (
              <div style={{ textAlign: 'center', paddingTop: 60 }}>
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Cpu size={48} style={{ color: '#30363d', marginBottom: 16 }} />
                </motion.div>
                <p style={{ color: '#8b949e', marginBottom: 8 }}>
                  Awaiting neural activity...
                </p>
                <p style={{ color: '#484f58', fontSize: 11 }}>
                  Upload an invoice to activate AI agents
                </p>
              </div>
            ) : (
              logs.map((log, i) => {
                const config = getAgentConfig(log.agent);
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 12,
                      marginBottom: 8,
                      padding: '8px 12px',
                      background:
                        log.level === 'error'
                          ? 'rgba(248, 81, 73, 0.1)'
                          : log.level === 'warning'
                          ? 'rgba(210, 153, 34, 0.1)'
                          : 'transparent',
                      borderRadius: 8,
                      borderLeft: `3px solid ${config.color}`,
                    }}
                  >
                    {/* Timestamp */}
                    <span
                      style={{
                        color: '#484f58',
                        fontSize: 10,
                        minWidth: 65,
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {new Date(log.timestamp).toLocaleTimeString('en-US', {
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>

                    {/* Agent Icon */}
                    <span style={{ fontSize: 14 }}>{config.icon}</span>

                    {/* Agent Name */}
                    <span
                      style={{
                        color: config.color,
                        fontWeight: 600,
                        minWidth: 90,
                        fontSize: 11,
                      }}
                    >
                      {config.name}
                    </span>

                    {/* Message */}
                    <span
                      style={{
                        color:
                          log.level === 'error'
                            ? '#f85149'
                            : log.level === 'warning'
                            ? '#d29922'
                            : log.level === 'success'
                            ? '#3fb950'
                            : '#c9d1d9',
                        flex: 1,
                      }}
                    >
                      {log.message}
                    </span>

                    {/* Status Icon */}
                    {log.level === 'error' && <AlertTriangle size={14} style={{ color: '#f85149' }} />}
                    {log.level === 'success' && <CheckCircle size={14} style={{ color: '#3fb950' }} />}
                  </motion.div>
                );
              })
            )}

            {/* Cursor */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
              <span style={{ color: '#3fb950' }}>❯</span>
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.8, repeat: Infinity }}
                style={{
                  width: 8,
                  height: 16,
                  background: '#3fb950',
                  borderRadius: 2,
                }}
              />
            </div>
          </div>
        )}

        {/* Minimized view */}
        {isMinimized && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 16px',
              height: 'calc(100% - 56px)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {activeAgents.size > 0 ? (
                <>
                  <Zap size={14} style={{ color: '#3fb950' }} />
                  <span style={{ color: '#c9d1d9', fontSize: 11 }}>
                    {activeAgents.size} agent(s) active
                  </span>
                </>
              ) : (
                <span style={{ color: '#8b949e', fontSize: 11 }}>
                  {logs.length} events logged
                </span>
              )}
            </div>
            <button
              onClick={() => setIsMinimized(false)}
              style={{
                background: 'rgba(88, 166, 255, 0.1)',
                border: 'none',
                color: '#58a6ff',
                cursor: 'pointer',
                padding: '4px 12px',
                borderRadius: 6,
                fontSize: 11,
              }}
            >
              Expand
            </button>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

// Add keyframes to document
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes borderGlow {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 1; }
    }
  `;
  document.head.appendChild(style);
}
