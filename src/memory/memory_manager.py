import json
from ..core.database import db
from .semantic_memory import semantic_memory

class MemoryManager:
    def __init__(self):
        pass

    def get_context(self, user_id, channel_id, query_text=None):
        # 1. Retrieve Short-term Logs
        short_term = db.get_recent_logs(channel_id, limit=15)
        
        # 2. Retrieve Persistent Summary
        summary_data = self.get_persistent_summary(channel_id)
        
        # 3. Use Vector Search for Semantic Facts
        semantic = "No matching memories found."
        if query_text:
            semantic = semantic_memory.query_facts(user_id, query_text)
        
        return {
            "short_term": short_term,
            "summary": summary_data,
            "semantic": semantic
        }

    def get_persistent_summary(self, channel_id):
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT topic, content, key_points FROM summary_memory WHERE channel_id = ?", (channel_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "topic": row[0],
                    "content": row[1],
                    "key_points": row[2]
                }
            return None

    def update_memory(self, channel_id, user_id, username, message, response):
        db.log_message(channel_id, user_id, username, message)
        db.log_message(channel_id, "bot_assistant", "Nia", response)

    async def summarize_history(self, channel_id):
        """
        Triggered when logs > 15. Summarizes oldest 10 and merges with existing summary.
        """
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE channel_id = ?", (channel_id,))
            count = cursor.fetchone()[0]
            
            if count <= 15:
                return

            # Fetch oldest 10 messages
            cursor.execute("SELECT id, username, content FROM chat_logs WHERE channel_id = ? ORDER BY id ASC LIMIT 10", (channel_id,))
            old_msgs = cursor.fetchall()
            ids_to_delete = [m[0] for m in old_msgs]
            formatted_msgs = "\n".join([f"{m[1]}: {m[2]}" for m in old_msgs])

            # Fetch existing summary
            existing = self.get_persistent_summary(channel_id)
            
            from ..ai.client import ai_client
            prompt = f"""Summarize the next part of this conversation. 
EXISTING SUMMARY: {existing if existing else "None"}
NEW MESSAGES:
{formatted_msgs}

Update the summary strictly as a JSON object:
{{
  "topic": "Main topic",
  "content": "Overall narrative summary",
  "key_points": ["point 1", "point 2"]
}}
"""
            try:
                raw = await ai_client.generate_response([{"role": "user", "content": prompt}])
                if not raw:
                    print("ERROR: AI returned an empty response during summarization.")
                    return

                cleaned = raw.strip()
                if "```json" in cleaned:
                    cleaned = cleaned.split("```json")[-1].split("```")[0].strip()
                elif "{" in cleaned and "}" in cleaned:
                    # Try to extract JSON if it's not in a code block
                    start = cleaned.find("{")
                    end = cleaned.rfind("}") + 1
                    cleaned = cleaned[start:end]
                
                try:
                    data = json.loads(cleaned)
                except json.JSONDecodeError as je:
                    print(f"ERROR: Could not parse AI response as JSON: {cleaned}. Error: {je}")
                    return
                
                # Update DB
                cursor.execute('''
                    INSERT OR REPLACE INTO summary_memory (channel_id, topic, content, key_points, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (channel_id, data['topic'], data['content'], json.dumps(data.get('key_points', []))))
                
                # Delete summarized logs
                cursor.execute(f"DELETE FROM chat_logs WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
                conn.commit()
                print(f"DEBUG: Successfully summarized 10 messages for {channel_id}")
            except Exception as e:
                print(f"ERROR in summarization: {e}")
            except Exception as e:
                print(f"ERROR in summarization: {e}")

memory_manager = MemoryManager()
