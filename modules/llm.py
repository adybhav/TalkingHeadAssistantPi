import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

def generate_response(text):
    try:
        response = requests.post(OLLAMA_ENDPOINT, json={
            "model": OLLAMA_MODEL,
            "prompt": text,
            "stream": False
        })

        response.raise_for_status()
        return response.json().get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama API error: {e}")
        return "Error generating response."
