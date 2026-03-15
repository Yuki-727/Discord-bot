import sqlite3
import os
import json
from datetime import datetime

class Database:
    def __init__(self, db_path="yuki_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # User Affection
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS affection (
                    user_id TEXT PRIMARY KEY,
                    level INTEGER DEFAULT 0,
                    last_interaction TIMESTAMP
                )
            ''')
            # Long-term Memory (Personal info about users, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    user_id TEXT,
                    key TEXT,
                    value TEXT,
                    timestamp TIMESTAMP,
                    PRIMARY KEY (user_id, key)
                )
            ''')
            # Chat Logs (for passive context)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    user_id TEXT,
                    username TEXT,
                    content TEXT,
                    timestamp TIMESTAMP
                )
            ''')
            conn.commit()

    def update_affection(self, user_id, amount):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO affection (user_id, level, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    level = level + ?,
                    last_interaction = ?
            ''', (user_id, amount, datetime.now(), amount, datetime.now()))
            conn.commit()

    def get_affection(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT level FROM affection WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def add_memory(self, user_id, key, value):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memory (user_id, key, value, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value = ?,
                    timestamp = ?
            ''', (user_id, key, value, datetime.now(), value, datetime.now()))
            conn.commit()

    def get_memories(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM memory WHERE user_id = ?', (user_id,))
            return {row[0]: row[1] for row in cursor.fetchall()}

    def log_message(self, channel_id, user_id, username, content):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_logs (channel_id, user_id, username, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (channel_id, user_id, username, content, datetime.now()))
            conn.commit()

    def get_recent_logs(self, channel_id, limit=20):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, content FROM chat_logs 
                WHERE channel_id = ? 
                ORDER BY timestamp DESC LIMIT ?
            ''', (channel_id, limit))
            logs = cursor.fetchall()
            return logs[::-1] # Reverse to get chronological order
