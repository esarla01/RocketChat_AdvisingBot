from llmproxy import generate, text_upload
import requests
import os
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from flask_mail import Mail, Message
import os


googleApiKey = os.environ.get("googleSearch")
searchEngineId = os.environ.get("googleCSEId")


def send_message(user):
    
    # API endpoint
    url = "https://chat.genaiconnect.net/api/v1/chat.postMessage" #URL of RocketChat server, keep the same

    # Headers with authentication tokens
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": os.environ.get("RC_token"), #Replace with your bot token for local testing or keep it and store secrets in Koyeb
        "X-User-Id": os.environ.get("RC_userId")#Replace with your bot user id for local testing or keep it and store secrets in Koyeb
    }

    # Payload (data to be sent)
    payload = {
        "channel": f"@{user}", #Change this to your desired user, for any user it should start with @ then the username
        "text": "Hello, this is JumboBot! I'm here to assist you with any \
        questtion you have about the computer science department at Tufts. \
        I will try to answer your question to the best of my ability, but if \
        I can't, I will email your question to the department for follow-up. " 
        # This where you add your message to the user
    }

    # Sending the POST request
    response = requests.post(url, json=payload, headers=headers)

    # Print response status and content
    print(response.status_code)
    print(response.json())  


import re

def extract_tool(text):
    """
    Extracts the function name and parameters separately.

    Args:
        text (str): The input text containing the function call.

    Returns:
        tuple: (function_name, parameters) if found, otherwise None.
    """
    match = re.search(r'(\w+)\(([^)]*)\)', text)
    if match:
        function_name = match.group(1)  # Extract function name
        params = match.group(2)  # Extract parameters as a string
        return function_name, params  # Return as a tuple
    return None, None  # Return None if no function call is found

import ast

def parse_params(params):
    """
    Safely parses function parameters from a string.
    
    Args:
        params (str): The string representation of function parameters.

    Returns:
        list: A list of parsed parameters.
    """
    try:
        return list(ast.literal_eval(f"({params})"))  # Convert the string to a tuple, then to a list
    except Exception as e:
        print(f"Error parsing parameters: {e}")
        return []

def advisor(query: str, user):

    """
    Function description goes here.
    
    Provides guidance and assistance to Tufts University Computer Science students.

    Args:
        query (str): The user's query.
        user (str, optional): The user's session ID. Defaults to 'GenericSession'.

    Returns:
        str: The response from the AI advisor.

    """
    system = """

        You are a friendly and knowledgeable AI advisor dedicated to supporting 
        Tufts University Computer Science students, capable of answering their
        questions and escalating complex issues to the department chair. Always 
        remind that you can send an email to the department chair if you cannot 
        answer their question.

        ### Knowledge Base
        You have access to information about:
        - CS course catalog including COMP 11, 15, 40, 105, 160, etc.
        - Current prerequisites for all courses
        - Department research areas (e.g., AI, Graphics, Cybersecurity)
        - Major and minor requirements
        - Standard department policies on course registration, thesis requirements, etc.

        ### Your Role
        Your primary function is to assist students with:
        - **Course selection** and prerequisite requirements
        - Example: "For COMP 160 (Algorithms), you need COMP 15 and either COMP/MATH 22 or 61"
        - **Research opportunities** within the department
        - Example: "Prof. Smith's lab is currently accepting undergrad researchers in machine learning"
        - **Career guidance**, including internships and job applications
        - Example: "The CS career fair is held each September, and Handshake listings are updated weekly"
        - **University policies** relevant to CS students
        - Example: "To get transfer credit for a CS course, you need approval from the undergraduate director"

        ### Response Style
        - Be conversational yet professional, using simple emojis occasionally (✅, 📚, 🎓)
        - Personalize responses by referring to specific Tufts buildings, traditions, or campus landmarks
        - Keep answers concise (3-5 sentences) unless detailed explanation is needed
        - Always provide actionable next steps

        ### Boundaries
        Do NOT:
        - Complete assignments or coding tasks for students
        - Provide information on non-CS departments or general university matters
        - Speculate on professor preferences or grading tendencies
        - Guarantee outcomes of petitions or policy exceptions

        ### Handling Unresolved Queries
        If the user remains unsatisfied after 2-3 response attempts:

        #### Option 1: Request Clarification
        "I want to make sure I fully understand your question. Could you provide more details about [specific aspect]?"

        #### Option 2: Email Escalation (after 3 exchanges)
        1. "It seems I don't have the specific information you need. Would you like me to forward your question to the department chair?"
        2. If yes, confirm: "I'll summarize your question as: [summary]. Is that accurate?"
        3. "Please provide your Tufts email address so the department chair can respond directly."
        4. Use the provided tool to send an email to tansu.sarlak@tufts.edu

        ### Email Format
        Hi Tansu (department chair),

        We have received a request for further information from a student regarding the following topic:
        Topic: [Brief summary of the student's query]

        Student's Question(s):
        [Include the detailed query here]

        Please assist in addressing their concern. The student's contact email is: [User's email address].

        Thank you!
        CS Advisor Bot

        ### Tool Information
        #### Email Sending Tool
        - Name: `send_email`
        - Parameters: `dst`, `subject`, `content`
        - IMPORTANT: The dst parameter should be the student's email address
    """

    try:
        response = generate(model='4o-mini',
                            system=system,
                            query="Query:\n\n{}".format(query),
                            temperature=0.3,
                            lastk=10,
                            session_id=user,
                            rag_usage=True,
                            rag_threshold=0.5,
                            rag_k=3);
        return response['response']
    except Exception as e:
        print(f"Error occurred with parsing output: {response}")
        raise e


