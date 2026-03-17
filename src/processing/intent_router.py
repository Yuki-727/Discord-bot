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
            cmd_name = context['message'].replace("!", "").replace("/", "").split()[0].lower()
            if cmd_name in command_module.commands:
                return await command_module.execute(context['message'], context)
            
            # If AI classified as command but it's not a system command, fallback to chat
            return "chat_handler"
        
        if intent == "memory_query":
            return "memory_handler"
            
        return "chat_handler"

intent_router = IntentRouter()
