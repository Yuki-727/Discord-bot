import asyncio
import logging
from ..ai.client import ai_client
from ..ai.prompt_builder import prompt_builder

logger = logging.getLogger(__name__)

class MessagePipeline:
    def __init__(self):
        pass

    async def run(self, channel_id, user_id, username, message_text, bot_id):
        from ..memory.memory_manager import memory_manager
        from ..state.character_state import character_state
        # 1. Receive & 2. Filter (Handled by Cog)
        
        # 3. Normalize Text
        normalized_text = message_text.strip()
        
        # 4. [NEW] Addressing Detection
        from ..processing.addressing_detector import addressing_detector
        recent_context = memory_manager.get_context(user_id, channel_id, query_text=None)
        address_check = await addressing_detector.check_addressing(normalized_text, username, recent_context, bot_id)
        
        # DEBUG LOGGING for User
        logger.info(f"DEBUG [Addressing]: User={username}, Text='{normalized_text[:50]}...', Confidence={address_check['confidence']:.2f}, Reason='{address_check['reason']}'")
        
        is_dm = channel_id == user_id 
        is_addressed = address_check['is_addressed'] or is_dm
        
        # 5. Intent Detection (Always run for memory extraction)
        from ..processing.intent_classifier import intent_classifier
        intent_data = await intent_classifier.classify(normalized_text)
        
        if not is_addressed:
            # Passive Read Mode: Log to memory but don't reply
            memory_manager.update_memory(channel_id, user_id, username, normalized_text, "[Overheard]")
            from ..memory.semantic_memory import semantic_memory
            asyncio.create_task(semantic_memory.extract_facts(user_id, username, normalized_text, "[Overheard]"))
            return None 
        
        # 6. Intent Router
        from ..processing.intent_router import intent_router
        handler_type = await intent_router.route(intent_data, {
            "message": normalized_text,
            "channel_id": channel_id,
            "user_id": user_id,
            "username": username
        })
        
        if handler_type and not str(handler_type).endswith("_handler"):
            return handler_type
        
        # 7. Memory Retrieval & State Load
        memories = memory_manager.get_context(user_id, channel_id, query_text=normalized_text)
        state = character_state.load_state()
        
        # 8. Context Builder with YOU labeling

        # 8. Analyze Phase (Think Step)
        from ..processing.behavior_analyzer import behavior_analyzer
        behavior_analysis = await behavior_analyzer.analyze(normalized_text, username, intent_data)
        logger.info(f"DEBUG [Analysis]: Action={behavior_analysis['action']}, Reasoning={behavior_analysis.get('reasoning', {}).get('best_action')}")
        
        # 9. Prompt Builder
        from ..ai.prompt_builder import prompt_builder
        reasoning = behavior_analysis.get('reasoning', {})
        analysis_summary = (
            f"SUMMARY: {behavior_analysis['summary']}\n"
            f"STRATEGY: {behavior_analysis['action']} -> {reasoning.get('best_action', 'reply')}\n"
            f"TONE: {reasoning.get('tone', 'neutral')}"
        )
        context_lines = []
        for uid, name, content in recent_context['short_term']:
            display_name = "YOU" if str(uid) == str(bot_id) or name.lower() == "nia" else name
            context_lines.append(f"{display_name}: {content}")
        context_history = "\n".join(context_lines)
        
        combined_context = f"{context_history}\n\nANALYSIS:\n{analysis_summary}"
        system_prompt = prompt_builder.build_system_prompt(state, recent_context, combined_context)
        
        # 10. Generation (LLM Call)
        from ..ai.client import ai_client
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{username}: {normalized_text}"}
        ]
        response = await ai_client.generate_response(messages)
        
        # 11. [NEW] Humanization Layer
        from ..processing.humanization_engine import humanization_engine
        
        # 11a. [NEW] Imperfections (Typos, Prefixes)
        if response:
            response = humanization_engine.apply_imperfections(response, behavior_analysis)

        # 12. State & 13. Memory Update
        character_state.update_from_interaction(behavior_analysis)
        logger.info(f"DEBUG [State Update]: Character state updated based on interaction.")
        memory_manager.update_memory(channel_id, user_id, username, normalized_text, response)
        
        # 14. [NEW] Background Semantic Extraction (Parallel)
        from ..memory.semantic_memory import semantic_memory
        asyncio.create_task(semantic_memory.extract_facts(user_id, username, normalized_text, response))
        
        # 15. Reply (Returned to Cog)
        return response

pipeline = MessagePipeline()
