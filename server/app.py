from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core import run_customer_support
from config import ALLOWED_ORIGINS

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        print(f"Received message: {request.message}")  # Debug logging
        if not request.message:
            raise ValueError("Empty message received")
            
        result = run_customer_support(request.message)
        if not result:
            raise ValueError("No result from workflow")
            
        print(f"Sending response: {result}")  # Debug logging
        return result
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")  # Error logging
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/health")
async def health():
    
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
