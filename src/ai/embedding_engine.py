from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingEngine:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text):
        """
        Converts text into a vector embedding.
        """
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts):
        """
        Converts a list of texts into a list of vector embeddings.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

embedding_engine = EmbeddingEngine()
