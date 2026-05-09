import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Dict, Any

from .prompts import SYSTEM_PROMPT, INTENT_PROMPT, SearchIntent, AgentResponse
from .retriever import get_collection

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
    
    # Step 1: Intent Classification & Query Generation
    intent_prompt = f"{INTENT_PROMPT}\n\nConversation History:\n{history_str}"
    
    try:
        intent_response = client.models.generate_content(
            model=MODEL_ID,
            contents=intent_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SearchIntent,
            ),
        )
        # Parse the JSON response
        intent_data = SearchIntent.model_validate_json(intent_response.text)
    except Exception as e:
        print(f"Error in intent classification: {e}")
        # Fallback
        intent_data = SearchIntent(
            is_vague=True, 
            is_off_topic=False, 
            is_comparison=False, 
            search_query="", 
            reasoning="Fallback due to error"
        )
        
    print(f"Intent: {intent_data}")
    
    retrieved_context = ""
    if intent_data.is_off_topic:
        pass # No need to search
    elif intent_data.is_vague and not intent_data.is_comparison:
        pass # No need to search
    else:
        # Step 2: Search ChromaDB
        collection = get_collection()
        query = intent_data.search_query
        if not query:
            query = messages[-1]["content"]
            
        results = collection.query(
            query_texts=[query],
            n_results=15
        )
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            
            retrieved_context = "Retrieved Assessments Catalog Data:\n\n"
            for i in range(len(docs)):
                retrieved_context += f"--- Assessment {i+1} ---\n"
                retrieved_context += f"{docs[i]}\n"
                retrieved_context += f"URL: {metas[i].get('url', '')}\n"
                retrieved_context += f"Test Type (Keys shortcut): {metas[i].get('test_type', 'U')}\n\n"
                
    # Step 3: Generate Final Response
    final_prompt = f"Conversation History:\n{history_str}\n\n{retrieved_context}\n\n"
    final_prompt += "Based on the above conversation history and the retrieved catalog data (if any), generate the final response matching the AgentResponse schema."
    
    try:
        final_response = client.models.generate_content(
            model=MODEL_ID,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=AgentResponse,
                temperature=0.2, # Keep it deterministic
            ),
        )
        
        agent_resp = AgentResponse.model_validate_json(final_response.text)
        return agent_resp.model_dump()
    except Exception as e:
        print(f"Error generating final response: {e}")
        return {
            "reply": "I'm sorry, I encountered an internal error. Please try again.",
            "recommendations": [],
            "end_of_conversation": False
        }
