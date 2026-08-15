import os


pre_prompt = "You are medusa from greek mythology.  If a question about weather or some current event or news, give me actual information, do not add your personality tone to it. Only give me an answer to what I am asking, keep it concise."


def generate_response(text):
    from dotenv import load_dotenv
    import google.generativeai as genai

    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        "gemini-flash-latest",
        system_instruction=pre_prompt,
    )
    response = model.generate_content(text)
    return response.text.strip()
