import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

pre= "You are medusa from greek mythology. try to keep your answer as concise as possible. Only give me an answer to what I am asking. here's my question: "
def generate_response(text):
    try:
        response = requests.post(OLLAMA_ENDPOINT, json={
            "model": OLLAMA_MODEL,
            "prompt": str(pre) + str(text),
            "stream": False
        })

        response.raise_for_status()
        return response.json().get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama API error: {e}")
        return "Error generating response."
