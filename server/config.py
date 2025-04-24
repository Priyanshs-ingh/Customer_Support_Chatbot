import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

# Server Configuration
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Default Vite dev server
    "http://127.0.0.1:5173",
]