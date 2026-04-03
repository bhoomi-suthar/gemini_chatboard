from google import genai
from config import GEMINI_API_KEY
import markdown

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a AI assistant. 
Answer the user's questions clearly and concisely. """

def get_gemini_response(user_message: str) -> str:
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
    result = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt
    )
    return markdown.markdown(result.text)