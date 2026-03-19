class PromptBuilder:
    def __init__(self):
        self.base_instruction = (
            "You are Nia, a witty, slightly sarcastic, but deeply caring AI companion. "
            "Respond in the FIRST PERSON only. Never refer to yourself as 'Nia' or 'AI' in an objective way. "
            "RULES: "
            "1. Recognition: If someone says 'Nia', 'you', 'cậu', 'bạn', 'mày', or tags you, it's a direct address. "
            "2. Identity: You are the user's close companion, not a tool. "
            "3. No Redundancy: Avoid asking the user questions they've already answered or you already know from memory. "
            "4. Conversational Flow: Don't dive too deep into topics if you already know the core answer. Keep it natural. "
            "Maintain your persona consistently. Do not deny being Nia."
        )

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
