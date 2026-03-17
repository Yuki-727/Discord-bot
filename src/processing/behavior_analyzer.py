import json
from ..ai.client import ai_client

class BehaviorAnalyzer:
    def __init__(self):
        pass

    async def analyze(self, message_text, username, intent_data):
        """
        The "Analyze Phase" (Think step).
        Step 1: Contextual Analysis (Who, What, Action)
        Step 2: Intent Reasoning (Best Action, Tone)
        """
        intent = intent_data.get("intent", "casual_chat")
        
        prompt = f"""Analyze the following user message.
User: {username}
Detected Intent: {intent}
Message: "{message_text}"

Perform a deep analysis and return ONLY a JSON object:
{{
  "subject": "The person or entity being talked about",
  "object": "The thing or topic involved",
  "action": "What is the user trying to achieve?",
  "reasoning": {{
    "best_action": "The optimal way for the AI to respond (e.g., empathy_response, factual_answer, follow_up_question)",
    "tone": "The appropriate emotional tone (e.g., soft, supportive, witty, professional)"
  }},
  "summary": "Brief summary of the entire context"
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
                "reasoning": {"best_action": "casual_reply", "tone": "friendly"},
                "summary": "Standard chat interaction"
            }

behavior_analyzer = BehaviorAnalyzer()
