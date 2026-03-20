import sqlite3
import threading
from contextlib import contextmanager
from .config import config

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_path = config.DATABASE_NAME
        self._init_db()
        self._initialized = True

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 3-tier Memory: Chat Logs (Short/Long term)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    user_id TEXT,
                    username TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Character State persistence
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS character_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            # Semantic/Long-term Facts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    category TEXT,
                    content TEXT,
                    importance INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Persistent Conversation Summaries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summary_memory (
                    channel_id TEXT PRIMARY KEY,
                    topic TEXT,
                    content TEXT,
                    key_points TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Monitored Channels for Passive Reading
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitored_channels (
                    channel_id TEXT PRIMARY KEY
                )
            ''')
            conn.commit()

    def add_monitored_channel(self, channel_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO monitored_channels (channel_id) VALUES (?)", (channel_id,))
            conn.commit()

    def is_channel_monitored(self, channel_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM monitored_channels WHERE channel_id = ?", (channel_id,))
            return cursor.fetchone() is not None

    def log_message(self, channel_id, user_id, username, content):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_logs (channel_id, user_id, username, content)
                VALUES (?, ?, ?, ?)
            ''', (channel_id, user_id, username, content))
            conn.commit()

    def get_recent_logs(self, channel_id, limit=20):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, username, content FROM chat_logs 
                WHERE channel_id = ? 
                ORDER BY id DESC LIMIT ?
            ''', (channel_id, limit))
            logs = cursor.fetchall()
            return logs[::-1]

    def clear_history(self, channel_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_logs WHERE channel_id = ?", (channel_id,))
            cursor.execute("DELETE FROM summary_memory WHERE channel_id = ?", (channel_id,))
            cursor.execute("DELETE FROM character_state")
            conn.commit()

db = Database()
