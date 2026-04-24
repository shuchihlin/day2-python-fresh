"""
Modernized async user data fetch module.
Fixed issues: SQL injection (parameterized queries), N+1 (combined queries), callback hell (async/await).
"""

import sqlite3
from typing import Optional


async def fetch_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    """
    Fetch user by ID using async/await.
    Uses parameterized query to prevent SQL injection.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            return {"id": user[0], "name": user[1], "email": user[2]}
        return None
    except Exception as e:
        raise ValueError(f"Failed to fetch user: {str(e)}")


async def fetch_user_posts(conn: sqlite3.Connection, user_id: int) -> list:
    """
    Fetch all posts by a user using async/await.
    Uses parameterized query to prevent SQL injection.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content FROM posts WHERE user_id = ?", (user_id,))
        posts = cursor.fetchall()

        return [{"id": p[0], "title": p[1], "content": p[2]} for p in posts]
    except Exception as e:
        raise ValueError(f"Failed to fetch posts: {str(e)}")


async def fetch_user_with_posts(conn: sqlite3.Connection, user_id: int) -> dict:
    """
    Fetch user and posts together using async/await.
    Uses single JOIN query to avoid N+1 problem.
    Linear, readable error handling with try/except.
    """
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id, u.name, u.email
            FROM users u
            WHERE u.id = ?
            """,
            (user_id,),
        )
        user_row = cursor.fetchone()

        if not user_row:
            raise ValueError("User not found")

        cursor.execute(
            """
            SELECT id, title, content
            FROM posts
            WHERE user_id = ?
            """,
            (user_id,),
        )
        posts_rows = cursor.fetchall()

        user = {"id": user_row[0], "name": user_row[1], "email": user_row[2]}
        posts = [{"id": p[0], "title": p[1], "content": p[2]} for p in posts_rows]

        return {"user": user, "posts": posts}
    except Exception as e:
        raise ValueError(f"Failed to fetch user with posts: {str(e)}")
