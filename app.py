import time
import requests
from flask import Flask, request, jsonify
from llmproxy import generate, pdf_upload
from utils import generate_response, send_message
import os
import hashlib


app = Flask(__name__)


# @app.before_first_request
# def initialize():
#     """Uploads shared documents to a small set of predefined RAG SIDs."""
#     try:
#         pdf_upload(
#             path='undergrad-course-descriptions.pdf',
#             session_id='GenericSession',
#             strategy='smart'
#         )
#         pdf_upload(
#             path='sl-bscs-degree-sheet-2028.pdf',
#             session_id='GenericSession',
#             strategy='smart'
#         )
 
#     except Exception as e:
#         print(f"Error during initialization: {e}")

#     print("Initialization complete with shared RAG sessions!")


@app.route('/', methods=['POST'])
def hello_world():
   return jsonify({"text":'Hello from Koyeb - you reached the main page!'})


@app.route('/query', methods=['POST'])
def main():
    data = request.get_json() 

    user = data.get("user_name", "Unknown")
    message = data.get("text", "")

    # Generate response
    response = generate_response(message, user)

    return jsonify({"text": response})
    
@app.errorhandler(404)
def page_not_found(e):
    return "Not Found", 404

if __name__ == "__main__":
    
    app.run()