from collections import deque

class ChatMemory:
    def __init__(self, limit=10):
        self.history = {}
        self.limit = limit

    def add_message(self, user_id, role, content):
        if user_id not in self.history:
            self.history[user_id] = deque(maxlen=self.limit)
        self.history[user_id].append({"role": role, "content": content})

    def get_history(self, user_id):
        return list(self.history.get(user_id, []))

    def clear_history(self, user_id):
        if user_id in self.history:
            self.history[user_id].clear()
