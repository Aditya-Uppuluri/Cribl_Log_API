from flask import Flask, request, jsonify, render_template_string
import requests
import os
import uuid
from datetime import datetime
import json
import gzip
import logging
import urllib.parse

app = Flask(__name__)
 
# Enhanced logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
 
# In-memory storage for analysis results (use Redis/DB in production)
analysis_results = {}

# CORRECT STREAMLIT URL - Update this with your actual URL
STREAMLIT_APP_URL = "https://criblchatbot-ksbwyaufrk8t2lt6dmhdgc.streamlit.app"
 
# HTML template for viewing results (keeping your existing template but with fixes)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cribl Log Analysis Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0fdfa; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(90deg, #0d9488, #14b8a6); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .result-card { background: white; border: 1px solid #a7f3d0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .status.success { background-color: #f0fdf4; border-left: 4px solid #22c55e; color: #16a34a; }
        .status.processing { background-color: #fef3c7; border-left: 4px solid #f59e0b; color: #92400e; }
        .status.error { background-color: #fef2f2; border-left: 4px solid #ef4444; color: #dc2626; }
        .log-preview { background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
        .analysis-result { background-color: #f9fafb; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #14b8a6; }
        .timestamp { color: #6b7280; font-size: 0.9em; }
        .refresh-btn { background-color: #14b8a6; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin: 10px 0; }
        .refresh-btn:hover { background-color: #0d9488; }
        .chatbot-link { display: inline-block; background-color: #059669; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; margin: 5px 0; }
        .chatbot-link:hover { background-color: #047857; }
        .debug-info { background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 15px; margin: 10px 0; font-size: 0.9em; }
        .url-test { background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 15px; margin: 10px 0; }
    </style>
    <script>
        function refreshPage() {
            location.reload();
        }
        
        function testUrl(url) {
            window.open(url, '_blank');
        }
        
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Cribl Log Analysis Dashboard</h1>
            <p>Real-time log analysis results from your Streamlit chatbot</p>
        </div>
        
        <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Results</button>
        
        <div class="debug-info">
            <strong>Debug Info:</strong><br>
            <strong>Streamlit App URL:</strong> <code>{{ streamlit_url }}</code><br>
            <strong>Webhook URL:</strong> <code>{{ webhook_url }}/log-to-chatbot</code><br>
            <strong>Dashboard URL:</strong> <code>{{ webhook_url }}/dashboard</code><br>
            <strong>Test URL:</strong> <code>{{ webhook_url }}/test</code><br>
            <strong>Total Results:</strong> {{ results|length }}
        </div>
        
        {% if results %}
            {% for result_id, result in results.items() %}
            <div class="result-card">
                <h3>Analysis {{ result_id }} - {{ result.timestamp }}</h3>
                
                <div class="status {{ result.status }}">
                    <strong>Status:</strong>
                    {% if result.status == 'success' %}
                        ✅ Analysis Complete - URL Generated
                    {% elif result.status == 'processing' %}
                        ⏳ Processing...
                    {% else %}
                        ❌ Error occurred
                    {% endif %}
                </div>
                
                <div class="log-preview">
                    <strong>Log Data Preview:</strong><br>
                    {{ result.log_preview }}
                </div>
                
                {% if result.debug_info %}
                <div class="debug-info">
                    <strong>Debug Info:</strong><br>
                    Content-Type: {{ result.debug_info.content_type }}<br>
                    Data Length: {{ result.debug_info.data_length }} characters<br>
                    Request Method: {{ result.debug_info.get('method', 'Unknown') }}<br>
                    URL Length: {{ result.chatbot_url|length if result.chatbot_url else 'N/A' }} characters
                </div>
                {% endif %}
                
                {% if result.chatbot_url %}
                <div class="url-test">
                    <button onclick="testUrl('{{ result.chatbot_url }}')" class="chatbot-link">
                        🔗 Open Analysis in Streamlit (New Window)
                    </button>
                    <br><small>Click to open in new window - this should trigger the analysis</small>
                </div>
                {% endif %}
                
                {% if result.error %}
                <div class="status error">
                    <strong>Error:</strong> {{ result.error }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <div class="result-card">
                <h3>No Analysis Results Yet</h3>
                <p>Waiting for log analysis requests from Cribl Stream...</p>
                <p><strong>Webhook URL:</strong> <code>{{ webhook_url }}/log-to-chatbot</code></p>
                <div class="url-test">
                    <button onclick="testUrl('{{ webhook_url }}/test')" class="chatbot-link">
                        🧪 Test Webhook Endpoint
                    </button>
                </div>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""
 
@app.route("/", methods=["GET"])
def home():
    return "✅ Cribl Log Relay API is running", 200
 
@app.route("/test", methods=["GET", "POST"])
def test_endpoint():
    """Test endpoint to verify webhook functionality"""
    if request.method == "GET":
        return jsonify({
            "message": "Test endpoint is working",
            "webhook_url": f"{request.url_root}log-to-chatbot",
            "dashboard_url": f"{request.url_root}dashboard",
            "streamlit_url": STREAMLIT_APP_URL
        })
    else:
        # Handle POST for testing with sample data
        return receive_log_with_test_data()

def receive_log_with_test_data():
    """Handle test POST request with sample data"""
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "user": "test_user",
        "action": "login_attempt",
        "source_ip": "192.168.1.100",
        "status": "success",
        "test": True
    }
    
    # Override request data for testing
    import json
    request._cached_data = json.dumps(test_data).encode()
    request._cached_json = test_data
    
    return receive_log()
 
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Dashboard to view analysis results"""
    webhook_url = request.url_root.rstrip('/')
    return render_template_string(HTML_TEMPLATE,
                                results=analysis_results,
                                webhook_url=webhook_url,
                                streamlit_url=STREAMLIT_APP_URL)
 

# Replace your receive_log() function with this enhanced version:
@app.route("/log-to-chatbot", methods=["GET", "POST", "PUT"])
def receive_log():
    """Enhanced webhook endpoint with GZIP decompression support"""
    
    # Log all incoming requests
    logger.info(f"📥 Received {request.method} request to /log-to-chatbot")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Content-Encoding: {request.headers.get('Content-Encoding', 'None')}")
    
    if request.method == "GET":
        return jsonify({
            "message": "Webhook endpoint is active",
            "expected_method": "POST or PUT",
            "content_type": "text/plain or application/json",
            "dashboard_url": f"{request.url_root}dashboard",
            "streamlit_url": STREAMLIT_APP_URL
        })
    
    # Handle different content types and encodings from Cribl
    try:
        # Get raw data first
        raw_data = request.get_data()
        
        # Check if data is GZIP compressed
        if request.headers.get('Content-Encoding') == 'gzip':
            logger.info("🗜️ Decompressing GZIP data...")
            try:
                # Decompress GZIP data
                decompressed_data = gzip.decompress(raw_data)
                data_text = decompressed_data.decode('utf-8')
                logger.info(f"✅ Successfully decompressed {len(raw_data)} bytes to {len(data_text)} characters")
            except Exception as decomp_error:
                logger.error(f"❌ GZIP decompression failed: {str(decomp_error)}")
                return jsonify({
                    "status": "error",
                    "message": f"GZIP decompression failed: {str(decomp_error)}",
                    "debug": {
                        "content_encoding": request.headers.get('Content-Encoding'),
                        "content_length": len(raw_data),
                        "raw_data_preview": str(raw_data[:50])
                    }
                }), 400
        else:
            # Not compressed, use as-is
            data_text = raw_data.decode('utf-8')
        
        # Now parse the decompressed/raw data
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON payload
            try:
                data = json.loads(data_text)
                if isinstance(data, list):
                    # Multiple log entries
                    logs = '\n'.join([json.dumps(entry, indent=2) if isinstance(entry, dict) else str(entry) for entry in data])
                elif isinstance(data, dict):
                    # Single log entry
                    logs = json.dumps(data, indent=2)
                else:
                    logs = str(data)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as text
                logs = data_text
        elif request.content_type and 'ndjson' in request.content_type:
            # Handle NDJSON (newline-delimited JSON)
            logger.info("📄 Processing NDJSON data...")
            logs_list = []
            for line in data_text.strip().split('\n'):
                if line.strip():
                    try:
                        parsed_line = json.loads(line)
                        logs_list.append(json.dumps(parsed_line, indent=2))
                    except json.JSONDecodeError:
                        logs_list.append(line)
            logs = '\n'.join(logs_list)
        else:
            # Handle plain text or other formats
            logs = data_text
            
        if not logs or logs.strip() == "":
            logger.warning("⚠️ Received empty log data after processing")
            return jsonify({
                "status": "error",
                "message": "No log data received after processing",
                "debug": {
                    "content_type": request.content_type,
                    "content_encoding": request.headers.get('Content-Encoding'),
                    "raw_data_length": len(raw_data),
                    "processed_data_length": len(data_text) if 'data_text' in locals() else 0
                }
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error parsing request data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error parsing request data: {str(e)}",
            "debug": {
                "content_type": request.content_type,
                "content_encoding": request.headers.get('Content-Encoding'),
                "data_length": len(request.get_data()),
                "headers": dict(request.headers)
            }
        }), 400
    
    analysis_id = f"cribl_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"📥 Processing log analysis request #{analysis_id}")
    logger.info(f"Processed log preview: {logs[:200]}...")
 
    # Store initial result with debug info
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": logs[:500],  # Show more preview
        "status": "processing",
        "chatbot_url": None,
        "error": None,
        "debug_info": {
            "content_type": request.content_type,
            "content_encoding": request.headers.get('Content-Encoding'),
            "data_length": len(logs),
            "method": request.method,
            "headers": dict(request.headers)
        }
    }
 
    # Enhanced prompt for better analysis
    prompt = f"""Analysis ID: {analysis_id}

CRIBL STREAM LOG ANALYSIS REQUEST

Timestamp: {timestamp}
Source: Cribl Stream Webhook

Log Data for Security Analysis:
{logs}

Please perform comprehensive predictive and prescriptive security analysis including:

🚨 THREAT LEVEL: [Assess as LOW/MEDIUM/HIGH/CRITICAL]
📊 RISK SCORE: [Rate 1-10]
🔍 KEY FINDINGS: [Summary of suspicious activities]
⚡ IMMEDIATE ACTIONS: [Critical next steps]
🛡️ RECOMMENDATIONS: [Long-term improvements]

Focus on insider threats, anomalous behavior, and security incidents."""
 
    try:
        # URL encode the prompt properly
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        chatbot_url = f"{STREAMLIT_APP_URL}?prompt={encoded_prompt}"
        
        # Update with chatbot URL
        analysis_results[analysis_id]["chatbot_url"] = chatbot_url
        analysis_results[analysis_id]["status"] = "success"
        
        logger.info(f"✅ Analysis #{analysis_id} URL generated successfully")
        logger.info(f"Chatbot URL length: {len(chatbot_url)} characters")
        logger.info(f"Readable log preview: {logs[:100]}...")
            
        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "message": f"Log analysis #{analysis_id} initiated successfully",
            "chatbot_url": chatbot_url,
            "dashboard_url": f"{request.url_root}dashboard",
            "streamlit_base_url": STREAMLIT_APP_URL,
            "log_preview": logs[:200],
            "instructions": "Click the chatbot URL to view the analysis in Streamlit"
        }), 200
        
    except Exception as e:
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["error"] = str(e)
        logger.error(f"❌ Error in analysis #{analysis_id}: {str(e)}")
        
        return jsonify({
            "status": "error",
            "analysis_id": analysis_id,
            "message": str(e),
            "dashboard_url": f"{request.url_root}dashboard"
        }), 500

# Test endpoint to manually trigger analysis
@app.route("/test-analysis", methods=["POST"])
def test_analysis():
    """Manually test the analysis flow"""
    test_logs = """
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "user": "john.doe",
        "action": "file_access",
        "file_path": "/sensitive/financial_data.xlsx",
        "source_ip": "192.168.1.100",
        "department": "IT",
        "access_time": "02:30:00",
        "status": "success",
        "unusual_activity": "accessing sensitive files outside business hours"
    }
    """
    
    # Simulate the webhook request
    analysis_id = f"test_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": test_logs[:500],
        "status": "processing",
        "chatbot_url": None,
        "error": None,
        "debug_info": {
            "content_type": "application/json",
            "data_length": len(test_logs),
            "method": "POST (Test)",
            "headers": {"test": "true"}
        }
    }
    
    prompt = f"""Analysis ID: {analysis_id}

TEST LOG ANALYSIS REQUEST

Timestamp: {timestamp}
Source: Manual Test

Log Data for Security Analysis:
{test_logs}

Please perform comprehensive security analysis of this test data."""
    
    try:
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        chatbot_url = f"{STREAMLIT_APP_URL}?prompt={encoded_prompt}"
        
        analysis_results[analysis_id]["chatbot_url"] = chatbot_url
        analysis_results[analysis_id]["status"] = "success"
        
        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "message": "Test analysis created successfully",
            "chatbot_url": chatbot_url,
            "dashboard_url": f"{request.url_root}dashboard"
        }), 200
        
    except Exception as e:
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["error"] = str(e)
        
        return jsonify({
            "status": "error",
            "analysis_id": analysis_id,
            "message": str(e)
        }), 500
 
@app.route("/results/<analysis_id>", methods=["GET"])
def get_result(analysis_id):
    """Get specific analysis result"""
    if analysis_id in analysis_results:
        return jsonify(analysis_results[analysis_id])
    else:
        return jsonify({"error": "Analysis not found"}), 404
 
@app.route("/results", methods=["GET"])
def get_all_results():
    """Get all analysis results"""
    return jsonify(analysis_results)
 
@app.route("/clear-results", methods=["POST"])
def clear_results():
    """Clear all stored results"""
    global analysis_results
    analysis_results = {}
    return jsonify({"message": "All results cleared"})

# Add debugging route
@app.route("/debug", methods=["GET"])
def debug_info():
    """Debug information endpoint"""
    return jsonify({
        "streamlit_url": STREAMLIT_APP_URL,
        "total_results": len(analysis_results),
        "recent_results": list(analysis_results.keys())[-5:] if analysis_results else [],
        "environment": {
            "port": os.environ.get("PORT", 5000),
            "debug": app.debug
        }
    })
 
# Add error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/dashboard",
            "/log-to-chatbot",
            "/test",
            "/test-analysis",
            "/results",
            "/debug"
        ]
    }), 404
 
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500
 
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
