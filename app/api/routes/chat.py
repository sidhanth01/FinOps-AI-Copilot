from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.rag_core import get_rag_chain # <-- Import the lazy-loading function

router = APIRouter()

# --- Pydantic Schemas for Chat ---
class ChatRequest(BaseModel):
    """Schema for the user's question."""
    question: str

class ChatResponse(BaseModel):
    """Schema for the AI's response."""
    answer: str
    sources: str
    status: str = "success"

@router.post("/ask", response_model=ChatResponse, tags=["AI"])
async def ask_ai_copilot(request: ChatRequest):
    """
    Handles natural language questions using the RAG system.
    RAG chain is initialized here on first request, making API startup safe.
    """
    
    # 1. Attempt to initialize/get the RAG chain
    rag_chain, rag_error = get_rag_chain()

    if rag_error:
        # 2. Fallback path if RAG system failed to initialize
        # Returns a helpful error message to the user without crashing the endpoint (500)
        print(f"RAG System Offline: {rag_error}")
        return ChatResponse(
            answer=f"AI System is temporarily offline. Reason: {rag_error}. Please ensure Ollama is running and the 'mistral' model is pulled.",
            sources="N/A",
            status="error"
        )
    
    # 3. Invoke the RAG chain
    try:
        # NOTE: We use .invoke() for a synchronous call in this simple demo
        response = rag_chain.invoke({"input": request.question})
        
        # Format sources from the retrieved documents
        sources = ", ".join(
            [doc.metadata.get("source", "Unknown Source") for doc in response['context']]
        )
        
        return ChatResponse(
            answer=response['answer'],
            sources=sources,
            status="success"
        )
        
    except Exception as e:
        # Catch any failure during the LLM call itself (e.g., connection drop)
        print(f"Error invoking RAG chain: {e}")
        # Raising an HTTPException ensures the client gets a proper error status.
        raise HTTPException(
            status_code=500, 
            detail=f"Internal RAG Chain Error. Please check Ollama server logs. Error: {type(e).__name__}: {e}"
        )