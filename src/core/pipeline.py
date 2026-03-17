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
        
        # 3. Normalize Text
        normalized_text = message_text.strip()
        
        # 4. Intent Detection (Rule + AI)
        from ..processing.intent_classifier import intent_classifier
        intent_data = await intent_classifier.classify(normalized_text)
        
        # 5. Intent Router
        from ..processing.intent_router import intent_router
        handler_type = await intent_router.route(intent_data, {"message": normalized_text})
        
        # 6. Memory Retrieval & 5. State Load
        memories = memory_manager.get_context(user_id, channel_id)
        state = character_state.load_state()
        
        # 7. Context Builder (Optimization)
        history_lines = []
        for uid, name, content in memories['short_term']:
            history_lines.append(f"{name}: {content}")
        context_summary = "\n".join(history_lines)
        
        # 8. Analyze Phase (Think Step)
        from ..processing.behavior_analyzer import behavior_analyzer
        analysis = await behavior_analyzer.analyze(normalized_text, username)
        
        # 9. Prompt Builder
        # Inject analysis into prompt builder logic (future polish needed)
        combined_context = f"{context_summary}\n\nANALYSIS OF CURRENT MESSAGE:\n{analysis['summary']}"
        system_prompt = prompt_builder.build_system_prompt(state, memories, combined_context)
        
        # 10. LLM Call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{username}: {normalized_text}"}
        ]
        response = await ai_client.generate_response(messages)
        
        # 11. State & 12. Memory Update
        state['last_interaction'] = normalized_text
        character_state.save_state(state)
        memory_manager.update_memory(channel_id, user_id, username, normalized_text, response)
        
        # 13. Reply (Returned to Cog)
        return response

pipeline = MessagePipeline()
