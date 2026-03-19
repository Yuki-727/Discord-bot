import os
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingEngine:
    def __init__(self):
        # Using a very lightweight local model (approx 80MB)
        # Dimensions: 384
        try:
            self.model_name = "all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)
            print(f"INFO: Local Embedding Engine initialized with {self.model_name}")
        except Exception as e:
            print(f"ERROR: Local Embedding initialization failed: {e}")
            self.model = None

    def embed_text(self, text):
        """
        Converts text into a vector embedding locally.
        """
        if not self.model:
            return [0.0] * 384 # Fallback
            
        try:
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            print(f"ERROR: Local Embedding failed: {e}")
            return [0.0] * 384

    def embed_batch(self, texts):
        """
        Converts a list of texts into vector embeddings locally.
        """
        if not self.model:
            return [[0.0] * 384 for _ in texts]
            
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            print(f"ERROR: Local Batch Embedding failed: {e}")
            return [[0.0] * 384 for _ in texts]

    @staticmethod
    def cosine_similarity(v1, v2):
        from math import sqrt
        # Ensure vectors have same dimension
        dim = min(len(v1), len(v2))
        v1, v2 = v1[:dim], v2[:dim]
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sqrt(sum(a * a for a in v1))
        magnitude2 = sqrt(sum(b * b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

embedding_engine = EmbeddingEngine()
