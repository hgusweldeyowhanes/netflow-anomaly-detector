import React from 'react';
import './FlowVisualization.css';

function FlowVisualization() {
  return (
    <div className="panel flow-viz-panel">
      <h2 className="panel-title">🌐 Network Flow Overview</h2>
      <div className="flow-viz">
        <svg viewBox="0 0 400 300" preserveAspectRatio="xMidYMid meet">
          {/* Background */}
          <rect width="400" height="300" fill="#f9f9f9" />
          
          {/* Grid lines */}
          <g stroke="#e0e0e0" strokeWidth="1" opacity="0.5">
            <line x1="0" y1="50" x2="400" y2="50" />
            <line x1="0" y1="100" x2="400" y2="100" />
            <line x1="0" y1="150" x2="400" y2="150" />
            <line x1="0" y1="200" x2="400" y2="200" />
            <line x1="0" y1="250" x2="400" y2="250" />
          </g>

          {/* Source nodes */}
          <g id="sources">
            <circle cx="50" cy="80" r="20" fill="#667eea" opacity="0.8" />
            <text x="50" y="90" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S1</text>
            
            <circle cx="50" cy="150" r="20" fill="#667eea" opacity="0.8" />
            <text x="50" y="160" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S2</text>
            
            <circle cx="50" cy="220" r="20" fill="#667eea" opacity="0.8" />
            <text x="50" y="230" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">S3</text>
          </g>

          {/* Destination nodes */}
          <g id="destinations">
            <circle cx="350" cy="80" r="20" fill="#4CAF50" opacity="0.8" />
            <text x="350" y="90" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">D1</text>
            
            <circle cx="350" cy="150" r="20" fill="#4CAF50" opacity="0.8" />
            <text x="350" y="160" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">D2</text>
            
            <circle cx="350" cy="220" r="20" fill="#4CAF50" opacity="0.8" />
            <text x="350" y="230" textAnchor="middle" fill="white" fontSize="12" fontWeight="bold">D3</text>
          </g>

          {/* Normal flows */}
          <g stroke="#667eea" strokeWidth="2" opacity="0.5" fill="none" markerEnd="url(#arrowblue)">
            <path d="M 70 80 Q 200 50 330 80" />
            <path d="M 70 150 Q 200 120 330 150" />
            <path d="M 70 220 Q 200 250 330 220" />
          </g>

          {/* Anomalous flows */}
          <g stroke="#ff9800" strokeWidth="3" opacity="0.8" fill="none" markerEnd="url(#arroworange)">
            <path d="M 70 80 Q 150 180 330 220" strokeDasharray="5,5" />
            <path d="M 70 220 Q 220 100 330 80" strokeDasharray="5,5" />
          </g>

          {/* Arrow markers */}
          <defs>
            <marker id="arrowblue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#667eea" />
            </marker>
            <marker id="arroworange" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#ff9800" />
            </marker>
          </defs>

          {/* Legend */}
          <text x="20" y="280" fontSize="12" fill="#666">● Normal flows</text>
          <circle cx="12" cy="275" r="3" fill="#667eea" />
          
          <text x="180" y="280" fontSize="12" fill="#666">⚠ Anomalous flows</text>
          <circle cx="172" cy="275" r="3" fill="#ff9800" />
        </svg>
        <p className="viz-description">
          Visualization of network flows. Blue lines represent normal traffic, orange dashed lines indicate anomalous patterns.
        </p>
      </div>
    </div>
  );
}

export default FlowVisualization;
