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

SHARED_SIDS = ["SID_1", "SID_2", "SID_3"]  # Predefined shared sessions

@app.before_first_request
def initialize():
    """Uploads shared documents to a small set of predefined RAG SIDs."""
    try:
        for sid in SHARED_SIDS:  # Upload documents to all shared SIDs
            pdf_upload(
                path='undergrad-course-descriptions.pdf',
                session_id=sid,
                strategy='smart'
            )
            pdf_upload(
                path='sl-bscs-degree-sheet-2028.pdf',
                session_id=sid,
                strategy='smart'
            )

    except Exception as e:
        print(f"Error during initialization: {e}")

    print("Initialization complete with shared RAG sessions!")


@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

\
def assign_shared_sid(user):
    """Assigns a user to one of the predefined shared SIDs."""
    index = int(hashlib.md5(user.encode()).hexdigest(), 16) % len(SHARED_SIDS)
    return SHARED_SIDS[index]


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

    # Check if the user has already received the initial message
    # If not, send the initial message; otherwise, generate a response to their query.
    # if user not in user_initial_message_sent:
    #     send_message(user)
    #     user_initial_message_sent[user] = True
    # else:

    
   # Assign user to one of the shared SIDs
    session_id = assign_shared_sid(user)
    print(f"Assigned SID for {user}: {session_id}")

    # Generate response using the assigned shared SID
    response = generate_response(app, message, session_id)  # Pass shared SID
 
 
    # Send response back
    print(response)

    return jsonify({"text": response})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()