import asyncio
from ..ai.client import ai_client
from ..ai.prompt_builder import prompt_builder
from ..memory.memory_manager import memory_manager
from ..state.character_state import character_state

class MessagePipeline:
    def __init__(self):
        pass

    async def run(self, channel_id, user_id, username, message_text, bot_id):
        # 1. Receive & 2. Filter (Handled by Cog)
        
        # 3. Intent Detection (Placeholder)
        intent = "chat"
        
        # 4. Memory Retrieval
        memories = memory_manager.get_context(user_id, channel_id)
        
        # 5. State Load
        state = character_state.load_state()
        
        # 6. Context Builder (Optimization)
        history_lines = []
        for uid, name, content in memories['short_term']:
            history_lines.append(f"{name}: {content}")
        context_summary = "\n".join(history_lines)
        
        # 7. Prompt Builder
        system_prompt = prompt_builder.build_system_prompt(state, memories, context_summary)
        
        # 8. LLM Call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{username}: {message_text}"}
        ]
        response = await ai_client.generate_response(messages)
        
        # 9. State Update (Placeholder)
        state['last_interaction'] = message_text
        character_state.save_state(state)
        
        # 10. Memory Update
        memory_manager.update_memory(channel_id, user_id, username, message_text, response)
        
        # 11. Personality Filter (Placeholder)
        final_text = response
        
        # 12. Reply (Returned to Cog)
        return final_text

pipeline = MessagePipeline()
