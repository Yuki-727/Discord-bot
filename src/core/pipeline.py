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
        
        # If the router returned a direct response (e.g., from an internal command), return it now.
        if handler_type and not str(handler_type).endswith("_handler"):
            return handler_type
        
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
        analysis = await behavior_analyzer.analyze(normalized_text, username, intent_data)
        
        # 9. Prompt Builder
        reasoning = analysis.get('reasoning', {})
        analysis_summary = (
            f"SUMMARY: {analysis['summary']}\n"
            f"STRATEGY: {analysis['action']} -> {reasoning.get('best_action', 'reply')}\n"
            f"TONE: {reasoning.get('tone', 'neutral')}"
        )
        combined_context = f"{context_summary}\n\nANALYSIS:\n{analysis_summary}"
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
        
        # 13. [NEW] Background Semantic Extraction (Parallel)
        from ..memory.semantic_memory import semantic_memory
        asyncio.create_task(semantic_memory.extract_facts(user_id, username, normalized_text, response))
        
        # 14. Reply (Returned to Cog)
        return response

pipeline = MessagePipeline()
