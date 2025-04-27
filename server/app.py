from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core import run_customer_support
from config import ALLOWED_ORIGINS
from components.utils import DataExtract
from datetime import datetime

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database = "nebula"

class ChatRequest(BaseModel):
    message: str

class DataRequest(BaseModel):
    records: list
    database: str
    collection: str

@app.post("/api/create-user")
async def insert_data(request: DataRequest):
    try:
        collection = "users"
        data_extractor = DataExtract(database=database, collection=collection)
        inserted_count = data_extractor.insert_data_mongodb(request.records)
        return {"message": f"Successfully inserted {inserted_count} records"}
    except Exception as e:
        print(f"Error in insert-data endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        if not request.message:
            raise ValueError("Empty message received")
            
        result = run_customer_support(request.message)
        if not result:
            raise ValueError("No result from workflow")
            
        chat_data = {
            "message": request.message,
            "response": result,
            "timestamp": datetime.utcnow()
        }
        data_extractor = DataExtract(database=database, collection="chats")
        data_extractor.insert_data_mongodb(chat_data)
            
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