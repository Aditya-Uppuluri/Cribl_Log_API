from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Cribl Log Relay API is running", 200

@app.route("/log-to-chatbot", methods=["POST"])
def receive_log():
    logs = request.get_data(as_text=True)
    print("📥 Received log:")
    print(logs[:300])  # Preview first 300 chars

    prompt = f"Log analysis request:\n\n{logs}\n\nPlease perform predictive and prescriptive analysis."
    chatbot_url = "https://criblchatbot-nbuhd3ky6qhstx5zdg2wgq.streamlit.app/?prompt=" + requests.utils.quote(prompt)

    try:
        response = requests.get(chatbot_url)
        print(f"➡️ Forwarded to chatbot, status: {response.status_code}")
        return jsonify({"status": "forwarded", "chatbot_response": response.status_code}), 200
    except Exception as e:
        print(f"❌ Error sending to chatbot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
