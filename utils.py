from llmproxy import generate, retrieve,text_upload
import requests
import os
import re
import ast
import json
from bs4 import BeautifulSoup

GOOGLE_API_KEY = os.getenv("googleSearch")
SEARCH_ENGINE_ID = os.getenv("googleCSEId")
# GOOGLE_API_KEY = "AIzaSyA9aWt3R251o7VlMv2mzRoqgjIS2t_wrio"
# SEARCH_ENGINE_ID = "c43b2b31e407e4d17"

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

def advisor(query: str, user: str, bot):
    context = None

    rag_context = "No relevant rag context!"
    # try:
    #     rag_context = retrieve(
    #         query=query,
    #             session_id='RagSession',
    #             rag_threshold= 0.5,
    #             rag_k=3
    #     )
    #     print('Rag Context:', rag_context)
    # except Exception as e:
    #     rag_context = "No relevant rag context!"
    #     print('Error retrieving rag context:', e)
    
    # print('Rag Context:', rag_context)

    if should_search_web(query, rag_context, user):
        parsed_query = parse_query(query)
        context = google_search(parsed_query)
        store_context(context)
        context = retrieve(
            query=query,
                session_id='RagSession',
                rag_threshold= 0.5,
                rag_k=3
        )
    else:
        context = rag_context_string_simple(rag_context)

    if not bot:
        if not context or context == "No relevant information found on web!":
            query = f"Query:\n{query}"
        else:
            query = f"Query:\n{query}. Some additional context: \n{context}" 
    
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
    system_prompt = f"""
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
        - **Student:** "{user}"
        - **Question:** `<student's question>`  
        - **Background:** `<helpful context about the inquiry>`  
        - **Example Usage**:  
        ```send_message("Student: {user}", "Question: What are the 
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
        if bot == "HumanAdvisor":
            # If this is a response from a human advisor, format it accordingly
            response = generate(model='4o-mini',
                                system=transmit_response_prompt,
                                query=f"Human Advisor Response:\n\n{query}",
                                lastk=10,
                                temperature=0.3,
                                session_id=user)
        else:
            # Standard AI response handling (including escalation if needed)
            response = generate(model='4o-mini',
                                system=system_prompt,
                                lastk=10,
                                query=query,
                                temperature=0.3,
                                session_id=user)
                        
        return response['response']
    
    except Exception as e:
        print(f"Error occurred with parsing output: {e}")
        return "An error occurred while processing your request."

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
    
def generate_response(query: str, user: str, bot=False):
    print("Received query:", query)
    print("User:", user)
    """
    Generates a response to a user query and executes any extracted tool call.

    Args:
        query (str): The user's query.
        user (str): The user's session ID.

    Returns:
        str: The generated response.
    """    

    response = advisor(query, user, bot)
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


def rag_context_string_simple(rag_context):

    context_string = ""

    i=1
    for collection in rag_context:
    
        if not context_string:
            context_string = """The following is additional context that may be helpful in answering the user's query. """

        context_string += """
        #{} {}
        """.format(i, collection['doc_summary'])
        j=1
        for chunk in collection['chunks']:
            context_string+= """
            #{}.{} {}
            """.format(i,j, chunk)
            j+=1
        i+=1
    return context_string


def should_search_web(query: str, context: str, user: str) -> bool:
    response = generate(
        model='4o-mini',
        system="""
        You are an AI knowledge base assistant for Tufts CS students. Given a 
        user query and retrieved internal knowledge (RAG), determine: Is the 
        existing knowledge sufficient to answer the query? If the query is not
        clear, check the previous messages for context.
        - If yes, strictly return "NO_SEARCH_NEEDED".
        - If no, strictly return "SEARCH_NEEDED".     
        """,
        query=f"Query: {query}\nContext: {context}",
        temperature=0.0,
        lastk=10,
        session_id="web_searcher",
        rag_usage=False
    )    
              
    return response['response'] == "SEARCH_NEEDED"


def parse_query(query: str) -> str:
    response = generate(
        model='4o-mini',
        system="""
        You are an AI assistant that reformulates search queries for Tufts CS students. 
        Your task is to rewrite the given query into a concise, search-friendly format 
        to retrieve accurate information on Tufts CS courses, degree requirements, 
        faculty, research, internships, and related topics. If the query is not
        clear, check the previous messages for context.
        """,
        query=f"Reformulate this query for a Google search:\n\n{query}",
        temperature=0.0,
        lastk=10,
        session_id="query_parser",
        rag_usage=False
    )
    return response['response']


def fetch_full_content(url: str, timeout: int = 10) -> str:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the main content div, articles, or sections
    content = soup.find('article') or soup.find('main') or soup.find('body')
    return content.get_text(strip=True) if content else soup.get_text(strip=True)

def google_search(query: str, num_results: int = 3) -> str:

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY, 
        "cx": SEARCH_ENGINE_ID, 
        "q": query.replace('"', ''), 
        "num": num_results
    }
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("items", [])
        
        if not results:
            return "No relevant information found on web!"

        formatted_results = "\n\n".join(f"Link: {item['link']}\n Summary: {item.get('snippet', 'No summary available')}" for item in results)

        system_prompt = """
        You are an AI assistant selecting the most relevant search result for a 
        given query. Your task is to analyze the provided search results and 
        choose the single most useful link that is likely to contain a 
        comprehensive answer. 

        - Prioritize results from official sources (e.g., university websites) 
            or authoritative references.
        - If multiple results seem relevant, select the most detailed and 
            directly related one.
        - If none of the results are useful, respond with "$NO URLS$" and 
            nothing else.
        - Strictly return only the chosen URL, without any additional text.
        """

        selected_url = generate(
            model='4o-mini',
            system=system_prompt,
            query=f"Query: {query}\nResults:\n{formatted_results}",
            temperature=0.1,
            lastk=1,
            session_id="GenericSessionId",
            rag_usage=False
        ).get("response", "$NO URLS$")

        if selected_url != "$NO URLS$":
            return fetch_full_content(selected_url)
        else:
            return "No relevant information found on web!"

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    

def store_context(context: str) -> None:
    """Evaluates and stores meaningful information into RAG for future use."""
    response = generate(
        model='4o-mini',
        system="""
        You are an AI assistant managing a knowledge base for Tufts CS students. 
        Given new information, determine whether it is valuable for future reference. 

        - If the information is relevant to academic advising, courses, research, 
          careers, or university policies, summarize it concisely.  
        - If the information is too general, redundant, or not useful for RAG, return "$DISCARD$".
        - If storing, ensure the summary is structured and retains key details.
        """,
        query=f"Evaluate and summarize the following information for storage:\n\n{context}",
        temperature=0.0,
        lastk=0,
        session_id='RagSession',
        rag_usage=False
    )

    summary = response.get("response", "$DISCARD$")

    if summary != "$DISCARD$":
        text_upload(text=summary, session_id="RagSession", strategy='fixed')
