import React, { useState, useEffect } from 'react';
import './App.css';
import AlertsPanel from './components/AlertsPanel';
import StatsPanel from './components/StatsPanel';
import FlowVisualization from './components/FlowVisualization';
import DataUploader from './components/DataUploader';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch alerts from Netlify function
  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/.netlify/functions/get-alerts');
      const data = await response.json();
      if (response.ok) {
        setAlerts(data.alerts || []);
        setStats(data.stats || {});
      } else {
        setError(data.error || 'Failed to fetch alerts');
      }
    } catch (err) {
      setError('Error connecting to server: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Load alerts on mount
  useEffect(() => {
    fetchAlerts();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔍 Network Anomaly Detection</h1>
        <p>Real-time monitoring and alerting for suspicious network traffic</p>
      </header>

      <main className="app-main">
        <div className="controls">
          <DataUploader onUploadSuccess={fetchAlerts} />
          <button className="refresh-btn" onClick={fetchAlerts} disabled={loading}>
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="dashboard">
          <div className="left-panel">
            <StatsPanel stats={stats} />
            <FlowVisualization />
          </div>

          <div className="right-panel">
            <AlertsPanel alerts={alerts} />
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by Isolation Forest • Deployed on Netlify</p>
      </footer>
    </div>
  );
}

export default App;
