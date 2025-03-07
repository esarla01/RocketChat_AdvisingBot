import requests
from utils import advisor

if __name__ == "__main__":


    def send_advisor_message(username, text):

        """Send a direct message to a specific user in Rocket.Chat"""
        rocketchat_url = "https://chat.genaiconnect.net/api/v1/chat.postMessage"
        
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "AzNCz3nUBiQDR_dX8iQWxY0Gsc73Q-3ZShPjSqIxW8E",
            "X-User-Id": "S2xaY9Kq9mTuKt6Hn"
        }

        payload = {
            "channel": "@tansu.sarlak",  # Sends a direct message to the user
            "text": text
        }

        response = requests.post(rocketchat_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print(f"Message successfully sent to {username}")
        else:
            print(f"Failed to send message: {response.json()}")

    send_advisor_message("sydney.bulatao", "Hello from Koyeb - you reached the main page!")