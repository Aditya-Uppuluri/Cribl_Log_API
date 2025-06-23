from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import requests
import os
import uuid
from datetime import datetime
import json
import gzip
import logging
import urllib.parse
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables BEFORE creating the app
load_dotenv()

app = Flask(__name__)

# Enhanced logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure Gemini AI with better error handling
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
model = None

def initialize_gemini():
    """Initialize Gemini AI with proper error handling"""
    global model
    
    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")
        logger.info("Please set GEMINI_API_KEY in your .env file")
        return False
    
    if not GEMINI_API_KEY.strip():
        logger.warning("⚠️ GEMINI_API_KEY is empty")
        return False
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Test the API key by trying to create a model
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini AI initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini AI: {str(e)}")
        logger.error("Please check your GEMINI_API_KEY is valid")
        model = None
        return False

# Initialize Gemini on startup
gemini_available = initialize_gemini()

# In-memory storage for analysis results (use Redis/DB in production)
analysis_results = {}

# STREAMLIT URL - Update this with your actual URL
STREAMLIT_APP_URL = "https://criblchatbot-ksbwyaufrk8t2lt6dmhdgc.streamlit.app"

def analyze_logs_with_llm(log_data, analysis_id):
    """
    Analyze log data using Gemini AI and return a structured summary
    """
    if not model:
        return {
            "status": "error",
            "summary": "LLM analysis unavailable - API key not configured or invalid",
            "threat_level": "UNKNOWN",
            "risk_score": "N/A",
            "key_findings": "LLM service unavailable",
            "recommendations": "Configure valid GEMINI_API_KEY to enable AI analysis",
            "error": "Gemini API not available"
        }
    
    try:
        # Enhanced prompt for structured analysis
        prompt = f"""
        As a cybersecurity expert, analyze the following log data and provide a structured summary:

        LOG DATA:
        {log_data}

        Please provide analysis in this EXACT format:

        THREAT_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
        RISK_SCORE: [1-10]
        SUMMARY: [2-3 sentence overview of what happened]
        KEY_FINDINGS: [Bullet points of important observations]
        IMMEDIATE_ACTIONS: [What should be done right now]
        RECOMMENDATIONS: [Long-term security improvements]

        Focus on security implications, anomalies, and actionable insights.
        """

        # Generate content with safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = model.generate_content(
            prompt,
            safety_settings=safety_settings
        )

        if response.text:
            # Parse the structured response
            analysis_text = response.text
            
            # Extract structured data
            parsed_analysis = parse_llm_response(analysis_text)
            parsed_analysis["status"] = "success"
            parsed_analysis["full_response"] = analysis_text
            
            logger.info(f"✅ LLM analysis completed for {analysis_id}")
            return parsed_analysis
        else:
            logger.warning(f"⚠️ Empty response from LLM for {analysis_id}")
            return {
                "status": "error",
                "summary": "LLM returned empty response",
                "threat_level": "UNKNOWN",
                "risk_score": "N/A",
                "key_findings": "No analysis available",
                "recommendations": "Manual review required"
            }

    except Exception as e:
        logger.error(f"❌ LLM analysis failed for {analysis_id}: {str(e)}")
        return {
            "status": "error",
            "summary": f"LLM analysis failed: {str(e)}",
            "threat_level": "UNKNOWN",
            "risk_score": "N/A",
            "key_findings": "Analysis error occurred",
            "recommendations": "Manual review required",
            "error": str(e)
        }

