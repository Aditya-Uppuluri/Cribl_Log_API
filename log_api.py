from flask import Flask, request, jsonify, render_template_string
import requests
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)

# In-memory storage for analysis results (use Redis/DB in production)
analysis_results = {}

# HTML template for viewing results
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

@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Dashboard to view analysis results"""
    webhook_url = request.url_root.rstrip('/')
    return render_template_string(HTML_TEMPLATE, 
                                results=analysis_results, 
                                webhook_url=webhook_url)

@app.route("/log-to-chatbot", methods=["POST"])
def receive_log():
    logs = request.get_data(as_text=True)
    analysis_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"📥 Received log analysis request #{analysis_id}")
    print(f"Log preview: {logs[:200]}...")

    # Store initial result
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": logs[:200],
        "status": "processing",
        "chatbot_url": None,
        "error": None
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
        chatbot_url = "https://criblchatbot-hswvo3hhkgngsfvmwty9ql.streamlit.app/?prompt=" + requests.utils.quote(prompt)
        
        # Update with chatbot URL
        analysis_results[analysis_id]["chatbot_url"] = chatbot_url
        
        response = requests.get(chatbot_url, timeout=30)
        
        if response.status_code == 200:
            analysis_results[analysis_id]["status"] = "success"
            print(f"✅ Analysis #{analysis_id} sent to chatbot successfully")
        else:
            analysis_results[analysis_id]["status"] = "error"
            analysis_results[analysis_id]["error"] = f"Chatbot returned status {response.status_code}"
            
        return jsonify({
            "status": "success",
            "analysis_id": analysis_id,
            "message": f"Log analysis #{analysis_id} initiated",
            "chatbot_url": chatbot_url,
            "dashboard_url": f"{request.url_root}dashboard",
            "chatbot_status": response.status_code
        }), 200
        
    except Exception as e:
        analysis_results[analysis_id]["status"] = "error"
        analysis_results[analysis_id]["error"] = str(e)
        print(f"❌ Error in analysis #{analysis_id}: {str(e)}")
        
        return jsonify({
            "status": "error",
            "analysis_id": analysis_id,
            "message": str(e),
            "dashboard_url": f"{request.url_root}dashboard"
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)