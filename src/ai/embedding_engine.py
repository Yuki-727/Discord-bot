import os
import voyageai

class EmbeddingEngine:
    def __init__(self):
        self.api_key = os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            print("WARNING: VOYAGE_API_KEY not found in environment.")
        self.vo = voyageai.Client(api_key=self.api_key) if self.api_key else None
        self.model = "voyage-3-lite" # Lightweight and free-tier friendly

    def embed_text(self, text):
        """
        Converts text into a vector embedding using Voyage AI.
        """
        if not self.vo:
            return [0.0] * 512 # Fallback
            
        result = self.vo.embed([text], model=self.model)
        return result.embeddings[0]

    def embed_batch(self, texts):
        """
        Converts a list of texts into vector embeddings.
        """
        if not self.vo:
            return [[0.0] * 512 for _ in texts]
            
        result = self.vo.embed(texts, model=self.model)
        return result.embeddings

embedding_engine = EmbeddingEngine()
