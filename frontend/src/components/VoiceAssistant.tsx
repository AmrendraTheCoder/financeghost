import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, X, Loader2 } from 'lucide-react';
import { api } from '../api';

interface VoiceAssistantProps {
  isOpen: boolean;
  onClose: () => void;
}

interface VoiceResponse {
  intent: string;
  response: string;
  data?: any;
  suggestions?: string[];
}

export function VoiceAssistant({ isOpen, onClose }: VoiceAssistantProps) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState<VoiceResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check for browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event: any) => {
        const current = event.resultIndex;
        const result = event.results[current];
        const text = result[0].transcript;
        setTranscript(text);

        if (result.isFinal) {
          processVoiceCommand(text);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setError(`Speech recognition error: ${event.error}`);
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const startListening = () => {
    if (recognitionRef.current) {
      setTranscript('');
      setResponse(null);
      setError(null);
      setIsListening(true);
      recognitionRef.current.start();
    } else {
      setError('Speech recognition not supported in this browser');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  const processVoiceCommand = async (text: string) => {
    setIsProcessing(true);
    try {
      const result = await api.post('/voice/command', { transcript: text });
      setResponse(result.data);

      // Text-to-speech response
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(result.data.response);
        utterance.rate = 1;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
      }
    } catch (err) {
      setError('Failed to process command');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setTranscript(suggestion);
    processVoiceCommand(suggestion);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'var(--bg-primary)',
            borderRadius: 24,
            padding: 32,
            width: '90%',
            maxWidth: 500,
            textAlign: 'center',
          }}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              top: 16,
              right: 16,
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
            }}
          >
            <X size={24} />
          </button>

          {/* Title */}
          <h2 style={{ marginBottom: 8, fontSize: '1.5rem' }}>
            🎙️ Hey Ghost
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
            Ask me about your finances
          </p>

          {/* Microphone Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={isListening ? stopListening : startListening}
            disabled={isProcessing}
            style={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              border: 'none',
              background: isListening
                ? 'linear-gradient(135deg, #EA4335, #FBBC05)'
                : 'linear-gradient(135deg, #4285F4, #34A853)',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 24px',
              boxShadow: isListening
                ? '0 0 0 8px rgba(234, 67, 53, 0.2)'
                : '0 4px 20px rgba(66, 133, 244, 0.3)',
              transition: 'all 0.3s ease',
            }}
          >
            {isProcessing ? (
              <Loader2 size={48} className="animate-spin" />
            ) : isListening ? (
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
              >
                <MicOff size={48} />
              </motion.div>
            ) : (
              <Mic size={48} />
            )}
          </motion.button>

          {/* Status */}
          <p
            style={{
              color: isListening ? 'var(--error)' : 'var(--text-secondary)',
              marginBottom: 16,
              minHeight: 24,
            }}
          >
            {isListening
              ? 'Listening...'
              : isProcessing
              ? 'Processing...'
              : 'Tap to speak'}
          </p>

          {/* Transcript */}
          {transcript && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                background: 'var(--bg-secondary)',
                padding: 16,
                borderRadius: 12,
                marginBottom: 16,
              }}
            >
              <p style={{ color: 'var(--text-tertiary)', fontSize: 12, marginBottom: 4 }}>
                You said:
              </p>
              <p style={{ fontWeight: 500 }}>"{transcript}"</p>
            </motion.div>
          )}

          {/* Response */}
          {response && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                background: 'var(--primary-light)',
                padding: 16,
                borderRadius: 12,
                marginBottom: 16,
                textAlign: 'left',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Volume2 size={16} style={{ color: 'var(--primary)' }} />
                <span style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 500 }}>
                  Ghost says:
                </span>
              </div>
              <p style={{ color: 'var(--text-primary)' }}>{response.response}</p>
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <div
              style={{
                background: '#fce8e6',
                color: 'var(--error)',
                padding: 12,
                borderRadius: 8,
                marginBottom: 16,
              }}
            >
              {error}
            </div>
          )}

          {/* Suggestions */}
          <div style={{ marginTop: 16 }}>
            <p style={{ color: 'var(--text-tertiary)', fontSize: 12, marginBottom: 8 }}>
              Try saying:
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
              {(response?.suggestions || [
                'How much did we spend?',
                'Show invoices needing review',
                "What's our cash forecast?",
              ]).map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(suggestion)}
                  style={{
                    padding: '8px 16px',
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--gray-200)',
                    borderRadius: 20,
                    fontSize: 12,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
