// Netlify Function: Get alerts from Python backend
// Path: netlify/functions/get-alerts.js

const axios = require('axios');

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };

  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers };
  }

  try {
    console.log(`Fetching alerts from ${PYTHON_API_URL}/api/alerts`);
    
    // Call your Python backend
    const response = await axios.get(`${PYTHON_API_URL}/api/alerts`, {
      timeout: 5000
    });

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(response.data)
    };
  } catch (error) {
    console.error('Error fetching alerts:', error.message);

    // Return mock data if Python API is not available
    const mockAlerts = {
      alerts: [
        {
          source_ip: '192.168.1.100',
          timestamp: new Date().toISOString(),
          alert_type: 'anomaly',
          risk_score: 85,
          anomaly_score: -2.5,
          top_features: ['high_packet_count', 'unusual_protocol', 'rare_port'],
          beacon_stats: null
        },
        {
          source_ip: '10.0.0.50',
          timestamp: new Date().toISOString(),
          alert_type: 'beacon',
          risk_score: 72,
          anomaly_score: null,
          top_features: [],
          beacon_stats: { cov: 0.25 }
        }
      ],
      stats: {
        total_flows: 1245,
        unique_sources: 23,
        anomalies_detected: 5,
        beacons_detected: 2,
        timestamp: new Date().toISOString()
      }
    };

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(mockAlerts)
    };
  }
};
