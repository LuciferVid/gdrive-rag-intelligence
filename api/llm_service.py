import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_answer(self, query, context_chunks):
        """Generates an answer based on the provided context."""
        context_text = "\n\n".join([f"Source: {c['metadata']['file_name']}\nContent: {c['text']}" for c in context_chunks])
        
        prompt = f"""
        You are a helpful AI assistant. Answer the following question based ONLY on the provided context.
        If the answer is not in the context, say that you don't have enough information in your Google Drive.
        
        Context:
        {context_text}
        
        Question: {query}
        
        Instructions:
        - Be concise and accurate.
        - Cite your sources by mentioning the file names.
        - Return the answer in clear paragraphs.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
