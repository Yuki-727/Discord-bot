import groq
from ..core.config import config

class AIClient:
    def __init__(self):
        self.client = groq.AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = config.AI_MODEL

    async def generate_response(self, messages):
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to AI: {str(e)}"

ai_client = AIClient()
