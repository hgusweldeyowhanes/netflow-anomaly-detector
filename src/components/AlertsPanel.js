import React from 'react';
import './AlertsPanel.css';

function AlertsPanel({ alerts }) {
  const getRiskColor = (risk) => {
    if (risk >= 85) return '#ff4444';
    if (risk >= 70) return '#ff9800';
    if (risk >= 50) return '#ffc107';
    return '#4CAF50';
  };

  const getRiskLabel = (risk) => {
    if (risk >= 85) return 'CRITICAL';
    if (risk >= 70) return 'HIGH';
    if (risk >= 50) return 'MEDIUM';
    return 'LOW';
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="panel">
        <h2 className="panel-title">🚨 Alerts</h2>
        <div className="empty-state">
          <p>No alerts detected</p>
          <p className="text-muted">System is operating normally</p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel alerts-panel">
      <h2 className="panel-title">🚨 Alerts ({alerts.length})</h2>
      <div className="alerts-list">
        {alerts.map((alert, idx) => (
          <div key={idx} className="alert-card" style={{ borderLeftColor: getRiskColor(alert.risk_score) }}>
            <div className="alert-header">
              <span className="alert-ip">{alert.source_ip}</span>
              <span className="alert-risk" style={{ backgroundColor: getRiskColor(alert.risk_score) }}>
                {getRiskLabel(alert.risk_score)} ({Math.round(alert.risk_score)})
              </span>
            </div>
            
            <div className="alert-details">
              <p><strong>Type:</strong> {alert.alert_type}</p>
              <p><strong>Time:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
              {alert.anomaly_score && <p><strong>Anomaly Score:</strong> {alert.anomaly_score.toFixed(3)}</p>}
            </div>

            {alert.top_features && alert.top_features.length > 0 && (
              <div className="alert-features">
                <strong>Contributing Features:</strong>
                <ul>
                  {alert.top_features.map((feat, i) => (
                    <li key={i}>{feat}</li>
                  ))}
                </ul>
              </div>
            )}

            {alert.beacon_stats && (
              <div className="alert-beacon">
                <strong>Beacon Activity:</strong>
                <p>Regular connections detected (COV: {alert.beacon_stats.cov.toFixed(3)})</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AlertsPanel;
