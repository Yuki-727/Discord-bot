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
{context_summary}

{memories.get('semantic', '')}

Maintain a natural, conversational tone. Do not mention you are an AI unless asked.
"""
        return prompt

prompt_builder = PromptBuilder()
