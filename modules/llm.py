import json
import datetime
import re
import requests
from ddgs import DDGS

OLLAMA_ENDPOINT = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma4:e2b-it-qat"

# Medusa persona injected as a strict system-level instruction
pre_prompt = "You are medusa from greek mythology.  If a question about weather or some current event or news, give me actual information, do not add your personality tone to it. Only give me an answer to what I am asking, keep it concise."

tools_definition = [{
    'type': 'function',
    'function': {
        'name': 'execute_web_search',
        'description': 'Search the internet for real-time information, weather, recent events, or live data.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'The query to search for'}
            },
            'required': ['query']
        }
    }
}]


def execute_web_search(query: str) -> str:
    """Uses a local DuckDuckGo scraper to fetch live data instantly."""
    if "today" in query.lower():
        # Generates a string like "August 01 2026"
        formatted_date = datetime.date.today().strftime("%B %d %Y")

        # Word-boundary regex replacement (case-insensitive)
        query = re.sub(r'\btoday\b', formatted_date, query, flags=re.IGNORECASE)
        print(f"📅 [Temporal Grounding] Updated query to: '{query}'")
    print(f"🔍 [Local Web Search] Querying: '{query}'")
    try:
        results = DDGS().text(query, max_results=3)
        context_snippets = []

        for item in results:
            # We combine the title and body snippet of the search result
            context_snippets.append(f"Source: {item.get('title')} | Content: {item.get('body')}")

        return "\n".join(context_snippets) if context_snippets else "No search results found."
    except Exception as e:
        return f"Internet search failed: {str(e)}"


def generate_response(text):
    try:
        messages = [
            {"role": "system", "content": pre_prompt},
            {"role": "user", "content": text}
        ]
        ollama_options = {
            "num_gpu": 0
        }
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "tools": tools_definition,
            "stream": False,
            "think": False,
            "options": ollama_options # Keeps Gemma fast and ensures it outputs the tool call correctly
        }

        response = requests.post(OLLAMA_ENDPOINT, json=payload)
        response.raise_for_status()
        response_json = response.json()
        message_out = response_json.get("message", {})

        if message_out.get("tool_calls"):
            for tool_call in message_out["tool_calls"]:
                if tool_call["function"]["name"] == "execute_web_search":
                    args = tool_call["function"]["arguments"]
                    if isinstance(args, str):
                        args = json.loads(args)

                    # Execute the local Python web search
                    search_results = execute_web_search(args["query"])
                    print(f"✅ Found {len(search_results.splitlines())} results from the web.")

                    messages.append(message_out)
                    messages.append({
                        "role": "tool",
                        "name": "execute_web_search",
                        "content": search_results
                    })

                    final_payload = {
                        "model": OLLAMA_MODEL,
                        "messages": messages,
                        "stream": False,
                        "think": False,
                        "options": ollama_options
                    }
                    final_response = requests.post(OLLAMA_ENDPOINT, json=final_payload)
                    final_response.raise_for_status()
                    return final_response.json().get("message", {}).get("content", "").strip()

        return message_out.get("content", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama API error: {e}")
        return "Error generating response."


if __name__ == "__main__":
    print(generate_response("Give me the top 2 US news updates from today"))