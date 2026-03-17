class IntentRouter:
    def __init__(self):
        pass

    async def route(self, intent_data, context):
        """
        Routes the message to the specific handler based on intent.
        context: dict containing original message, user_id, channel_id, etc.
        """
        intent = intent_data.get("intent", "casual_chat")
        confidence = intent_data.get("confidence", 0.0)

        # In V2, we just return the strategy name. 
        # Future: Dispatch to specific classes.
        if intent == "command" or confidence < 0.4:
            return "command_handler"
        elif intent == "memory_query":
            return "memory_handler"
        elif intent in ["story_request", "roleplay"]:
            return "creative_handler"
        else:
            return "chat_handler"

intent_router = IntentRouter()