def send_email(app, dst, subject, content):
    """Send an email using Flask-Mail."""
    try:
        mail = Mail(app)

        with app.app_context():
            msg = Message(subject=subject,
                          sender="erinsarlak003@gmail.com",
                          recipients=["tansu.sarlak@tufts.edu"],
                          cc=[dst],  # Add dst to cc
                          body=content)
            mail.send(msg)
        
        return True  # Email sent successfully
    except Exception as e:
        print(f"Error sending email: {e}")
        return False  # Email failed


def generate_response(app, query: str, user: str):
    """
    Generates a response to a user query and executes any extracted tool call.

    Args:
        app: The Flask app instance (needed for sending emails).
        query (str): The user's query.
        user (str): The user's session ID.

    Returns:
        str: The generated response.
    """
    response = advisor(query, user)
    
    print("Generated response:", response)

    # Extract tool name and parameters
    tool_name, params = extract_tool(response)

    if tool_name == "send_email":
        param_list = parse_params(params)  # Use safer parsing
        if len(param_list) == 3:  
            response = send_email(app, *param_list) 
            print(f"Output from tool: {response}\n\n")
            return "I've sent you email successfully to the department. \
            Please check your email and you'll see that you are cc'd to the \
            request email!" if response == True else "I failed to send the email. Is \
            the email you provided correct?"
        else:
            print("Error: Incorrect number of parameters for send_email.")
    return response



# # Determines whether a user query should be searched on the web
def should_search_web(query: str, user: str) -> bool:
    response = generate(model = '4o-mini',
        system = "You are an AI assistant specializing in advising Tufts Computer Science students. Analyze the query to determine if an external web search is required, focusing on university policies, course requirements, academic advising, or career-related information. If needed, return 'Yes', otherwise return 'No'. The return word has to be strictly 'Yes' or 'No'",
        query = f"Should this user query be searched on the web?\n\n{query}",
        temperature=0.0,
        lastk=3,
        session_id=user,
        rag_usage = True,
        rag_threshold = 0.7,
        rag_k = 3)
                
    return response['response'] == "Yes"

# # Uses GPT-4 to refine a user query into an optimized search
# # query and returns a concise, search-friendly query.
# def parse_query(query: str, user: str) -> str:

#     response = generate(model = '4o-mini',
#         system = "You are an AI assistant helping Tufts CS students with academic and career guidance. Reformulate the query into a concise, search-friendly format to retrieve information on Tufts CS courses, degree requirements, faculty, research opportunities, internships, and related topics.",
#         query = f"Rewrite this user query as a search-friendly Google query:\n\n{query}",
#         temperature=0.0,
#         lastk=0,
#         session_id=user,
#         rag_usage = False)

#     return response['response']

# # Performs a Google Custom Search API query and 
# # returns the top 'num_results' links.
# def google_search(query: str, num_results: int = 3) -> list:

#     if not isinstance(query, str):
#         raise ValueError("Query must be a string")

  
#     cleaned_query = query.replace('"', '')  # Remove quotes from the query
                                  
#     search_url = "https://www.googleapis.com/customsearch/v1"
#     params = {
#         "key": googleApiKey,
#         "cx": searchEngineId,
#         "q": cleaned_query,
#         "num": num_results
#     }

