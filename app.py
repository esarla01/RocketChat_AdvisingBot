import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import generate_response
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():
    pdf_path = 'soe-grad-handbook.pdf'
    
    # Check if PDF file is already uploaded
    if not os.path.exists(pdf_path):
        pdf_upload(
            path=pdf_path,
            session_id=user,
            strategy='smart')
    
    data = request.get_json() 

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    print(data)

    # Ignore bot messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})

    print(f"Message from {user} : {message}")

    # Generate a response using LLMProxy
    response = generate_response(message, user)

    response_text = response['response']
    
    # Send response back
    print(response_text)

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()