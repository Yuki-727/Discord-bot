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

character_state = CharacterState()
