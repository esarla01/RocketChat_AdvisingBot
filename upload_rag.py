from utils import RAG_CONTEXT_SESSION
from llmproxy import pdf_upload, text_upload
import os

def main_txt(rag_context_directory: str):
    """Function to upload RAG context from text files"""
    for filename in os.listdir(rag_context_directory):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(rag_context_directory, filename)
            print(f"Uploading file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as file:
                text_content = file.read()
            response = text_upload(
                text=text_content,
                strategy='fixed',
                session_id=RAG_CONTEXT_SESSION,
                local=True
            )
            print(f"Response: {response}")

def main_pdf(rag_context_directory: str):
    """Function to upload rag context"""
    for filename in os.listdir(rag_context_directory):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(rag_context_directory, filename)
            print(f"Uploading file: {file_path}")
            response = pdf_upload(file_path, strategy='smart', session_id=RAG_CONTEXT_SESSION, local=True)
            print(f"Response: {response}")


if __name__ == "__main__":
    main_txt("RagContext")
    main_pdf("RagContext")