def parse_llm_response(response_text):
    """
    Parse the structured LLM response into components
    """
    try:
        lines = response_text.split('\n')
        parsed = {
            "threat_level": "UNKNOWN",
            "risk_score": "N/A",
            "summary": "Analysis in progress...",
            "key_findings": "Processing...",
            "immediate_actions": "Under review...",
            "recommendations": "Pending analysis..."
        }

        current_section = None
        content_buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if line.startswith("THREAT_LEVEL:"):
                parsed["threat_level"] = line.split(":", 1)[1].strip()
            elif line.startswith("RISK_SCORE:"):
                parsed["risk_score"] = line.split(":", 1)[1].strip()
            elif line.startswith("SUMMARY:"):
                parsed["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("KEY_FINDINGS:"):
                current_section = "key_findings"
                content_buffer = []
                remaining = line.split(":", 1)[1].strip()
                if remaining:
                    content_buffer.append(remaining)
            elif line.startswith("IMMEDIATE_ACTIONS:"):
                if current_section == "key_findings" and content_buffer:
                    parsed["key_findings"] = '\n'.join(content_buffer)
                current_section = "immediate_actions"
                content_buffer = []
                remaining = line.split(":", 1)[1].strip()
                if remaining:
                    content_buffer.append(remaining)
            elif line.startswith("RECOMMENDATIONS:"):
                if current_section == "immediate_actions" and content_buffer:
                    parsed["immediate_actions"] = '\n'.join(content_buffer)
                current_section = "recommendations"
                content_buffer = []
                remaining = line.split(":", 1)[1].strip()
                if remaining:
                    content_buffer.append(remaining)
            elif current_section and line:
                content_buffer.append(line)

        # Handle the last section
        if current_section == "recommendations" and content_buffer:
            parsed["recommendations"] = '\n'.join(content_buffer)

        return parsed

    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        return {
            "threat_level": "UNKNOWN",
            "risk_score": "N/A",
            "summary": "Error parsing analysis",
            "key_findings": "Parsing failed",
            "immediate_actions": "Manual review required",
            "recommendations": "Check logs manually",
            "parse_error": str(e)
        }

# Enhanced HTML template with LLM analysis display
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
        
        .ai-analysis { background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border: 2px solid #0ea5e9; border-radius: 12px; padding: 20px; margin: 15px 0; }
        .ai-header { color: #0369a1; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; }
        .ai-header::before { content: "🤖"; margin-right: 8px; font-size: 1.2em; }
        
        .threat-level { display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9em; }
        .threat-level.LOW { background-color: #d1fae5; color: #065f46; }
        .threat-level.MEDIUM { background-color: #fef3c7; color: #92400e; }
        .threat-level.HIGH { background-color: #fed7aa; color: #c2410c; }
        .threat-level.CRITICAL { background-color: #fecaca; color: #dc2626; }
        .threat-level.UNKNOWN { background-color: #e5e7eb; color: #374151; }
        
        .risk-score { display: inline-block; background: #1e40af; color: white; padding: 4px 8px; border-radius: 50%; font-weight: bold; margin-left: 10px; }
        .analysis-section { margin: 10px 0; }
        .analysis-section h4 { color: #0369a1; margin: 8px 0 4px 0; }
        .analysis-content { background: white; padding: 10px; border-radius: 6px; border-left: 3px solid #0ea5e9; white-space: pre-wrap; }
        
        .log-preview { background-color: #f3f4f6; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; max-height: 200px; overflow-y: auto; margin: 10px 0; }
        .refresh-btn { background-color: #14b8a6; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin: 10px 0; }
        .refresh-btn:hover { background-color: #0d9488; }
        .debug-info { background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; padding: 15px; margin: 10px 0; font-size: 0.9em; }
        .api-status { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .api-status.available { background-color: #f0fdf4; color: #16a34a; }
        .api-status.unavailable { background-color: #fef2f2; color: #dc2626; }
    </style>
    <script>
        function refreshPage() { location.reload(); }
        setTimeout(function() { location.reload(); }, 60000); // Auto-refresh every minute
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI-Powered Cribl Log Analysis Dashboard</h1>
            <p>Real-time log analysis with AI-generated insights</p>
        </div>
        
        <div class="api-status {{ 'available' if gemini_available else 'unavailable' }}">
            <strong>Gemini AI Status:</strong>
            {% if gemini_available %}
                ✅ Available and Ready
            {% else %}
                ❌ Unavailable - Check API Key Configuration
            {% endif %}
        </div>
        
        <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Results</button>
        
        {% if results %}
            {% for result_id, result in results.items() %}
            <div class="result-card">
                <h3>Analysis {{ result_id }} - {{ result.timestamp }}</h3>
                
                <div class="status {{ result.status }}">
                    <strong>Status:</strong>
                    {% if result.status == 'success' %}
                        ✅ Analysis Complete with AI Insights
                    {% elif result.status == 'processing' %}
                        ⏳ Processing with AI...
                    {% else %}
                        ❌ Error occurred
                    {% endif %}
                </div>
                
                {% if result.ai_analysis %}
                <div class="ai-analysis">
                    <div class="ai-header">
                        AI Security Analysis
                        <span class="threat-level {{ result.ai_analysis.threat_level }}">{{ result.ai_analysis.threat_level }}</span>
                        {% if result.ai_analysis.risk_score != 'N/A' %}
                        <span class="risk-score">{{ result.ai_analysis.risk_score }}</span>
                        {% endif %}
                    </div>
                    
                    <div class="analysis-section">
                        <h4>📋 Summary</h4>
                        <div class="analysis-content">{{ result.ai_analysis.summary }}</div>
                    </div>
                    
                    <div class="analysis-section">
                        <h4>🔍 Key Findings</h4>
                        <div class="analysis-content">{{ result.ai_analysis.key_findings }}</div>
                    </div>
                    
                    <div class="analysis-section">
                        <h4>⚡ Immediate Actions</h4>
                        <div class="analysis-content">{{ result.ai_analysis.immediate_actions }}</div>
                    </div>
                    
                    <div class="analysis-section">
                        <h4>🛡️ Recommendations</h4>
                        <div class="analysis-content">{{ result.ai_analysis.recommendations }}</div>
                    </div>
                </div>
                {% endif %}
                
                <details>
                    <summary style="cursor: pointer; color: #0369a1; font-weight: bold;">📄 View Raw Log Data</summary>
                    <div class="log-preview">{{ result.log_preview }}</div>
                </details>
                
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
    status = "✅ AI-Powered Cribl Log Relay API is running"
    if gemini_available:
        status += " with Gemini AI"
    else:
        status += " (Gemini AI unavailable)"
    return status, 200

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with API status"""
    return jsonify({
        "status": "healthy",
        "gemini_ai": "available" if gemini_available else "unavailable",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Dashboard to view analysis results with AI insights"""
    webhook_url = request.url_root.rstrip('/')
    return render_template_string(HTML_TEMPLATE,
                                results=analysis_results,
                                webhook_url=webhook_url,
                                streamlit_url=STREAMLIT_APP_URL,
                                gemini_available=gemini_available)

@app.route("/log-to-chatbot", methods=["GET", "POST", "PUT"])
def receive_log():
    """Enhanced webhook endpoint with AI analysis"""
    
    logger.info(f"📥 Received {request.method} request to /log-to-chatbot")
    
    if request.method == "GET":
        return jsonify({
            "message": "AI-Powered Webhook endpoint is active",
            "expected_method": "POST or PUT",
            "ai_analysis": "Available" if gemini_available else "Unavailable (check API key)",
            "dashboard_url": f"{request.url_root}dashboard"
        })
    
    # Process the log data
    try:
        raw_data = request.get_data()
        
        if request.headers.get('Content-Encoding') == 'gzip':
            logger.info("🗜️ Decompressing GZIP data...")
            decompressed_data = gzip.decompress(raw_data)
            data_text = decompressed_data.decode('utf-8')
        else:
            data_text = raw_data.decode('utf-8')
        
        # Parse data based on content type
        if request.content_type and 'application/json' in request.content_type:
            try:
                data = json.loads(data_text)
                if isinstance(data, list):
                    logs = '\n'.join([json.dumps(entry, indent=2) if isinstance(entry, dict) else str(entry) for entry in data])
                elif isinstance(data, dict):
                    logs = json.dumps(data, indent=2)
                else:
                    logs = str(data)
            except json.JSONDecodeError:
                logs = data_text
        else:
            logs = data_text
            
        if not logs or logs.strip() == "":
            return jsonify({"status": "error", "message": "No log data received"}), 400
            
    except Exception as e:
        logger.error(f"❌ Error parsing request data: {str(e)}")
        return jsonify({"status": "error", "message": f"Error parsing request data: {str(e)}"}), 400
    
    analysis_id = f"cribl_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logger.info(f"📥 Processing log analysis request #{analysis_id}")
    
    # Store initial result
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": logs[:1000],  # Store preview
        "status": "processing",
        "ai_analysis": None,
        "error": None,
        "debug_info": {
            "content_type": request.content_type,
            "data_length": len(logs),
            "method": request.method,
            "gemini_available": gemini_available
        }
    }
    
    # Perform AI analysis
    logger.info(f"🤖 Starting AI analysis for {analysis_id}")
    ai_analysis = analyze_logs_with_llm(logs, analysis_id)
    
    # Update result with AI analysis
    analysis_results[analysis_id]["ai_analysis"] = ai_analysis
    analysis_results[analysis_id]["status"] = "success" if ai_analysis["status"] == "success" else "error"
    
    if ai_analysis["status"] == "error":
        analysis_results[analysis_id]["error"] = ai_analysis.get("error", "AI analysis failed")
    
    logger.info(f"✅ Analysis #{analysis_id} completed")
    
    return jsonify({
        "status": "success",
        "analysis_id": analysis_id,
        "message": f"Log analysis #{analysis_id} completed",
        "ai_summary": ai_analysis.get("summary", "Analysis completed"),
        "threat_level": ai_analysis.get("threat_level", "UNKNOWN"),
        "dashboard_url": f"{request.url_root}dashboard",
        "gemini_available": gemini_available,
        "instructions": "Check the dashboard for detailed AI analysis"
    }), 200

# Test endpoint for AI analysis
@app.route("/test-ai", methods=["POST"])
def test_ai_analysis():
    """Test AI analysis with sample data"""
    test_logs = """
    {
        "timestamp": "2024-01-15T02:30:00Z",
        "user": "john.doe",
        "action": "file_access",
        "file_path": "/sensitive/financial_data.xlsx",
        "source_ip": "192.168.1.100",
        "department": "IT",
        "access_time": "02:30:00",
        "status": "success",
        "unusual_activity": "accessing sensitive files outside business hours",
        "failed_attempts": 3,
        "escalated_privileges": true
    }
    """
    
    analysis_id = f"test_ai_{str(uuid.uuid4())[:8]}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Store initial result
    analysis_results[analysis_id] = {
        "timestamp": timestamp,
        "log_preview": test_logs,
        "status": "processing",
        "ai_analysis": None,
        "error": None,
        "debug_info": {"test": True, "gemini_available": gemini_available}
    }
    
    # Perform AI analysis
    logger.info(f"🧪 Testing AI analysis for {analysis_id}")
    ai_analysis = analyze_logs_with_llm(test_logs, analysis_id)
    
    # Update with results
    analysis_results[analysis_id]["ai_analysis"] = ai_analysis
    analysis_results[analysis_id]["status"] = "success" if ai_analysis["status"] == "success" else "error"
    
    return jsonify({
        "status": "success",
        "analysis_id": analysis_id,
        "ai_analysis": ai_analysis,
        "dashboard_url": f"{request.url_root}dashboard",
        "gemini_available": gemini_available
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)