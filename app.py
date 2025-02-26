import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import send_message
import os

app = Flask(__name__)

# Dictionary to keep track of users who have received the initial message
user_initial_message_sent = {}

@app.before_first_request
def initialize():

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

    print("Initialization complete!")

@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})

@app.route('/query', methods=['POST'])
def main():

    data = request.get_json() 

    # Extract relevant information
    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    print(data)

    # Ignore bot messages
    if data.get("bot") or not message:
        return jsonify({"status": "ignored"})

    print(f"Message from {user} : {message}")

    # Check if the user has already received the initial message
    if user not in user_initial_message_sent:
        send_message(user)
        # Mark that the user has received the initial message
        user_initial_message_sent[user] = True

    if not data.get("bot") and message:
        send_message(user)

    # Generate a response using LLMProxy
    response = generate(
        model='4o-mini',
        system='answer my question and add keywords',
        query= message,
        temperature=0.0,
        lastk=5,
        session_id='GenericSession',
        rag_usage=True,
        rag_threshold=0.7,
        rag_k=3
    )

    response_text = response['response']
    
    # Send response back
    print(response_text)

    return jsonify({"text": response_text})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()