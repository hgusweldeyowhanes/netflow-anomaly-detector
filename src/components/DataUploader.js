import React, { useRef } from 'react';
import './DataUploader.css';

function DataUploader({ onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = React.useState(false);
  const [message, setMessage] = React.useState('');

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/.netlify/functions/analyze-flows', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('✅ File uploaded and analyzed successfully!');
        setTimeout(() => {
          onUploadSuccess();
          setMessage('');
        }, 1000);
      } else {
        setMessage('❌ ' + (data.error || 'Upload failed'));
      }
    } catch (err) {
      setMessage('❌ Error: ' + err.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="uploader">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        disabled={uploading}
        className="file-input"
        aria-label="Upload CSV file"
      />
      <button
        className="upload-btn"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
      >
        {uploading ? '📤 Uploading...' : '📁 Upload Flow Data (CSV)'}
      </button>
      {message && <span className={`message ${message.includes('✅') ? 'success' : 'error'}`}>{message}</span>}
    </div>
  );
}

export default DataUploader;
