class IntentRouter:
    def __init__(self):
        pass

    async def route(self, intent_data, context):
        """
        Routes the message to the specific handler based on intent.
        """
        intent = intent_data.get("intent", "casual_chat")
        confidence = intent_data.get("confidence", 0.0)

        if intent == "command":
            from .command_module import command_module
            # Handle as internal command
            return await command_module.execute(context['message'], context)
        
        if intent == "memory_query":
            return "memory_handler"
            
        return "chat_handler"

intent_router = IntentRouter()
