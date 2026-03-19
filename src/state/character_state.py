import json
from ..core.database import db

class CharacterState:
    def __init__(self):
        self.default_state = {
            "mood": "neutral",
            "energy": 100,
            "current_topic": None,
            "last_interaction": None
        }
    
    def load_state(self):
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM character_state WHERE key = "current"')
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return self.default_state

    def save_state(self, state_dict):
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO character_state (key, value)
                VALUES ("current", ?)
            ''', (json.dumps(state_dict),))
            conn.commit()

    def update_from_interaction(self, behavior_analysis):
        """
        Updates NIA's internal state based on the AI's behavior analysis.
        """
        state = self.load_state()
        
        # 1. Topic update
        state["current_topic"] = behavior_analysis.get("summary", state.get("current_topic"))
        
        # 2. Energy decay
        state["energy"] = max(0, state.get("energy", 100) - 1)
        
        # 3. Mood adjustment based on Tone
        reasoning = behavior_analysis.get("reasoning", {})
        tone = reasoning.get("tone", "neutral").lower()
        
        if "happy" in tone or "excited" in tone:
            state["mood"] = "happy"
        elif "angry" in tone or "annoyed" in tone:
            state["mood"] = "annoyed"
        elif "sad" in tone:
            state["mood"] = "thoughtful"
        
        self.save_state(state)

character_state = CharacterState()
