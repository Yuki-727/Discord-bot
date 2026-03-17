import json
from ..core.database import db
from ..ai.client import ai_client

class SemanticMemory:
    def __init__(self):
        pass

    async def extract_facts(self, user_id, username, message_text, response_text):
        """
        AI analyzes the interaction to see if there's any permanent info worth saving.
        """
        prompt = f"""Review the following interaction between {username} and the AI.
User: "{message_text}"
AI: "{response_text}"

Identify if any permanent facts about the user or their preferences were revealed.
Example: "User likes pizza", "User's birthday is June 5th", "User is feeling sad about work".

Return ONLY a JSON array of objects, or an empty array [] if nothing important:
[
  {{
    "category": "preferences/personal/lore/status",
    "content": "The fact in one concise sentence",
    "importance": 1-5
  }}
]
"""
        try:
            raw_response = await ai_client.generate_response([{"role": "user", "content": prompt}])
            cleaned_json = raw_response.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
            
            facts = json.loads(cleaned_json)
            for fact in facts:
                self.save_fact(user_id, fact['category'], fact['content'], fact['importance'])
        except Exception as e:
            print(f"Error in semantic extraction: {e}")

    def save_fact(self, user_id, category, content, importance):
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO semantic_memory (user_id, category, content, importance)
                VALUES (?, ?, ?, ?)
            ''', (user_id, category, content, importance))
            conn.commit()

    def query_facts(self, user_id, query_text=None):
        """
        Retrieve facts for a user. In V1, we just get the most important/recent ones.
        """
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT category, content FROM semantic_memory 
                WHERE user_id = ? 
                ORDER BY importance DESC, timestamp DESC LIMIT 10
            ''', (user_id,))
            rows = cursor.fetchall()
            return "\n".join([f"- [{row[0]}] {row[1]}" for row in rows])

semantic_memory = SemanticMemory()
