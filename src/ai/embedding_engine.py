import os
import httpx
import time

class EmbeddingEngine:
    def __init__(self):
        self.api_key = os.getenv("HF_TOKEN")
        self.model_id = "sentence-transformers/all-MiniLM-L6-v2"
        # Standard Inference API endpoint
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        
        if not self.api_key:
            print("WARNING: HF_TOKEN not found in environment. Embeddings will be offline.")

    def embed_text(self, text):
        """
        Converts text into a vector embedding using Hugging Face Inference API.
        Dimensions: 384
        """
        if not self.api_key:
            return [0.0] * 384
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.api_url, headers=headers, json={"inputs": [text]})
                if response.status_code == 200:
                    return response.json()[0]
                else:
                    print(f"ERROR: HuggingFace API {response.status_code}: {response.text}")
                    return [0.0] * 384
        except Exception as e:
            print(f"ERROR: HuggingFace Embedding failed: {e}")
            return [0.0] * 384

    def embed_batch(self, texts):
        """
        Converts a list of texts into vector embeddings using Hugging Face Inference API.
        """
        if not self.api_key:
            return [[0.0] * 384 for _ in texts]
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(self.api_url, headers=headers, json={"inputs": texts})
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"ERROR: HuggingFace Batch API {response.status_code}: {response.text}")
                    return [[0.0] * 384 for _ in texts]
        except Exception as e:
            print(f"ERROR: HuggingFace Batch failed: {e}")
            return [[0.0] * 384 for _ in texts]

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
