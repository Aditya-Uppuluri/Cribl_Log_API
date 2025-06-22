from flask import Flask, request, jsonify, render_template_string
import requests
import os
import uuid
from datetime import datetime
import json
import gzip
import logging
import urllib.parse
from collections import deque 

app = Flask(__name__)
# Global buffer to store the last 100 log entries
log_buffer = deque(maxlen=100) # <-- ADD THIS LINE

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
    """
    Enhanced webhook that buffers the last 100 logs and sends them for analysis.
    """
    logger.info(f"📥 Received {request.method} request to /log-to-chatbot")
    if request.method == "GET":
        return jsonify({ "message": "Webhook endpoint is active. POST log data here." })

    # --- [Existing data parsing logic] ---
    try:
        raw_data = request.get_data()
        if request.headers.get('Content-Encoding') == 'gzip':
            logger.info("🗜️ Decompressing GZIP data...")
            decompressed_data = gzip.decompress(raw_data)
            data_text = decompressed_data.decode('utf-8')
        else:
            data_text = raw_data.decode('utf-8')
    except Exception as e:
        logger.error(f"❌ Error parsing request data: {str(e)}")
        return jsonify({ "status": "error", "message": f"Error parsing request data: {str(e)}" }), 400
    
    # --- [START OF NEW LOGIC] ---

    # 1. Add new log entries to the global buffer
    if data_text and data_text.strip():
        # Split by newline to handle multiple log lines in a single payload
        new_entries = data_text.strip().split('\n')
        log_buffer.extend(new_entries)
        logger.info(f"📝 Added {len(new_entries)} new entries. Buffer size is now {len(log_buffer)}.")
    else:
        logger.warning("⚠️ Received empty log data. No entries added to buffer.")
        # Acknowledge the request without creating an analysis task
        return jsonify({"status": "acknowledged", "message": "Request contained empty log data."}), 200

    # 2. The 'logs' for analysis is now the consolidated content of the entire buffer
    logs = "\n".join(log_buffer)

    # --- [END OF NEW LOGIC] ---

    analysis_id = f"cribl_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"⚙️ Processing analysis request #{analysis_id} using the last {len(log_buffer)} log entries.")
 
    # Store initial result with debug info reflecting the buffer state
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": f"--- CONTEXT: LAST {len(log_buffer)} LOGS ---\n{logs[:500]}",
        "status": "processing",
        "chatbot_url": None,
        "error": None,
        "debug_info": {
            "content_type": request.content_type,
            "incoming_data_length": len(data_text),
            "buffer_size": len(log_buffer),
            "method": request.method,
        }
    }
 
    # Enhanced prompt that uses the entire log buffer
    prompt = f"""Analysis ID: {analysis_id}

CRIBL STREAM LOG ANALYSIS REQUEST

Timestamp: {timestamp}
Source: Cribl Stream Webhook

Here is the context of the last {len(log_buffer)} log entries for security analysis:
--- LOGS START ---
{logs}
--- LOGS END ---

Please perform comprehensive predictive and prescriptive security analysis on the *entire set* of logs provided above. Focus on identifying trends, insider threats, anomalous behavior, and potential security incidents within this collection of logs. Provide the analysis in the requested structured format:

🚨 THREAT LEVEL:
📊 RISK SCORE:
🔍 KEY FINDINGS:
⚡ IMMEDIATE ACTIONS:
🛡️ RECOMMENDATIONS:
"""
 
    try:
        # URL encode the consolidated prompt
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        chatbot_url = f"{STREAMLIT_APP_URL}?prompt={encoded_prompt}"
        
        analysis_results[analysis_id]["chatbot_url"] = chatbot_url
        analysis_results[analysis_id]["status"] = "success"
        
        logger.info(f"✅ Analysis #{analysis_id} URL generated successfully using {len(log_buffer)} logs.")
            
        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "message": f"Log analysis #{analysis_id} initiated using the last {len(log_buffer)} entries.",
            "chatbot_url": chatbot_url,
            "dashboard_url": f"{request.url_root}dashboard",
            "log_buffer_size": len(log_buffer)
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
    """Clear all stored results and the log buffer."""
    global analysis_results
    analysis_results = {}
    
    # NEW: Clear the log buffer as well
    log_buffer.clear()
    
    logger.info("🗑️ Cleared all analysis results and the log buffer.")
    return jsonify({"message": "All results and the log buffer have been cleared"})

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