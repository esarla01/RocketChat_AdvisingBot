from llmproxy import generate, text_upload
import requests
import os
import json
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

googleApiKey = os.environ.get("googleSearch")
searchEngineId = os.environ.get("googleCSEId")

# Determines whether a user query should be searched on the web
def should_search_web(query: str, user: str) -> bool:
    response = generate(model = '4o-mini',
        system = "You are an AI assistant specializing in advising Tufts Computer Science students. Analyze the query to determine if an external web search is required, focusing on university policies, course requirements, academic advising, or career-related information. If needed, return 'Yes', otherwise return 'No'.",
        query = f"Should this user query be searched on the web?\n\n{query}",
        temperature=0.0,
        lastk=3,
        session_id=user,
        rag_usage = True,
        rag_threshold = 0.7,
        rag_k = 3)
                
    return response['response'] == "Yes"

# Uses GPT-4 to refine a user query into an optimized search
# query and returns a concise, search-friendly query.
def parse_query(query: str, user: str) -> str:

    response = generate(model = '4o-mini',
        system = "You are an AI assistant helping Tufts CS students with academic and career guidance. Reformulate the query into a concise, search-friendly format to retrieve information on Tufts CS courses, degree requirements, faculty, research opportunities, internships, and related topics.",
        query = f"Rewrite this user query as a search-friendly Google query:\n\n{query}",
        temperature=0.0,
        lastk=0,
        session_id=user,
        rag_usage = False)

    return response['response']

# Performs a Google Custom Search API query and 
# returns the top 'num_results' links.
def google_search(query: str, num_results: int = 3) -> list:

    if not isinstance(query, str):
        raise ValueError("Query must be a string")

  
    cleaned_query = query.replace('"', '')  # Remove quotes from the query
                                  
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": googleApiKey,
        "cx": searchEngineId,
        "q": cleaned_query,
        "num": num_results
    }

    try:
        response = requests.get(search_url, params=params, timeout=10)

        response.raise_for_status()
        data = response.json()

        results = data.get("items", [])

        important_results = []
        for item in results:
            url = item["link"]
            content = fetch_full_content(url)
            important_results.append(content)

        return important_results

    except Exception as e:
        print(f" Unexpected error: {e}")

    return []

# Fetches the full content of a webpage and returns it as a string
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


# Determines whether a response contains useful information`
def is_useful_information(response: str, user: str) -> bool:
    response = generate(model = '4o-mini',
        system = "You are an AI assistant evaluating whether the response contains useful information for a Tufts CS student. Assess if it helps with academic advising, course planning, research opportunities, or career guidance. If useful, return 'Yes', otherwise return 'No'.",
        query = f"Is the following response useful?\n\n{response}",
        temperature=0.0,
        lastk=0,
        session_id=user,
        rag_usage = True,
        rag_threshold = 0.7,
        rag_k = 3)
    
    return response['response'] == "Yes"

def store_context(context: str, user:str ) -> None:
    summary = generate(model='4o-mini',
                       system="You are an AI assistant summarizing information relevant to Tufts University Computer Science students. Generate a summary focused on academic advising, course selection, research opportunities, career paths, and university policies.",
                       query=f"Summarize the following context:\n\n{context}",
                       temperature=0.0,
                       lastk=0,
                       session_id=user,
                       rag_usage=False)
    text_upload(
        text=summary['response'],
        session_id=user,
        strategy='fixed')

# Generates a response to a user query using the provided context
def generate_response(query: str, user:str ) -> str:

    print("HELLO!")

    try:
        context = None

        if  should_search_web(query, user):
            parsed_query = parse_query(query, user)

            google_search_results = google_search(parsed_query, user)

            context = google_search_results;

        # Generate a response using LLMProxy
        if context:
            response = generate(model='4o-mini',
                system = "You are an AI advisor for Tufts University Computer Science students. Answer student queries related to course selection, prerequisites, research opportunities, career advice, internships, and university policies. If user asks an unrelated question, remind the user your purpose. Be conversational, and friendly.'.",
                query=f"User query:\n\n{query}\n\nContext:\n\n{context}",
                temperature=0.0,
                lastk=4,
                session_id=user,
                rag_usage=True,
                rag_threshold=0.7,
                rag_k=3)
            if is_useful_information(response):
                store_context(response)
        else:
            response = generate(model='4o-mini',
                system="You are an AI advisor for Tufts University Computer Science students. Answer student queries related to course selection, prerequisites, research opportunities, career advice, internships, and university policies. If user asks an unrelated question, remind the user your purpose. Be conversational, and friendly.",
                query=f"User query:\n\n{query}",
                temperature=0.0,
                lastk=4,
                session_id=user,
                rag_usage=True,
                rag_threshold=0.7,
                rag_k=3)
            print("Printed response without context")

        response['response'] = clean_markdown(response['response'])

    except Exception as e:
        print(f"Error generating response: {e}")
             
    return response

def clean_markdown(text: str) -> str:
    """
    Removes markdown bold and extra newlines from the input text.
    
    Parameters:
      text (str): The original markdown-formatted text.
    
    Returns:
      str: The cleaned-up plain text.
    """
    # Remove markdown bold markers (and similar formatting)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # Remove markdown links

    
    # Optionally, remove extra whitespace/newlines (keeping paragraph breaks)
    text = re.sub(r'\n\s*\n', '\n', text)  # Remove extra newlines
    
    return text.strip()
