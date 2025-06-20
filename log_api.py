from flask import Flask, request, jsonify, render_template_string
import requests
import os
import uuid
from datetime import datetime
import json
import logging
 
app = Flask(__name__)

# Enhanced logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
 
# In-memory storage for analysis results (use Redis/DB in production)
analysis_results = {}
 
# HTML template for viewing results (keeping your existing template)
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
        .log-preview { background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: monospace; white-space: pre-wrap; }
        .analysis-result { background-color: #f9fafb; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #14b8a6; }
        .timestamp { color: #6b7280; font-size: 0.9em; }
        .refresh-btn { background-color: #14b8a6; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin: 10px 0; }
        .refresh-btn:hover { background-color: #0d9488; }
        .chatbot-link { display: inline-block; background-color: #059669; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; margin: 5px 0; }
        .chatbot-link:hover { background-color: #047857; }
        .debug-info { background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 15px; margin: 10px 0; }
    </style>
    <script>
        function refreshPage() {
            location.reload();
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
            <strong>Expected Webhook URL:</strong> <code>{{ webhook_url }}/log-to-chatbot</code><br>
            <strong>Dashboard URL:</strong> <code>{{ webhook_url }}/dashboard</code><br>
            <strong>Test URL:</strong> <code>{{ webhook_url }}/test</code>
        </div>
        
        {% if results %}
            {% for result_id, result in results.items() %}
            <div class="result-card">
                <h3>Analysis #{{ loop.index }} - {{ result.timestamp }}</h3>
                
                <div class="status {{ result.status }}">
                    <strong>Status:</strong>
                    {% if result.status == 'success' %}
                        ✅ Analysis Complete
                    {% elif result.status == 'processing' %}
                        ⏳ Processing...
                    {% else %}
                        ❌ Error occurred
                    {% endif %}
                </div>
                
                <div class="log-preview">
                    <strong>Log Data Preview:</strong><br>
                    {{ result.log_preview }}...
                </div>
                
                {% if result.debug_info %}
                <div class="debug-info">
                    <strong>Debug Info:</strong><br>
                    Content-Type: {{ result.debug_info.content_type }}<br>
                    Data Length: {{ result.debug_info.data_length }}<br>
                    Headers: {{ result.debug_info.headers }}
                </div>
                {% endif %}
                
                {% if result.chatbot_url %}
                <a href="{{ result.chatbot_url }}" target="_blank" class="chatbot-link">
                    🔗 View Full Analysis in Chatbot
                </a>
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
            "dashboard_url": f"{request.url_root}dashboard"
        })
    else:
        # Handle POST for testing
        return receive_log()
 
@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Dashboard to view analysis results"""
    webhook_url = request.url_root.rstrip('/')
    return render_template_string(HTML_TEMPLATE,
                                results=analysis_results,
                                webhook_url=webhook_url)

@app.route("/log-to-chatbot", methods=["GET", "POST", "PUT"])
def receive_log():
    """Enhanced webhook endpoint with better debugging"""
    
    # Log all incoming requests
    logger.info(f"📥 Received {request.method} request to /log-to-chatbot")
    logger.info(f"Content-Type: {request.content_type}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == "GET":
        return jsonify({
            "message": "Webhook endpoint is active",
            "expected_method": "POST",
            "content_type": "text/plain or application/json",
            "dashboard_url": f"{request.url_root}dashboard"
        })
    
    # Handle different content types from Cribl
    try:
        if request.content_type and 'application/json' in request.content_type:
            # Handle JSON payload
            data = request.get_json()
            if isinstance(data, list):
                # Multiple log entries
                logs = '\n'.join([json.dumps(entry) if isinstance(entry, dict) else str(entry) for entry in data])
            elif isinstance(data, dict):
                # Single log entry
                logs = json.dumps(data, indent=2)
            else:
                logs = str(data)
        else:
            # Handle plain text or other formats
            logs = request.get_data(as_text=True)
            
        if not logs or logs.strip() == "":
            logger.warning("⚠️ Received empty log data")
            return jsonify({
                "status": "error",
                "message": "No log data received",
                "debug": {
                    "content_type": request.content_type,
                    "data_length": len(request.get_data()),
                    "raw_data": request.get_data(as_text=True)[:200]
                }
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error parsing request data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error parsing request data: {str(e)}",
            "debug": {
                "content_type": request.content_type,
                "data_length": len(request.get_data()),
                "headers": dict(request.headers)
            }
        }), 400
    
    analysis_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"📥 Processing log analysis request #{analysis_id}")
    logger.info(f"Log preview: {logs[:200]}...")
 
    # Store initial result with debug info
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": logs[:500],  # Show more preview
        "status": "processing",
        "chatbot_url": None,
        "error": None,
        "debug_info": {
            "content_type": request.content_type,
            "data_length": len(logs),
            "headers": dict(request.headers)
        }
    }
 
    # Enhanced prompt for better analysis
    prompt = f"""CRIBL STREAM LOG ANALYSIS REQUEST #{analysis_id}
 
Timestamp: {timestamp}
 
Log Data:
{logs}
 
Please perform comprehensive predictive and prescriptive analysis including:
1. Risk assessment and threat level
2. Behavioral pattern analysis  
3. Anomaly detection
4. Recommended immediate actions
5. Long-term security improvements
 
Analysis ID: {analysis_id}"""
 
    try:
        # URL encode the prompt properly - use quote_plus for better URL encoding
        encoded_prompt = requests.utils.quote_plus(prompt)
        chatbot_url = f"https://criblchatbot-ksbwyaufrk8t2lt6dmhdgc.streamlit.app/?prompt={encoded_prompt}"
        
        # Update with chatbot URL
        analysis_results[analysis_id]["chatbot_url"] = chatbot_url
        
        # Don't test the chatbot URL directly as Streamlit doesn't respond to GET requests in the traditional way
        # Instead, just mark as success since the URL is properly formatted
        chatbot_status = "url_generated"
        
        analysis_results[analysis_id]["status"] = "success"
        logger.info(f"✅ Analysis #{analysis_id} URL generated successfully")
        logger.info(f"Chatbot URL: {chatbot_url[:100]}...")
            
        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "message": f"Log analysis #{analysis_id} initiated",
            "chatbot_url": chatbot_url,
            "dashboard_url": f"{request.url_root}dashboard",
            "chatbot_status": chatbot_status,
            "log_preview": logs[:200]
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

# Add a catch-all route for debugging
@app.route("/log-to-chatbot/<path:extra>", methods=["GET", "POST", "PUT"])
def receive_log_with_extra(extra):
    """Catch requests with extra path components"""
    logger.warning(f"⚠️ Request to /log-to-chatbot/{extra} - redirecting to main endpoint")
    return receive_log()
 
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
            "/results"
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