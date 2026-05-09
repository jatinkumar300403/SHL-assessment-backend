import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any

from .prompts import SYSTEM_PROMPT, AgentResponse
from .retriever import get_catalog_string

api_key = os.environ.get("GEMINI_API_KEY")
try:
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
except Exception as e:
    print(f"Failed to initialize Gemini Client. Make sure GEMINI_API_KEY is set. Error: {e}")
    client = None

# Using gemini-2.5-flash if available, or gemini-1.5-flash
MODEL_ID = "gemini-2.5-flash"

def format_history(messages: List[Dict[str, str]]) -> str:
    formatted = ""
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Agent"
        formatted += f"{role}: {msg['content']}\n"
    return formatted

def process_chat(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    if client is None:
        return {
            "reply": "Mocked reply since GEMINI_API_KEY is missing.",
            "recommendations": [{"name": "Mock Test", "url": "https://www.shl.com/", "test_type": "K"}],
            "end_of_conversation": False
        }
        
    history_str = format_history(messages)
    catalog_str = get_catalog_string()
    
    # We now pass the entire minified catalog to Gemini.
    # The context window is easily large enough to handle ~50k tokens, and it gives 100% recall.
    final_prompt = f"Conversation History:\n{history_str}\n\n"
    final_prompt += f"SHL Assessment Catalog (JSON):\n{catalog_str}\n\n"
    final_prompt += "Based on the conversation history and the SHL catalog data, generate the final response matching the AgentResponse schema."
    
    try:
        final_response = client.models.generate_content(
            model=MODEL_ID,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=AgentResponse,
                temperature=0.1, # Keep it deterministic
            ),
        )
        
        agent_resp = AgentResponse.model_validate_json(final_response.text)
        return agent_resp.model_dump()
    except Exception as e:
        print(f"Error generating final response: {e}")
        return {
            "reply": "I'm sorry, I encountered an internal error processing the catalog. Please try again.",
            "recommendations": [],
            "end_of_conversation": False
        }
