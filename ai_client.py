import httpx
import config

class AIClient:
    def __init__(self):
        self.api_key = config.AI_API_KEY
        self.base_url = config.AI_API_BASE_URL
        self.model = config.AI_MODEL

    async def generate_response(self, messages: list) -> str:
        if not self.api_key:
            print("ERROR: AI_API_KEY is missing in AIClient!", flush=True)
            return "Error: AI_API_KEY is missing. Please check your Railway environment variables."
            
        # Clean the key: remove whitespace, quotes, and 'Bearer ' if already present
        api_key_clean = self.api_key.strip().strip('"').strip("'")
        if api_key_clean.lower().startswith("bearer "):
            api_key_clean = api_key_clean[7:].strip()

        print(f"DEBUG_V2: Key length={len(api_key_clean)}, Model={self.model}, BaseURL={self.base_url}", flush=True)
        
        headers = {
            "Authorization": f"Bearer {api_key_clean}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages
        }

        base_url = self.base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "Error: Received an empty or unexpected response from the AI API."
            
            except httpx.TimeoutException:
                return "Error: The request to the AI API timed out. Please try again later."
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                print(f"API Error ({e.response.status_code}): {error_detail}")
                return f"Error: API returned an HTTP error status: {e.response.status_code}. Detail: {error_detail[:100]}"
            except Exception as e:
                return f"Error: An unexpected error occurred: {str(e)}"
