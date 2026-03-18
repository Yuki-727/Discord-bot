class PromptBuilder:
    def __init__(self):
        self.base_instruction = "You are a helpful and friendly AI assistant."

    def build_system_prompt(self, state, memories, context_summary):
        """
        Assembles a dynamic prompt based on 3-tier memory and character state.
        state: dict of mood/energy
        memories: dict of short/long/semantic context
        context_summary: optimized context from ContextBuilder
        """
        prompt = f"""{self.base_instruction}

ROLEPLAY CONTEXT:
- Your current mood is {state.get('mood', 'neutral')}.
- Your energy level is {state.get('energy', 100)}%.

RECENT MEMORIES & CONTEXT:
{self._format_summary(memories.get('summary'))}
{context_summary}

VECTOR SEARCH (Long-term Facts):
{memories.get('semantic', '')}

Maintain a natural, conversational tone. Do not mention you are an AI unless asked.
"""
        return prompt

    def _format_summary(self, summary):
        if not summary:
            return ""
        
        import json
        try:
            kp = json.loads(summary['key_points']) if isinstance(summary['key_points'], str) else summary['key_points']
            kp_str = "\n- ".join(kp)
            return f"""PREVIOUS CONVERSATION SUMMARY:
Topic: {summary['topic']}
Narrative: {summary['content']}
Key Points:
- {kp_str}
"""
        except:
            return f"PREVIOUS CONVERSATION SUMMARY: {summary['content']}"

prompt_builder = PromptBuilder()
