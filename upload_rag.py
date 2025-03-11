from utils import RAG_CONTEXT_SESSION
from llmproxy import pdf_upload
import os

def main(rag_context_directory: str):
    """Function to upload rag context"""
    for filename in os.listdir(rag_context_directory):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(rag_context_directory, filename)
            print(f"Uploading file: {file_path}")
            response = pdf_upload(file_path, strategy='smart', session_id=RAG_CONTEXT_SESSION, local=True)
            print(f"Response: {response}")


if __name__ == "__main__":
    main("RagContext")