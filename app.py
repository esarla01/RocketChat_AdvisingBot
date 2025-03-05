import time
import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import generate_response, store_context
import os
import hashlib


app = Flask(__name__)

def send_advisor_message(username, text):
    """Send a direct message to a specific user in Rocket.Chat"""
    rocketchat_url = "https://chat.genaiconnect.net/api/v1/chat.postMessage"
    
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": "ISX3g0wXYBf2eKlIRTi66h8_BJeWJmPbIt4Wp-lkrbJ",
        "X-User-Id": "PG8JfShvZJYdehnf5"
    }

    payload = {
        "channel": f"@{username}",  # Sends a direct message to the user
        "text": text
    }

    response = requests.post(rocketchat_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"Message successfully sent to {username}")
    else:
        print(f"Failed to send message: {response.json()}")


# @app.before_first_request
def initialize():
    """Uploads shared documents to a small set of predefined RAG SIDs."""
    try:
        pdf_upload(
            path='undergrad-course-descriptions.pdf',
            session_id='RagSession',
            strategy='smart'
        )
        pdf_upload(
            path='sl-bscs-degree-sheet-2028.pdf',
            session_id='RagSession',
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

    user = data.get("user_name", "Unknown")
    message = data.get("text", "")
    bot = data.get("bot", "RealUser")

    if bot == "HumanAdvisor":
        response = generate_response(message, user, True)

        send_advisor_message(user, response)

        store_context(response)
        
        return jsonify({"text": f"Answer sent to {user} ✅"})
    else: 
        response = generate_response(message, user)

    return jsonify({"text": response})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()