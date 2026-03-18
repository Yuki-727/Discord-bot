class CommandModule:
    def __init__(self):
        self.commands = {
            "status": self.get_status,
            "reset_state": self.reset_state,
            "read": self.register_channel,
        }

    async def register_channel(self, context):
        from ..core.database import db
        channel_id = context.get('channel_id')
        if not channel_id:
            return "Error: No channel context."
        
        db.add_monitored_channel(channel_id)
        return f"Noted! I will now pay attention to everything in this channel (Passive Reading enabled)."

    async def execute(self, message_text, context):
        """
        Executes internal bot commands.
        """
        # Extract the first word as the command
        parts = message_text.replace("!", "").replace("/", "").split()
        if not parts:
            return "No command provided."
            
        cmd_name = parts[0].lower()
        handler = self.commands.get(cmd_name)
        
        if handler:
            return await handler(context)
        return "Command not recognized by internal system."

    async def get_status(self, context):
        from ..state.character_state import character_state
        state = character_state.load_state()
        return f"System Status: ONLINE\nMood: {state.get('mood')}\nEnergy: {state.get('energy')}%"

    async def reset_state(self, context):
        from ..state.character_state import character_state
        character_state.save_state(character_state.default_state)
        return "Character state has been reset to defaults."

command_module = CommandModule()
