from llmproxy import generate, retrieve,text_upload
import requests
import os
import re
import ast
import json

GOOGLE_API_KEY = os.getenv("googleSearch")
SEARCH_ENGINE_ID = os.getenv("googleCSEId")

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

def advisor(query: str, user: str):
    original_query = query
    # First retrieve the information from the rag_context (if any)
    rag_context = retrieve(
        query=query,
            session_id='miniproject_rag_10',
            rag_threshold= 0.5,
            rag_k=2
    )

    # Combine query with rag
    query = f"{query} \n Current rag_context (not web): {rag_context_string_simple(rag_context)}"


    response = AI_Agent(query)

    tool = extract_tool2(response)

    if tool:
        query = eval(tool)
        decision, summary = should_store_in_rag(original_query, query)

        if decision:
            response = text_upload(
                text= json.dumps(summary),
                session_id='miniproject_rag_10',
                strategy='fixed'
            )
        response = AI_Agent(query)

        print(response)

        if response == "$NO CONTEXT$":
            context=''
        else:
            context = response

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
        if user == "HumanAdvisor":
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
                                query=f"Query:\n\n{query} \n Some additional context:\n {context}",
                                temperature=0.3,
                                session_id=user)

        return response['response']
    
    except Exception as e:
        print(f"Error occurred with parsing output: {e}")
        return "An error occurred while processing your request."


def generate_response(query: str, user: str):
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

    response = advisor(query, user)
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
    


def AI_Agent(query):
    system= f"""
            You are an AI agent designed to help a chatbot for Tufts University
            computer science students. Your goal is to get necessary context
            so that the chatbot can accurately answer to the user's query. 
            
            In addition to your own intelligence, you are given access to a 
            tool to access the web.

            You will not be interacting with user instead, you will be given a
            query and some initial context (rag_context). You must decide
            if this initial context is enough to answer the user's query.
            If the context is not enough, strictly only respond with the tool 
            name and parameters that you want to execute to get more information.
            Otherwise, strictly just forward the exact same rag context shared with
            you, do not try to answer the user's query, just forward the context.

            If the query is not a question related to cs advising, strictly reply 
            with the following message: $NO CONTEXT$

            # If a tool is used
            The ouput of tool execution will be shared with you so you can decide
            your next steps. If the user provides you with more information from
            the web, clean the information and put the important bits into bullet
            points and strictly just reply with that, nothing else.

            ### PROVIDED TOOLS INFORMATION ###
            ## 1. Tool to retrieve a list of urls from the web along with a 
            brief summary about them.
            ## Intructions: Remember that you have a query from the user, make
            sure that the parameter you pass to this tool is an enhanced query,
            suitable for a google search.

            Name: web_search
            Parameters: query
            example usage: web_search("Tufts CS Major requirements")
            """

    response = generate(
        model='4o-mini',
        system=system,
        query=query,
        temperature=0.1,
        lastk=3,
        session_id="miniproject_10",
        rag_usage=False
    )
    return response['response']

def extract_tool2(text):
    match = re.search(r'web_search\([^)]*\)', text)
    if match:
        return match.group()
    return ""


def format_results_for_llm(results):
    """Format a list of dictionaries into a string for LLM input"""
    formatted_results = "\n\n".join(
        [f"Link: {item['link']}\nSummary: {item['summary']}" for item in results]
    )
    return formatted_results

def web_search(query, num_results=5):
    """Perform a Google search and return the top result links with summaries"""

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query,
        "num": num_results
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract URLs and summaries (snippets) from search result items
        results = [
            {"link": item["link"], "summary": item.get("snippet", "No summary available")}
            for item in data.get("items", [])
        ]

        results = format_results_for_llm(results)
        system=f"""
                You will be given links and summaries. Your job is to use this
                information to pick the link which you think has the most useful
                information to answer a query that will also be given to you.
                Once you identified the url, strictly, just respond with the url
                and nothing else.

                If no links are provided, just respond with $NO URLS$
                """
        response = generate(
            model='4o-mini',
            system=system,
            query=f"query:{query}urls:{results}",
            temperature=0.1,
            lastk=1,
            session_id="GenericSessionId",
            rag_usage=False
        )
        print(f"[Debugging] This is the url: {response['response']}")
        print(type(response['response']))
        web_content = get_page(response['response'])
        return web_content


    except requests.exceptions.RequestException as e:
        return f"Error: {e}"
    

# function to create a context string from retrieve's return val
def rag_context_string_simple(rag_context):

    context_string = ""

    i=1
    for collection in rag_context:
    
        if not context_string:
            context_string = """The following is additional context that may be helpful in answering the user's query."""

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


def should_store_in_rag(query, web_content):
        """
        Asks the LLM whether the web data should be stored in RAG.
        Returns a tuple (decision, summary)
        """
        system_prompt = """
        You are a knowledge base for a Tufts CS advising chatbot. Given the user 
        question and retrieved web search results, determine:
        - Should this information be stored in the chatbot's internal knowledge base (RAG)
        - If yer, provide a concise, structured summary suitable for storage.
        Note that it might be better if time-sensitive or dynamic information is not
        stored in RAG as this might change. However, evergreen and useful information
        should be stored in RAG.

        The output format shuld be:
        - Decision: [STORE // DISCARD]
        - Summary: [Concise summary]
        """

        response = generate(
            model = '4o-mini',
            system = json.dumps(system_prompt),
            query = f'Query: {json.dumps(query)}. Web content: \n{web_content}',
            temperature=0.0,
            lastk=1,
            session_id='GenericSession')
        # print(f"\n\n{response}\n\n")
        decision = "STORE" in response['response']
        summary = None
        if decision:
            summary_start = response['response'].find("- Summary:")
            if summary_start != -1:
                summary = response['response'][summary_start + len("- Summary:"):]
        return decision, summary