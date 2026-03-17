import json
from ..ai.client import ai_client

class BehaviorAnalyzer:
    def __init__(self):
        pass

    async def analyze(self, message_text, username):
        """
        The "Analyze Phase" (Think step).
        Extracts: Who, What, Action.
        """
        prompt = f"""Analyze the following user message.
User: {username}
Message: "{message_text}"

Extract the following information:
1. Subject (Who): The person or entity being talked about.
2. Object (What): The thing or topic involved.
3. Action (Do): What is the user trying to achieve or what action is requested?

Return ONLY a JSON object:
{{
  "subject": "...",
  "object": "...",
  "action": "...",
  "summary": "Brief summary of intent"
}}
"""
        try:
            response_text = await ai_client.generate_response([{"role": "user", "content": prompt}])
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
            
            return json.loads(cleaned_json)
        except Exception:
            return {
                "subject": username,
                "object": "conversation",
                "action": "chatting",
                "summary": "Standard chat interaction"
            }

behavior_analyzer = BehaviorAnalyzer()
