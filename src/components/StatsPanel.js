import React from 'react';
import './StatsPanel.css';

function StatsPanel({ stats }) {
  if (!stats) {
    return (
      <div className="panel stats-panel">
        <h2 className="panel-title">📊 Statistics</h2>
        <div className="empty-state">Loading...</div>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Total Flows',
      value: stats.total_flows || 0,
      icon: '📦',
      color: '#667eea'
    },
    {
      label: 'Unique Sources',
      value: stats.unique_sources || 0,
      icon: '🔗',
      color: '#4CAF50'
    },
    {
      label: 'Anomalies',
      value: stats.anomalies_detected || 0,
      icon: '⚠️',
      color: '#ff9800'
    },
    {
      label: 'Beacons',
      value: stats.beacons_detected || 0,
      icon: '📡',
      color: '#ff4444'
    }
  ];

  return (
    <div className="panel stats-panel">
      <h2 className="panel-title">📊 Statistics</h2>
      <div className="stats-grid">
        {statCards.map((stat, idx) => (
          <div key={idx} className="stat-card" style={{ borderTopColor: stat.color }}>
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <p className="stat-label">{stat.label}</p>
              <p className="stat-value" style={{ color: stat.color }}>{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {stats.timestamp && (
        <div className="stats-footer">
          <small>Last updated: {new Date(stats.timestamp).toLocaleTimeString()}</small>
        </div>
      )}
    </div>
  );
}

export default StatsPanel;
