def generate_response(text, use_ollama=True):
    if use_ollama:
        from modules.llm import generate_response as generate_ollama_response

        return generate_ollama_response(text)

    from modules.gemini_llm import generate_response as generate_gemini_response

    return generate_gemini_response(text)
