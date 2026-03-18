import time

class CooldownManager:
    def __init__(self, cooldown_seconds=20):
        self.cooldown_seconds = cooldown_seconds
        self.user_cooldowns = {} # user_id -> next_allow_time

    def is_on_cooldown(self, user_id):
        current_time = time.time()
        if user_id in self.user_cooldowns:
            if current_time < self.user_cooldowns[user_id]:
                return True
        return False

    def set_cooldown(self, user_id):
        self.user_cooldowns[user_id] = time.time() + self.cooldown_seconds

cooldown_manager = CooldownManager()
