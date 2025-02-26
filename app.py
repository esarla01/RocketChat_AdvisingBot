import time
import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import generate_response, send_message
import os
import hashlib


app = Flask(__name__)

# Email Configuration (Replace with your credentials)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'erinsarlak003@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'jqqs nlux pnlk pxmz'  # Use App Password
app.config['MAIL_DEFAULT_SENDER'] = 'erinsarlak003@gmail.com'

# Dictionary to keep track of users who have received the initial message
user_initial_message_sent = {}

@app.before_first_request
def initialize():
    """Uploads shared documents to a small set of predefined RAG SIDs."""
    try:
        pdf_upload(
            path='undergrad-course-descriptions.pdf',
            session_id='GenericSession',
            strategy='smart'
        )
        pdf_upload(
            path='sl-bscs-degree-sheet-2028.pdf',
            session_id='GenericSession',
            strategy='smart'
        )

    except Exception as e:
        print(f"Error during initialization: {e}")

    print("Initialization complete with shared RAG sessions!")


@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})


@app.route('/query', methods=['POST'])
def main():
    data = request.get_json() 

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    print(user)
    print(data)

    # Ignore bot messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})

    print(f"Message from {user}: {message}")

    response = generate_response(app, message, user)  # Pass shared SID
 
    # Send response back
    print(response)

    return jsonify({"text": response})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()