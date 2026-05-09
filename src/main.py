from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from src.agent import process_chat
from src.retriever import initialize_db

app = FastAPI(title="SHL Assessment Agent API")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

@app.on_event("startup")
async def startup_event():
    # Initialize the database on startup
    initialize_db()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        messages = [msg.model_dump() for msg in request.messages]
        response = process_chat(messages)
        return response
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
