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
            
        try:
            result = self.vo.embed([text], model=self.model)
            return result.embeddings[0]
        except Exception as e:
            print(f"ERROR: Voyage Embedding failed: {e}")
            return [0.0] * 512

    def embed_batch(self, texts):
        """
        Converts a list of texts into vector embeddings.
        """
        if not self.vo:
            return [[0.0] * 512 for _ in texts]
            
        try:
            result = self.vo.embed(texts, model=self.model)
            return result.embeddings
        except Exception as e:
            print(f"ERROR: Voyage Batch Embedding failed: {e}")
            return [[0.0] * 512 for _ in texts]

    @staticmethod
    def cosine_similarity(v1, v2):
        from math import sqrt
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sqrt(sum(a * a for a in v1))
        magnitude2 = sqrt(sum(b * b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

embedding_engine = EmbeddingEngine()
