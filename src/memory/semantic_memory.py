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
        try:
            self.collection = self.client.get_or_create_collection(
                name="user_facts",
                metadata={"hnsw:space": "cosine"}
            )
            # Peek to trigger a potential dimension check error immediately
            if self.collection.count() > 0:
                self.collection.peek()
        except Exception as e:
            if "dimension" in str(e).lower() or "Invalid" in str(e):
                print(f"DEBUG: Dimension mismatch or corrupted collection ({e}). Recreating...")
                try:
                    self.client.delete_collection("user_facts")
                except:
                    pass
                self.collection = self.client.create_collection(
                    name="user_facts",
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                raise e

    async def extract_facts(self, user_id, username, message_text, response_text):
        """
        AI analyzes the interaction (70% weight on User Message, 30% on Bot Response).
        Extracts facts in a unified JSON format.
        """
        prompt = f"""Analyze this interaction. 
Weight: 70% on User's Message ("{message_text}"), 30% on AI's Response ("{response_text}").

Goal: Identify 'memorable' facts about the user. Ignore common/obvious info.
Categories: identity, preferences, relationship, goals, fact, constraints.

Return ONLY a JSON array of objects:
[
  {{
    "type": "category_name",
    "value": "concise fact",
    "confidence": 0.0-1.0,
    "importance": 1-5,
    "is_memorable": true
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
                if fact.get('is_memorable') and fact.get('confidence', 0) > 0.6:
                    await self.save_fact(user_id, fact)
        except Exception as e:
            print(f"Error in semantic extraction: {e}")

    async def save_fact(self, user_id, fact_data):
        """
        Saves or Updates a fact. Implements Conflict Resolution & Merging.
        fact_data: {type, value, confidence, importance}
        """
        content = fact_data['value']
        category = fact_data['type']
        vector = embedding_engine.embed_text(content)
        
        # 1. Search for existing similar facts of the same type
        existing = self.collection.query(
            query_embeddings=[vector],
            n_results=1,
            where={"$and": [{"user_id": user_id}, {"type": category}]}
        )
        
        target_id = f"{user_id}_{hash(content)}_{os.getpid()}"
        is_update = False
        
        if existing['ids'][0]:
            similarity = 1 - existing['distances'][0][0] # Using cosine space (1 - dist = similarity)
            if similarity > 0.85: # High similarity -> Merge/Update
                target_id = existing['ids'][0][0]
                is_update = True
                print(f"DEBUG: Merging/Updating existing fact for {category}: {target_id}")
            elif category in ['identity', 'goals']:
                # Identity/Goals are usually singular, replace if not similar enough but same type
                self.collection.delete(ids=existing['ids'][0])
                print(f"DEBUG: Replacing different {category} fact.")

        # 2. Save (Add or Update)
        metadata = {
            "user_id": user_id,
            "type": category,
            "confidence": fact_data['confidence'],
            "importance": fact_data['importance'],
            "timestamp": "2024-03-18" # Or dynamic
        }

        if is_update:
            self.collection.update(
                ids=[target_id],
                embeddings=[vector],
                documents=[content],
                metadatas=[metadata]
            )
        else:
            self.collection.add(
                ids=[target_id],
                embeddings=[vector],
                documents=[content],
                metadatas=[metadata]
            )

    def query_facts(self, user_id, query_text):
        """
        Retrieve facts with Ranking & Filtering.
        """
        if not query_text:
            return "No query provided."

        query_vector = embedding_engine.embed_text(query_text)
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=10,
            where={"user_id": user_id}
        )
        
        if not results['documents'][0]:
            return "No matching memories found."
            
        # Rank by (distance * importance * confidence) - simplified logic
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        ranked_facts = []
        for i in range(len(docs)):
            metadata = metas[i]
            # Handle old metadata structure (legacy from Phase 10)
            confidence = metadata.get('confidence', 1.0)
            fact_type = metadata.get('type') or metadata.get('category', 'fact')
            
            if confidence > 0.5:
                ranked_facts.append(f"- [{fact_type.upper()}] {docs[i]}")

        return "\n".join(ranked_facts[:5])

semantic_memory = SemanticMemory()
