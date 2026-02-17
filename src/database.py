"""
データベース操作モジュール
==========================

SQLiteデータベースの初期化とCRUD操作を提供します。
"""

import sqlite3
import os

DB_NAME = "app.db"

def get_connection():
    """
    データベース接続を取得します。
    """
    return sqlite3.connect(DB_NAME)

def init_db():
    """
    データベースとテーブルを初期化します。
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    """
    新しいユーザーを追加します。

    Args:
        username (str): ユーザー名
        password_hash (str): ハッシュ化されたパスワード

    Returns:
        bool: 成功した場合はTrue、失敗した場合（重複など）はFalse
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error adding user: {e}")
        return False

def get_user(username):
    """
    ユーザー名からユーザー情報を取得します。

    Args:
        username (str): ユーザー名

    Returns:
        tuple or None: (id, username, password_hash) または None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user
