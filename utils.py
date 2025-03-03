from llmproxy import generate, retrieve
import requests
import os
import re
import ast

def extract_tool(text):
    """
    Extracts the function name and parameters separately.

    Args:
        text (str): The input text containing the function call.

    Returns:
        tuple: (function_name, parameters) if found, otherwise (None, None).
    """
    match = re.search(r'(\w+)\(([\s\S]*)\)', text)
    if match:
        function_name = match.group(1)  # Extract function name
        params = match.group(2)  # Extract parameters as a string
        return function_name, params.strip()  # Return as a tuple
    return None, None  # Return None if no function call is found

def parse_params(params):
    """
    Safely parses function parameters from a string, handling cases 
    where multi-line text arguments contain escaped newline characters.

    Args:
        params (str): The string representation of function parameters.

    Returns:
        list: A list of parsed parameters.
    """
    try:
        # Convert the parameters string into a Python tuple safely
        parsed_params = ast.literal_eval(f"({params})")

        # Ensure the result is a list
        if isinstance(parsed_params, tuple):
            return list(parsed_params)
        return [parsed_params]
    
    except SyntaxError as e:
        print(f"Syntax error while parsing parameters: {e}")
    except Exception as e:
        print(f"Error parsing parameters: {e}")

    return []

def advisor(query: str, user: str, advisor_response: bool):
    """
    AI Advisor for Tufts CS Students.

    This function provides guidance to Tufts University Computer Science students.
    It differentiates between handling user queries (including escalation) and 
    transmitting a response from a human advisor.

    Args:
        query (str): The user's query.
        user (str): The user's session ID.
        advisor_response (bool): Flag indicating if this response is from a human advisor.

    Returns:
        str: The AI's response.
    """

    # Original system prompt (unchanged)
    system_prompt = """
        ### AI Advisor for Tufts CS Students  

        You are a **friendly and knowledgeable AI assistant** dedicated to 
        helping Tufts University Computer Science students. Your goal is to 
        provide **accurate, concise, and actionable** responses to inquiries 
        about **courses, research, careers, and department policies**. If a 
        query is beyond your knowledge, you will **escalate it to a human 
        advisor**. 

        ---

        ### **Your Role**  
        You assist students with:

        - **Course selection & prerequisites**  
        - Example: _"For COMP 160 (Algorithms), you need COMP 15 and either 
        COMP/MATH 22 or 61."_
        - **Research opportunities**  
        - Example: _"Prof. Smith’s lab is accepting undergrad researchers in 
        machine learning."_
        - **Career guidance** (internships, job applications, networking)  
        - Example: _"The CS career fair is in September, and Handshake updates 
        weekly."_
        - **University policies** relevant to CS students  
        - Example: _"To transfer a CS course, you need approval from the 
        undergraduate director."_

        ---

        ### **Response Style**  
        - **Conversational yet professional** (use simple emojis occasionally: 
        ✅, 📚, 🎓).  
        - **Personalized** (mention Tufts-specific buildings, traditions, or 
        campus resources).  
        - **Concise (3-5 sentences)** unless a detailed explanation is necessary.  
        - **Always include actionable next steps** when applicable.  

        ---
        ### **Boundaries**  
        🚫 **Do NOT**:  
        - Complete assignments or coding tasks.  
        - Provide details on non-CS departments or university-wide matters.  
        - Speculate on professor preferences or grading policies.  
        - Guarantee outcomes of petitions or policy exceptions.  

        ---

        ### **Handling Unresolved Queries**  
        If you cannot fully answer a student’s question after **2-3 exchanges**, 
        take one of the following actions:  

        #### **1️⃣ Request Clarification**  
        💬 _"I want to make sure I fully understand your question. Could you 
        clarify [specific aspect]?"_  

        #### **2️⃣ Escalate to a Human Advisor**  
        If further assistance is needed:  
        1. _"It looks like I don’t have the exact information you need. Would 
        you like me to forward your question to a human advisor?"_  
        2. If the student agrees, confirm: _"I'll summarize your question as: 
        [summary]. Does that sound accurate?"_  
        3. Upon confirmation, use the provided tool to send a message to the 
        department chair.  

        ---

        ### **Escalation Tool: `send_message`**  
        - **Function**: Sends a message to the CS department chair with the 
        student’s query.  
        - **Parameters**:  
        - **Student:** {user} 
        - **Question:** `<student's question>`  
        - **Background:** `<helpful context about the inquiry>`  
        - **Example Usage**:  
        ```send_message("Student: Jane Doe", "Question: What are the 
        prerequisites for COMP 160?", "Background: Jane is a sophomore 
        considering the algorithms course next semester.")```      
    """

    # Prompt for transmitting a human advisor's response
    transmit_response_prompt = """
    You have received a response from a **human advisor**.  
    Use this response to provide a clear and direct answer to the student.

    Respond in the following format:
    - _"I checked with a human advisor, and here’s the guidance: [advisor’s response]. 
      Let me know if you have any further questions!"_
    """

    try:
        if advisor_response:
            # If this is a response from a human advisor, format it accordingly
            response = generate(model='4o-mini',
                                system=transmit_response_prompt,
                                query=f"Human Advisor Response:\n\n{query}",
                                temperature=0.3,
                                session_id=user)
        else:
            # Standard AI response handling (including escalation if needed)
            response = generate(model='4o-mini',
                                system=system_prompt,
                                query=f"Query:\n\n{query}",
                                temperature=0.3,
                                session_id=user)

        return response['response']
    
    except Exception as e:
        print(f"Error occurred with parsing output: {e}")
        return "An error occurred while processing your request."


def generate_response(query: str, user: str, advisor_response: bool):
    print("Received query:", query)
    print("User:", user)
    print("Advisor Response:", advisor_response)
    """
    Generates a response to a user query and executes any extracted tool call.

    Args:
        query (str): The user's query.
        user (str): The user's session ID.

    Returns:
        str: The generated response.
    """    

    response = advisor(query, user, advisor_response)
    print("Generated response:", response)

    # Extract tool name and parameters
    tool_name, params = extract_tool(response)

    if tool_name == "send_message":
        param_list = parse_params(params)  # Use safer parsing
        if len(param_list) == 3:  
            try:
                tool_response = send_message(*param_list) 
                print(f"Tool Output: {tool_response}\n")
                return tool_response  # Return tool's response instead of LLM's
            except Exception as e:
                print(f"Error occurred with tool execution: {e}")
                return "An error occurred while forwarding your query."
        else:
            print("Error: Incorrect number of parameters for send_message.")
            return "Error: Incorrect function parameters."
    
    return response

def send_message(student: str, question: str, background: str):
    """
    Sends an email to the CS department's human advisor with the student's query.

    Args:
        student (str): Information about the student.
        question (str): The student's question.
        background (str): Additional context about the inquiry.

    Returns:
        str: A message indicating the success or failure of the email sending process.
    """
    try:
        # Compose the email message
        # Properly format the JSON payload as a dictionary (not a set)
        payload = {
            "bot": "AI Advisor",
            "student": student,
            "question": question,
            "background": background
        }
        
        # Send the email
        response = requests.post(
            "https://institutional-galina-tufts-077937b9.koyeb.app/query", 
            json=payload
        )

        # Ensure a valid response
        if response.status_code == 200:
            return "Your query has been forwarded to the department chair for further assistance. I will notify you once a response is received."

        return f"Error: Received response code {response.status_code}, Response: {response.text}"

    except Exception as e:
        return f"Error occurred while sending the message: {e}"