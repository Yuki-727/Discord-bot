import json
import chromadb
from chromadb.config import Settings
import os
from ..ai.embedding_engine import embedding_engine
from ..ai.client import ai_client

class SemanticMemory:
    def __init__(self, db_path="./data/chroma_db"):
        # Ensure data directory exists
        os.makedirs(db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="user_facts",
            metadata={"hnsw:space": "cosine"} # Use cosine similarity for better semantic matching
        )

    async def extract_facts(self, user_id, username, message_text, response_text):
        """
        AI analyzes the interaction to see if there's any permanent info worth saving.
        """
        prompt = f"""Review the following interaction between {username} and the AI.
User: "{message_text}"
AI: "{response_text}"

Identify if any permanent facts about the user or their preferences were revealed.
Example: "User likes pizza", "User's birthday is June 5th", "User is feeling sad about work".

Return ONLY a JSON array of objects, or an empty array [] if nothing important:
[
  {{
    "category": "preferences/personal/lore/status",
    "content": "The fact in one concise sentence",
    "importance": 1-5
  }}
]
"""
        try:
            raw_response = await ai_client.generate_response([{"role": "user", "content": prompt}])
            cleaned_json = raw_response.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[-1].split("```")[0].strip()
            
            facts = json.loads(cleaned_json)
            for fact in facts:
                self.save_fact(user_id, fact['category'], fact['content'], fact['importance'])
        except Exception as e:
            print(f"Error in semantic extraction: {e}")

    def save_fact(self, user_id, category, content, importance):
        """
        Saves a fact into ChromaDB with its embedding.
        """
        vector = embedding_engine.embed_text(content)
        
        # Unique ID for each fact
        fact_id = f"{user_id}_{hash(content)}_{os.getpid()}"
        
        self.collection.add(
            ids=[fact_id],
            embeddings=[vector],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "category": category,
                "importance": importance
            }]
        )

    def query_facts(self, user_id, query_text):
        """
        Retrieve facts for a user using Vector Search.
        """
        if not query_text:
            return "No query provided for memory search."

        # Convert query to vector
        query_vector = embedding_engine.embed_text(query_text)
        
        # Search the collection
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=5,
            where={"user_id": user_id}
        )
        
        if not results['documents'][0]:
            return "No matching memories found."
            
        facts = results['documents'][0]
        formatted_facts = "\n".join([f"- {fact}" for fact in facts])
        return formatted_facts

semantic_memory = SemanticMemory()