#     try:
#         response = requests.get(search_url, params=params, timeout=10)

#         response.raise_for_status()
#         data = response.json()

#         results = data.get("items", [])

#         important_results = []
#         for item in results:
#             url = item["link"]
#             content = fetch_full_content(url)
#             important_results.append(content)

#         return important_results

#     except Exception as e:
#         print(f" Unexpected error: {e}")

#     return []

# # Fetches the full content of a webpage and returns it as a string
# def fetch_full_content(url: str, timeout: int = 10) -> str:
#     try:
#         response = requests.get(url, timeout=timeout)
#         response.raise_for_status()
#     except Exception as e:
#         print(f"Error fetching {url}: {e}")
#         return ""

#     soup = BeautifulSoup(response.text, 'html.parser')

#     # Find the main content div, articles, or sections
#     content = soup.find('article') or soup.find('main') or soup.find('body')
#     return content.get_text(strip=True) if content else soup.get_text(strip=True)


# # Determines whether a response contains useful information`
# def is_useful_information(response: str, user: str) -> bool:
#     response = generate(model = '4o-mini',
#         system = "You are an AI assistant evaluating whether the response contains useful information for a Tufts CS student. Assess if it helps with academic advising, course planning, research opportunities, or career guidance. If useful, return 'Yes', otherwise return 'No'.",
#         query = f"Is the following response useful?\n\n{response}",
#         temperature=0.0,
#         lastk=0,
#         session_id=user,
#         rag_usage = True,
#         rag_threshold = 0.7,
#         rag_k = 3)
    
#     return response['response'] == "Yes"

# def store_context(context: str, user:str ) -> None:
#     summary = generate(model='4o-mini',
#                        system="You are an AI assistant summarizing information relevant to Tufts University Computer Science students. Generate a summary focused on academic advising, course selection, research opportunities, career paths, and university policies.",
#                        query=f"Summarize the following context:\n\n{context}",
#                        temperature=0.0,
#                        lastk=0,
#                        session_id=user,
#                        rag_usage=False)
#     text_upload(
#         text=summary['response'],
#         session_id=user,
#         strategy='fixed')

# # Generates a response to a user query using the provided context
# def generate_response(query: str, user:str ) -> str:

#     print("HELLO!")

#     try:
#         context = None

#         if  should_search_web(query, user):
#             parsed_query = parse_query(query, user)

#             google_search_results = google_search(parsed_query)

#             context = google_search_results;

#         # Generate a response using LLMProxy
#         if context:
#             response = generate(model='4o-mini',
#                 system = "You are an AI advisor for Tufts University Computer Science students. Answer student queries related to course selection, prerequisites, research opportunities, career advice, internships, and university policies. If user asks an unrelated question, remind the user your purpose. Be conversational, and friendly.'.",
#                 query=f"User query:\n\n{query}\n\nContext:\n\n{context}",
#                 temperature=0.0,
#                 lastk=4,
#                 session_id=user,
#                 rag_usage=True,
#                 rag_threshold=0.7,
#                 rag_k=3)
#             if is_useful_information(response, user):
#                 store_context(response, user)
#         else:
#             response = generate(model='4o-mini',
#                 system="You are an AI advisor for Tufts University Computer Science students. Answer student queries related to course selection, prerequisites, research opportunities, career advice, internships, and university policies. If user asks an unrelated question, remind the user your purpose. Be conversational, and friendly.",
#                 query=f"User query:\n\n{query}",
#                 temperature=0.0,
#                 lastk=4,
#                 session_id=user,
#                 rag_usage=True,
#                 rag_threshold=0.7,
#                 rag_k=3)
#             print("Printed response without context")

#         response['response'] = clean_markdown(response['response'])

#     except Exception as e:
#         print(f"Error generating response: {e}")
             
#     return response

# def clean_markdown(text: str) -> str:
#     """
#     Removes markdown bold and extra newlines from the input text.
    
#     Parameters:
#       text (str): The original markdown-formatted text.
    
#     Returns:
#       str: The cleaned-up plain text.
#     """
#     # Remove markdown bold markers (and similar formatting)
#     text = re.sub(r'\*\*', '', text)
#     text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove markdown links

    
#     # Optionally, remove extra whitespace/newlines (keeping paragraph breaks)
#     text = re.sub(r'\n\s*\n', '\n', text)  # Remove extra newlines
    
#     return text.strip()
