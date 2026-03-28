"""SQLite: чаты, сообщения, настройки пользователя."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

from app.config.settings import get_settings


def init_db(db_path: Optional[Path] = None) -> None:
    path = db_path or get_settings().sqlite_path
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS chats
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS messages
           (id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS active_chats
           (user_id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id))"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_settings
           (user_id INTEGER PRIMARY KEY,
            show_reasoning INTEGER DEFAULT 0)"""
    )
    conn.commit()
    conn.close()


class ChatManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or get_settings().sqlite_path)

    def get_or_create_active_chat(self, user_id: int) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT chat_id FROM active_chats WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            chat_id = result[0]
        else:
            c.execute("INSERT INTO chats (user_id, title) VALUES (?, ?)", (user_id, "Новый чат"))
            chat_id = c.lastrowid
            c.execute(
                "INSERT INTO active_chats (user_id, chat_id) VALUES (?, ?)",
                (user_id, chat_id),
            )
            conn.commit()
        conn.close()
        return chat_id

    def create_new_chat(self, user_id: int, title: str = "Новый чат") -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO chats (user_id, title) VALUES (?, ?)", (user_id, title))
        chat_id = c.lastrowid
        c.execute(
            "INSERT OR REPLACE INTO active_chats (user_id, chat_id) VALUES (?, ?)",
            (user_id, chat_id),
        )
        conn.commit()
        conn.close()
        return chat_id

    def switch_chat(self, user_id: int, chat_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO active_chats (user_id, chat_id) VALUES (?, ?)",
            (user_id, chat_id),
        )
        conn.commit()
        conn.close()

    def get_user_chats(self, user_id: int, limit: int = 10) -> List[Tuple]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """SELECT id, title, updated_at FROM chats
               WHERE user_id = ?
               ORDER BY updated_at DESC LIMIT ?""",
            (user_id, limit),
        )
        chats = c.fetchall()
        conn.close()
        return chats

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        c.execute("UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()

    def get_chat_messages(self, chat_id: int, limit: int = 20) -> List[Tuple[str, str]]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """SELECT role, content FROM messages
               WHERE chat_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (chat_id, limit),
        )
        messages = c.fetchall()
        conn.close()
        return list(reversed(messages))

    def update_chat_title(self, chat_id: int, title: str) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
        conn.commit()
        conn.close()

    def delete_chat(self, chat_id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        c.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        c.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()

    def get_show_reasoning(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT show_reasoning FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row is None:
            return True
        return bool(row[0])

    def set_show_reasoning(self, user_id: int, value: bool) -> None:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, show_reasoning) VALUES (?, ?)",
            (user_id, 1 if value else 0),
        )
        conn.commit()
        conn.close()
