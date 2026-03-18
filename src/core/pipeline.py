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
        
        # 4. [NEW] Addressing Detection
        from ..processing.addressing_detector import addressing_detector
        # Get last 10 for context lookback
        recent_context = memory_manager.get_context(user_id, channel_id, query_text=None)['short_term']
        address_check = await addressing_detector.check_addressing(normalized_text, username, recent_context, bot_id)
        
        is_dm = channel_id == user_id # Simple DM check
        is_addressed = address_check['is_addressed'] or is_dm
        
        # 5. Intent Detection (Always run for memory extraction)
        from ..processing.intent_classifier import intent_classifier
        intent_data = await intent_classifier.classify(normalized_text)
        
        if not is_addressed:
            # Passive Read Mode: Log to memory but don't reply
            memory_manager.update_memory(channel_id, user_id, username, normalized_text, "[Overheard]")
            # Still extract facts in background
            from ..memory.semantic_memory import semantic_memory
            asyncio.create_task(semantic_memory.extract_facts(user_id, username, normalized_text, "[Overheard]"))
            return None # Signal to Cog to stay silent
        
        # 6. Intent Router
        from ..processing.intent_router import intent_router
        handler_type = await intent_router.route(intent_data, {
            "message": normalized_text,
            "channel_id": channel_id,
            "user_id": user_id,
            "username": username
        })
        
        # If the router returned a direct response (e.g., from an internal command), return it now.
        if handler_type and not str(handler_type).endswith("_handler"):
            return handler_type
        
        # 6. Memory Retrieval & 5. State Load
        memories = memory_manager.get_context(user_id, channel_id, query_text=normalized_text)
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
        
        # 13. [NEW] Background Semantic Extraction & Summarization (Parallel)
        from ..memory.semantic_memory import semantic_memory
        asyncio.create_task(semantic_memory.extract_facts(user_id, username, normalized_text, response))
        asyncio.create_task(memory_manager.summarize_history(channel_id))
        
        # 14. Reply (Returned to Cog)
        return response

pipeline = MessagePipeline()
