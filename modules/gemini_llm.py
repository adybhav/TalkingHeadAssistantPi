import os

from dotenv import load_dotenv
import google.generativeai as genai


pre_prompt = "You are medusa from greek mythology.  If a question about weather or some current event or news, give me actual information, do not add your personality tone to it. Only give me an answer to what I am asking, keep it concise."

# Configure once at import time instead of on every request.
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-flash-latest",
    system_instruction=pre_prompt,
)


def generate_response(text):
    response = model.generate_content(text)
    return response.text.strip()
