import os
import httpx
import json

def check_models():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
    if not api_key:
        print("Error: No API key found in environment variables.")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        with httpx.Client() as client:
            response = client.get(url)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print("Available Models:")
                for m in models:
                    name = m.get("name")
                    methods = m.get("supportedGenerationMethods", [])
                    if "embedContent" in methods:
                        print(f"  - {name} (Supports Embedding)")
            else:
                print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_models()
