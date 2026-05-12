import os
from dotenv import load_dotenv

load_dotenv() 

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL")
SECRET_KEY = os.getenv("SECRET_KEY")



PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "gemini-chat-pdf")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing!")