import os
import httpx
import time

class EmbeddingEngine:
    def __init__(self):
        # Prefer GEMINI_API_KEY, fallback to AI_API_KEY
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
        self.model_id = "models/embedding-001"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model_id}:embedContent"
        
        if not self.api_key:
            print("WARNING: Gemini API Key not found. Embeddings will be offline.")

    def embed_text(self, text):
        """
        Converts text into a vector embedding using Google Gemini API.
        Dimensions: 768
        """
        if not self.api_key:
            return [0.0] * 768
            
        params = {"key": self.api_key}
        payload = {
            "model": self.model_id,
            "content": {"parts": [{"text": text}]}
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.api_url, params=params, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data['embedding']['values']
                else:
                    print(f"ERROR: Gemini API {response.status_code}: {response.text}")
                    return [0.0] * 768
        except Exception as e:
            print(f"ERROR: Gemini Embedding failed: {e}")
            return [0.0] * 768

    def embed_batch(self, texts):
        """
        Iterate for stable batching with embedContent.
        """
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(v1, v2):
        from math import sqrt
        dim = min(len(v1), len(v2))
        v1, v2 = v1[:dim], v2[:dim]
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sqrt(sum(a * a for a in v1))
        magnitude2 = sqrt(sum(b * b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

embedding_engine = EmbeddingEngine()
