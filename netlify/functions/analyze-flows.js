// Netlify Function: Analyze uploaded flow data
// Path: netlify/functions/analyze-flows.js

const axios = require('axios');
const FormData = require('form-data');

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    // Parse form data from event
    if (!event.body) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'No file provided' })
      };
    }

    // For Netlify functions, multipart form data handling requires additional libraries
    // This is a simplified version - in production, use busboy or similar
    console.log('File received for analysis');

    // Forward to Python API
    const formData = new FormData();
    formData.append('file', event.body);

    const response = await axios.post(
      `${PYTHON_API_URL}/api/analyze`,
      formData,
      {
        headers: formData.getHeaders(),
        timeout: 30000
      }
    );

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: 'Analysis completed',
        data: response.data
      })
    };
  } catch (error) {
    console.error('Error analyzing flows:', error.message);

    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Failed to analyze flows',
        details: error.message
      })
    };
  }
};
