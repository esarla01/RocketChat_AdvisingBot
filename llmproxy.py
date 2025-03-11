import os
import json
import requests

with open('config.json', 'r') as file:
    config = json.load(file) 

# Read proxy config from environment
end_point = os.environ.get("endPoint")
api_key = os.environ.get("apiKey")

api_key_local = config["apiKey"]
end_point_local = config["endPoint"]

# end_point = "https://a061igc186.execute-api.us-east-1.amazonaws.com/dev"
# api_key = "comp150-cdr-2025s-aSSTA2yLUUyoV2PZD6cD8y2ZKC1pMgNk5h7qVgNL"

def retrieve(
    query: str,
    session_id: str,
    rag_threshold: float,
    rag_k: int
    ):

    headers = {
        'x-api-key': api_key,
        'request_type': 'retrieve'
    }

    request = {
        'query': query,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            msg = json.loads(response.text)
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg  

def generate(
    model: str,
    system: str,
    query: str,
    temperature: float | None = None,
    lastk: int | None = None,
    session_id: str | None = None,
    rag_threshold: float | None = 0.5,
    rag_usage: bool | None = False,
    rag_k: int | None = 0
    ):
    

    headers = {
        'x-api-key': api_key,
        'request_type': 'call'
    }

    request = {
        'model': model,
        'system': system,
        'query': query,
        'temperature': temperature,
        'lastk': lastk,
        'session_id': session_id,
        'rag_threshold': rag_threshold,
        'rag_usage': rag_usage,
        'rag_k': rag_k
    }

    msg = None

    try:
        response = requests.post(end_point, headers=headers, json=request)

        if response.status_code == 200:
            res = json.loads(response.text)
            msg = {'response':res['result'],'rag_context':res['rag_context']}
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    return msg  



def upload(multipart_form_data, local=False):

    if not local:
        headers = {
            'x-api-key': api_key,
            'request_type': 'add'
        }
    else:
        headers = {
            'x-api-key': api_key_local,
            'request_type': 'add'
        }

    end_point = end_point_local if local else end_point

    msg = None
    try:
        response = requests.post(end_point, headers=headers, files=multipart_form_data)
        
        if response.status_code == 200:
            msg = "Successfully uploaded. It may take a short while for the document to be added to your context"
        else:
            msg = f"Error: Received response code {response.status_code}"
    except requests.exceptions.RequestException as e:
        msg = f"An error occurred: {e}"
    
    return msg


def pdf_upload(
    path: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None,
    local: bool = False,
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }

    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'file': (None, open(path, 'rb'), "application/pdf")
    }

    response = upload(multipart_form_data, local)
    return response

def text_upload(
    text: str,    
    strategy: str | None = None,
    description: str | None = None,
    session_id: str | None = None
    ):
    
    params = {
        'description': description,
        'session_id': session_id,
        'strategy': strategy
    }


    multipart_form_data = {
        'params': (None, json.dumps(params), 'application/json'),
        'text': (None, text, "application/text")
    }


    response = upload(multipart_form_data)
    return response