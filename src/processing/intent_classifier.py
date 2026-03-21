import json
import re
from ..ai.client import ai_client

class IntentClassifier:
    def __init__(self):
        # Layer 1: Rules (Fast)
        self.rules = {
            "command": [r"^!", r"^/"],
            "casual_chat": [r"hi", r"hello", r"chào", r"tạm biệt", r"bye"],
        }
        self.possible_intents = [
            "incomplete_fragment", "casual_chat", "question", "memory_query", 
            "command", "story_request", "roleplay", "emotional_support", "system_control"
        ]

    def _rule_detect(self, text):
        raw_text = text.lower().strip()
        for intent, patterns in self.rules.items():
            for pattern in patterns:
                if re.search(pattern, raw_text):
                    return {"intent": intent, "confidence": 1.0, "source": "rule"}
        return None

    async def classify(self, text):
        # Layer 1: Rules
        rule_result = self._rule_detect(text)
        if rule_result:
            return rule_result

        # Layer 2: AI Classification
        prompt = f"""Classify the intent of the following user message for an AI assistant.
Message: "{text}"

Possible intents: {", ".join(self.possible_intents)}

Return ONLY a JSON object with this exact structure:
{{
  "intent": "string",
  "confidence": float
}}
"""
        try:
            response_text = await ai_client.generate_response([{"role": "user", "content": prompt}])
            # Clean response text in case of markdown or preamble
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
            
            data = json.loads(cleaned_json)
            data["source"] = "ai"
            return data
        except Exception:
            # Layer 3: Fallback
            return {"intent": "casual_chat", "confidence": 0.5, "source": "fallback"}

intent_classifier = IntentClassifier()
