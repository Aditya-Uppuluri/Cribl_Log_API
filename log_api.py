from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/log-to-chatbot', methods=['POST'])
def receive_log():
    logs = request.get_data(as_text=True)
    
    # Construct prompt for chatbot
    prompt = f"Log analysis request:\n\n{logs}\n\nPlease perform predictive and prescriptive analysis."

    # Send to Streamlit chatbot as query param (or internal endpoint)
    chatbot_url = "https://criblchatbot-nbuhd3ky6qhstx5zdg2wgq.streamlit.app/?prompt=" + requests.utils.quote(prompt)
    
    # Just trigger it – Streamlit picks up prompt
    response = requests.get(chatbot_url)

    return jsonify({"status": "forwarded", "chatbot_response": response.status_code})

if __name__ == "__main__":
    app.run(port=5000)
