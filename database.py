"""
database.py - SQLite Database Management for Rule-Based Chatbot.

This module handles:
1. Automatic database and table creation at application startup.
2. Saving and loading conversation messages.
3. Storing, retrieving, and deleting persistent user memories (name, preferences).
4. Secure parameterized queries to prevent SQL Injection attacks.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional

# Default database file path in the same directory as this script
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish and return a connection to the SQLite database.
    Configures row_factory so columns can be accessed by name like dictionaries.
    """
    target_path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path)
    # Enable dict-like column access: row['message'] instead of row[3]
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Create necessary database tables if they do not exist already.
    This runs automatically when the Flask app starts.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            # 1. Messages Table: stores chat logs per session
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    sender TEXT NOT NULL CHECK(sender IN ('user', 'bot')),
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Index to ensure fast message lookup by session_id
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id);
            """)

            # 2. User Memory Table: stores persistent key-value facts per session
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, memory_key)
                );
            """)

            # Index to ensure fast memory lookup by session_id
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_session 
                ON user_memory(session_id);
            """)
    finally:
        conn.close()


def save_message(session_id: str, sender: str, message: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Save a message (either from 'user' or 'bot') to the messages table.
    Uses parameterized SQL queries (?) to guarantee protection against SQL injection.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (session_id, sender, message, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP);
                """,
                (session_id, sender, message),
            )
            msg_id = cursor.lastrowid

            cursor.execute(
                "SELECT id, session_id, sender, message, timestamp FROM messages WHERE id = ?;",
                (msg_id,),
            )
            row = cursor.fetchone()
            return {
                "id": row["id"],
                "session_id": row["session_id"],
                "sender": row["sender"],
                "message": row["message"],
                "timestamp": row["timestamp"],
            }
    finally:
        conn.close()


def get_messages(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all conversation messages for a specific session in chronological order.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, session_id, sender, message, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC;
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "sender": row["sender"],
                "message": row["message"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def clear_messages(session_id: str, db_path: Optional[str] = None) -> int:
    """
    Delete all chat history for a specific session.
    Note: This only deletes messages and preserves saved user memories.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM messages WHERE session_id = ?;",
                (session_id,),
            )
            return cursor.rowcount
    finally:
        conn.close()


def save_memory(session_id: str, memory_key: str, memory_value: str, db_path: Optional[str] = None) -> None:
    """
    Save or update a specific memory item (e.g., key='name', value='Mamatha').
    Uses an UPSERT (INSERT ... ON CONFLICT DO UPDATE) to avoid duplicate keys per session.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO user_memory (session_id, memory_key, memory_value, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id, memory_key)
                DO UPDATE SET
                    memory_value = excluded.memory_value,
                    timestamp = CURRENT_TIMESTAMP;
                """,
                (session_id, memory_key.strip().lower(), memory_value.strip()),
            )
    finally:
        conn.close()


def get_memory(session_id: str, memory_key: str, db_path: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a single memory value by its key for a specific session.
    Returns None if the key has not been saved.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT memory_value
            FROM user_memory
            WHERE session_id = ? AND memory_key = ?;
            """,
            (session_id, memory_key.strip().lower()),
        )
        row = cursor.fetchone()
        return row["memory_value"] if row else None
    finally:
        conn.close()


def get_all_memories(session_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all memories saved for a specific session as a list of dictionaries.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, memory_key, memory_value, timestamp
            FROM user_memory
            WHERE session_id = ?
            ORDER BY memory_key ASC;
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "key": row["memory_key"],
                "value": row["memory_value"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_memory(session_id: str, memory_key: str, db_path: Optional[str] = None) -> int:
    """
    Delete a specific memory item (e.g., forgetting the user's name or favorite color).
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_memory WHERE session_id = ? AND memory_key = ?;",
                (session_id, memory_key.strip().lower()),
            )
            return cursor.rowcount
    finally:
        conn.close()


def clear_all_memories(session_id: str, db_path: Optional[str] = None) -> int:
    """
    Delete all stored memories for a specific session.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM user_memory WHERE session_id = ?;",
                (session_id,),
            )
            return cursor.rowcount
    finally:
        conn.close()
