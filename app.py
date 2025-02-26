import time
import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import generate_response, send_message
import os

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

from datetime import datetime, timedelta

ROCKETCHAT_URL = "https://chat.genaiconnect.net"
AUTH_HEADERS = {
    "Content-Type": "application/json",
    "X-Auth-Token": os.environ.get("RC_token"),
    "X-User-Id": os.environ.get("RC_userId")
}

# Dictionary to store the last online time of users
last_seen = {}

def check_user_online(user):
    """Check if a user is online in Rocket.Chat."""
    url = f"{ROCKETCHAT_URL}/api/v1/users.presence?user={user}"
    response = requests.get(url, headers=AUTH_HEADERS)

    if response.status_code == 200:
        return response.json().get("presence") == "online"
    return False

def send_message(user):
    """Send a message when the user comes back online after inactivity."""
    url = f"{ROCKETCHAT_URL}/api/v1/chat.postMessage"
    payload = {
        "channel": f"@{user}",
        "text": "Welcome back! If you have any questions about the Tufts CS department, I'm here to help."
    }

    response = requests.post(url, json=payload, headers=AUTH_HEADERS)
    if response.status_code == 200:
        print(f"Message sent to {user}")
    else:
        print(f"Failed to send message: {response.json()}")

def monitor_users(users, delay_minutes=30):
    """Continuously check if users return online after inactivity."""
    while True:
        for user in users:
            is_online = check_user_online(user)
            now = datetime.now()

            if is_online:
                # If user is online and not recorded, store the timestamp
                if user not in last_seen:
                    last_seen[user] = now

                # Check if the user was offline for more than 'delay_minutes'
                elif now - last_seen[user] > timedelta(minutes=delay_minutes):
                    send_message(user)  # Send the message
                    last_seen[user] = now  # Update last seen time

            else:
                # If user is offline, update their last seen time
                last_seen[user] = now
        
        time.sleep(10)  # Poll every 10 seconds

# Example: List of users to monitor
users_to_monitor = ["username1", "username2"]

# Start monitoring users (Run this in a separate thread or background process)
monitor_users(users_to_monitor)

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

    response = ''
    # # Check if the user has already received the initial message
    # # If not, send the initial message, otherwise generate a response
    # # to their query.
    # if user not in user_initial_message_sent:
    #     send_message(user)
    #     user_initial_message_sent[user] = True
    # else:
    response = generate_response(app, message, user);
 
    # Send response back
    print(response)

    return jsonify({"text": response})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()