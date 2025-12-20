import { useState, useEffect } from 'react';
import { FileText, Image, X } from 'lucide-react';
import { motion } from 'framer-motion';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
}

export function FilePreview({ file, onRemove }: FilePreviewProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const isImage = file.type.startsWith('image/');
  const isPDF = file.type === 'application/pdf';

  useEffect(() => {
    if (isImage) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [file, isImage]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: 12,
        background: 'var(--bg-secondary)',
        borderRadius: 12,
        border: '1px solid var(--gray-200)',
        position: 'relative',
      }}
    >
      {/* Preview Thumbnail */}
      <div
        style={{
          width: 60,
          height: 60,
          borderRadius: 8,
          overflow: 'hidden',
          background: 'var(--gray-100)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isImage && preview ? (
          <img
            src={preview}
            alt={file.name}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />
        ) : isPDF ? (
          <FileText size={28} style={{ color: '#EA4335' }} />
        ) : (
          <Image size={28} style={{ color: 'var(--gray-400)' }} />
        )}
      </div>

      {/* File Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p
          style={{
            fontWeight: 500,
            fontSize: 14,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {file.name}
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          {formatFileSize(file.size)} • {file.type.split('/')[1]?.toUpperCase() || 'File'}
        </p>
      </div>

      {/* Remove Button */}
      <button
        onClick={onRemove}
        style={{
          position: 'absolute',
          top: -8,
          right: -8,
          width: 24,
          height: 24,
          borderRadius: '50%',
          border: 'none',
          background: 'var(--error)',
          color: 'white',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <X size={14} />
      </button>
    </motion.div>
  );
}
