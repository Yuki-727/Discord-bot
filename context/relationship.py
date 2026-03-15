from utils.database import Database

class RelationshipModule:
    def __init__(self, db: Database):
        self.db = db

    def get_affection_info(self, user_id):
        affection = self.db.get_affection(user_id)
        
        closeness = "Stranger"
        if affection > 50: closeness = "Acquaintance"
        if affection > 200: closeness = "Good Friend"
        if affection > 500: closeness = "Very Close"
        
        return {
            "score": affection,
            "level": closeness
        }

    def update_relationship(self, user_id, message_content):
        # Sentiment-based affection logic
        positive_triggers = ["good", "smart", "love", "like", "awesome", "cute", "cool", "nice"]
        negative_triggers = ["stupid", "hate", "ugly", "annoying", "bad", "mean"]
        
        change_val = 0
        message_lower = message_content.lower()
        for word in positive_triggers:
            if word in message_lower: 
                change_val += 2
        for word in negative_triggers:
            if word in message_lower: 
                change_val -= 3
            
        if change_val != 0:
            self.db.update_affection(user_id, change_val)
            return change_val
        return 0
