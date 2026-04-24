"""
Legacy callback-style user data fetch module.
Contains intentional issues: SQL injection, N+1 queries, callback hell.
Reserved for Day 3 refactoring to async/await.
"""

import sqlite3
from typing import Callable, Any, Optional


def fetch_user_by_id(user_id: int, callback: Callable[[Optional[dict], Optional[str]], None]):
    """
    Fetch user by ID using callback pattern.
    Intentional SQL injection vulnerability: user_id is not parameterized.
    """
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        query = f"SELECT id, name, email FROM users WHERE id = {user_id}"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            callback({"id": user[0], "name": user[1], "email": user[2]}, None)
        else:
            callback(None, "User not found")
    except Exception as e:
        callback(None, str(e))


def fetch_user_posts(user_id: int, callback: Callable[[Optional[list], Optional[str]], None]):
    """
    Fetch all posts by a user.
    Intentional N+1 issue: if you fetch 100 users first, this makes 100 queries.
    """
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, title, content FROM posts WHERE user_id = {user_id}")
        posts = cursor.fetchall()
        conn.close()

        result = [{"id": p[0], "title": p[1], "content": p[2]} for p in posts]
        callback(result, None)
    except Exception as e:
        callback(None, str(e))


def fetch_user_with_posts(
    user_id: int,
    on_user: Callable[[Optional[dict], Optional[str]], None],
    on_posts: Callable[[Optional[list], Optional[str]], None],
):
    """
    Callback hell: fetch user, then fetch their posts, then invoke two separate callbacks.
    This demonstrates why async/await is cleaner than nested callbacks.
    """

    def user_callback(user, error):
        if error:
            on_user(None, error)
            return
        on_user(user, None)

        def posts_callback(posts, error):
            if error:
                on_posts(None, error)
                return
            on_posts(posts, None)

        fetch_user_posts(user_id, posts_callback)

    fetch_user_by_id(user_id, user_callback)
