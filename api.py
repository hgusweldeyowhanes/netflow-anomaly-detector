"""
Flask API for Network Anomaly Detector
Wraps the existing Python pipeline for use with Netlify
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import json
import traceback
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'netflow-anomaly-detector'))

from src.feature_extraction import load_flows, build_features, FEATURE_COLUMNS
from src.model import AnomalyModel
from src.alerting import build_alerts, write_alerts
from src.data_generator import generate_dataset
from src.beacon_detector import detect_beacons, beacon_alerts

import yaml

app = Flask(__name__)
CORS(app)

# Load config
def load_config(path: str = 'netflow-anomaly-detector/config.yaml') -> dict:
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except:
        return {
            'data': {'input_path': 'netflow-anomaly-detector/data/flows.csv', 'window_minutes': 5},
            'model': {'type': 'isolation_forest', 'contamination': 0.02, 'n_estimators': 200},
            'scoring': {'alert_risk_threshold': 70},
            'beacon_detector': {'min_connections': 8, 'cov_threshold': 0.3},
            'alerting': {'output_path': 'netflow-anomaly-detector/output/alerts.json', 'top_n_features': 5}
        }

CONFIG = load_config()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get current alerts"""
    try:
        cfg = CONFIG
        
        # Ensure data directory exists and generate demo if needed
        input_path = cfg['data']['input_path']
        os.makedirs(os.path.dirname(input_path), exist_ok=True)
        
        if not os.path.exists(input_path):
            print(f"Generating demo data at {input_path}")
            generate_dataset(output_path=input_path)
        
        # Run analysis pipeline
        flows_df = load_flows(input_path)
        
        if flows_df.empty:
            return jsonify({
                'alerts': [],
                'stats': {
                    'total_flows': 0,
                    'unique_sources': 0,
                    'anomalies_detected': 0,
                    'beacons_detected': 0,
                    'timestamp': datetime.now().isoformat()
                }
            }), 200
        
        # Build features and score
        features_df = build_features(flows_df, window_minutes=cfg['data']['window_minutes'])
        
        model = AnomalyModel(
            model_type=cfg['model']['type'],
            contamination=cfg['model']['contamination'],
            n_estimators=cfg['model']['n_estimators'],
            random_state=cfg['model']['random_state']
        )
        
        scores_df = model.score(features_df)
        
        # Build alerts
        alerts = build_alerts(
            scores_df,
            features_df,
            alert_threshold=cfg['scoring']['alert_risk_threshold'],
            top_n_features=cfg['alerting']['top_n_features']
        )
        
        # Detect beacons
        beacon_results = detect_beacons(
            flows_df,
            min_connections=cfg['beacon_detector']['min_connections'],
            cov_threshold=cfg['beacon_detector']['cov_threshold']
        )
        
        beacon_alert_list = beacon_alerts(beacon_results)
        
        # Combine alerts
        all_alerts = alerts + beacon_alert_list
        
        # Calculate stats
        stats = {
            'total_flows': len(flows_df),
            'unique_sources': flows_df['source_ip'].nunique() if 'source_ip' in flows_df.columns else 0,
            'anomalies_detected': len([a for a in alerts if a.get('alert_type') == 'anomaly']),
            'beacons_detected': len(beacon_alert_list),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'alerts': all_alerts,
            'stats': stats
        }), 200
    
    except Exception as e:
        print(f"Error in get_alerts: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'alerts': [], 'stats': {}}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_flows():
    """Analyze uploaded CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be CSV format'}), 400
        
        cfg = CONFIG
        
        # Save uploaded file
        upload_path = cfg['data']['input_path']
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        
        # Run analysis
        flows_df = load_flows(upload_path)
        
        if flows_df.empty:
            return jsonify({
                'success': True,
                'message': 'File uploaded but contains no data',
                'alerts': [],
                'stats': {}
            }), 200
        
        # Run full pipeline
        features_df = build_features(flows_df, window_minutes=cfg['data']['window_minutes'])
        
        model = AnomalyModel(
            model_type=cfg['model']['type'],
            contamination=cfg['model']['contamination'],
            n_estimators=cfg['model']['n_estimators'],
            random_state=cfg['model']['random_state']
        )
        
        scores_df = model.score(features_df)
        alerts = build_alerts(
            scores_df,
            features_df,
            alert_threshold=cfg['scoring']['alert_risk_threshold'],
            top_n_features=cfg['alerting']['top_n_features']
        )
        
        # Save alerts
        os.makedirs(os.path.dirname(cfg['alerting']['output_path']), exist_ok=True)
        write_alerts(alerts, cfg['alerting']['output_path'])
        
        stats = {
            'total_flows': len(flows_df),
            'unique_sources': flows_df['source_ip'].nunique() if 'source_ip' in flows_df.columns else 0,
            'alerts_generated': len(alerts)
        }
        
        return jsonify({
            'success': True,
            'message': 'Analysis completed successfully',
            'alerts': alerts,
            'stats': stats
        }), 200
    
    except Exception as e:
        print(f"Error in analyze_flows: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(CONFIG), 200

@app.route('/api/download-alerts', methods=['GET'])
def download_alerts():
    """Download alerts as JSON"""
    try:
        alerts_path = CONFIG['alerting']['output_path']
        
        if os.path.exists(alerts_path):
            return send_file(alerts_path, as_attachment=True, download_name='alerts.json')
        else:
            return jsonify({'error': 'No alerts generated yet'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Network Anomaly Detector API")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/alerts - Get current alerts")
    print("  POST /api/analyze - Analyze CSV file")
    print("  GET  /api/config - Get configuration")
    print("  GET  /api/download-alerts - Download alerts")
    
    app.run(debug=False, port=8000, host='0.0.0.0')
